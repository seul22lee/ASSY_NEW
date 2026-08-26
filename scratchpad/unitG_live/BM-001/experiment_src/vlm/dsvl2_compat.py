"""Compatibility shim: run the OFFICIAL DeepSeek-VL2 code on psed310's stack.

psed310 has transformers 4.57.6 and torch 2.10; the official package pins
transformers 4.38.2. Nothing here changes DeepSeek's code or the environment's
torch/transformers - it only re-supplies names the newer transformers moved or
renamed, so the official modules import unchanged.

Every alias below is justified where it is made. Import this BEFORE deepseek_vl2.
"""
import importlib
import sys

_notes = []


def _needed() -> bool:
    """Is this a transformers NEWER than the one DeepSeek-VL2 was written for?

    On 4.38.x every name below already exists and behaves correctly, and
    patching anyway is actively harmful: `DynamicCache.__init__` assigns
    `self.seen_tokens`, so adding a read-only class property makes the real
    class unusable. The shim exists for the newer stack only.
    """
    import transformers
    parts = []
    for chunk in str(transformers.__version__).split(".")[:2]:
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits or 0))
    while len(parts) < 2:
        parts.append(0)
    return tuple(parts) > (4, 38)


def _note(text):
    _notes.append(text)


def apply():
    if not _needed():
        return list(_notes)
    # ---- transformers.models.llama.modeling_llama -----------------------
    # The 4.48 attention refactor removed the per-backend attention classes.
    # DeepSeek-VL2 imports two of them and uses them ONLY as values in its
    # ATTENTION_CLASSES dispatch dict, under the "mha_*" keys. deepseek-vl2
    # configures multi-head-latent attention, so those entries are never
    # selected; the names only have to exist for the import to succeed.
    from transformers.models.llama import modeling_llama as ml
    for name in ("LlamaFlashAttention2", "LlamaSdpaAttention"):
        if not hasattr(ml, name):
            setattr(ml, name, ml.LlamaAttention)
            _note("aliased %s -> LlamaAttention (dispatch-dict value only)" % name)

    # ---- transformers.pytorch_utils -------------------------------------
    import transformers.pytorch_utils as pu
    if not hasattr(pu, "is_torch_greater_or_equal_than_1_13"):
        pu.is_torch_greater_or_equal_than_1_13 = True
        _note("re-supplied is_torch_greater_or_equal_than_1_13 = True "
              "(torch here is far newer than 1.13)")
    if not hasattr(pu, "ALL_LAYERNORM_LAYERS"):
        import torch.nn as nn
        pu.ALL_LAYERNORM_LAYERS = [nn.LayerNorm]
        _note("re-supplied ALL_LAYERNORM_LAYERS")

    # ---- transformers.modeling_attn_mask_utils --------------------------
    import transformers.modeling_attn_mask_utils as am
    if not hasattr(am, "_prepare_4d_causal_attention_mask"):
        from transformers.modeling_attn_mask_utils import AttentionMaskConverter

        def _prepare_4d_causal_attention_mask(attention_mask, input_shape,
                                              inputs_embeds, past_key_values_length,
                                              sliding_window=None):
            converter = AttentionMaskConverter(is_causal=True,
                                               sliding_window=sliding_window)
            key_value_length = input_shape[-1] + past_key_values_length
            if attention_mask is not None and attention_mask.dim() == 2:
                return converter.to_4d(attention_mask, input_shape[-1],
                                       key_value_length=key_value_length,
                                       dtype=inputs_embeds.dtype)
            if attention_mask is None:
                return converter.to_causal_4d(input_shape[0], input_shape[-1],
                                              key_value_length,
                                              dtype=inputs_embeds.dtype,
                                              device=inputs_embeds.device)
            return attention_mask

        am._prepare_4d_causal_attention_mask = _prepare_4d_causal_attention_mask
        _note("re-supplied _prepare_4d_causal_attention_mask via "
              "AttentionMaskConverter, the class it was refactored into")

    # ---- transformers.utils ---------------------------------------------
    import transformers.utils as tu
    if not hasattr(tu, "is_flash_attn_greater_or_equal_2_10"):
        tu.is_flash_attn_greater_or_equal_2_10 = lambda: False
        _note("re-supplied is_flash_attn_greater_or_equal_2_10 -> False")
    return list(_notes)


def apply_cache():
    """Re-supply the two Cache members transformers renamed.

    `prepare_inputs_for_generation` reads `past_key_values.seen_tokens` and
    `.get_max_length()`. Both were removed: the first is now `get_seq_length()`,
    the second `get_max_cache_shape()`. These are exact renames, so the old
    names are restored as thin forwards rather than reimplemented.
    """
    if not _needed():
        return list(_notes)
    from transformers.cache_utils import Cache, DynamicCache
    for cls in (Cache, DynamicCache):
        if not hasattr(cls, "seen_tokens"):
            cls.seen_tokens = property(lambda self: self.get_seq_length())
            _note("re-supplied %s.seen_tokens -> get_seq_length()" % cls.__name__)
        if not hasattr(cls, "get_max_length"):
            def _get_max_length(self):
                getter = getattr(self, "get_max_cache_shape", None)
                return getter() if getter else None
            cls.get_max_length = _get_max_length
            _note("re-supplied %s.get_max_length -> get_max_cache_shape()"
                  % cls.__name__)
        if not hasattr(cls, "get_usable_length"):
            # transformers' own former implementation, restored verbatim in
            # behaviour: how much of the cache a new sequence may use.
            def _get_usable_length(self, new_seq_length, layer_idx=0):
                max_length = self.get_max_length()
                previous_seq_length = self.get_seq_length(layer_idx)
                if max_length is not None and previous_seq_length + new_seq_length > max_length:
                    return max_length - new_seq_length
                return previous_seq_length
            cls.get_usable_length = _get_usable_length
            _note("re-supplied %s.get_usable_length" % cls.__name__)
    return list(_notes)


def apply_generation():
    """Restore `.generate` on the model classes.

    From transformers 4.50, `PreTrainedModel` no longer inherits
    `GenerationMixin`; a model class must inherit it explicitly. transformers
    says so itself in the warning it prints for these very classes ("please
    modify your model class such that it inherits from GenerationMixin").
    DeepSeek-VL2 predates that change, so the mixin is attached here instead of
    editing their code. The generation logic used is transformers' own.
    """
    if not _needed():
        return list(_notes)
    from transformers.generation import GenerationMixin
    from deepseek_vl2.models.modeling_deepseek import DeepseekV2ForCausalLM
    from deepseek_vl2.models.modeling_deepseek_vl_v2 import DeepseekVLV2ForCausalLM
    for cls in (DeepseekV2ForCausalLM, DeepseekVLV2ForCausalLM):
        if issubclass(cls, GenerationMixin):
            continue
        try:
            cls.__bases__ = cls.__bases__ + (GenerationMixin,)
            _note("added GenerationMixin to %s bases" % cls.__name__)
        except TypeError:
            copied = 0
            for name in dir(GenerationMixin):
                if name.startswith("__") or hasattr(cls, name):
                    continue
                setattr(cls, name, getattr(GenerationMixin, name))
                copied += 1
            cls.generate = GenerationMixin.generate
            _note("copied GenerationMixin onto %s (%d members)"
                  % (cls.__name__, copied))
    return list(_notes)


def notes():
    return list(_notes)
