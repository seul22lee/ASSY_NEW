"""The parameter-resolution boundary: one rule, applied to every parameter.

WHY THIS EXISTS

Before S-9, each generation parameter followed its own authority rule and only one
of them said so out loud. `max_output_tokens` came from the stage and was clamped by
the adapter. `temperature` came from the adapter and ignored the stage. `top_p`,
`seed` and `response_schema` were accepted on the request and then dropped without
trace, and `deadline_s` was overridden with only the effective value recorded. Five
of six diverged silently, and the sixth diverged visibly by having a bespoke pair of
record fields written for it.

The defect was never which value won. It was that the question "who decides this
parameter?" had six different answers and no single place that stated any of them.

THE ONE RULE

    stage/default request
        -> experiment override, when the experiment states one
        -> provider normalization, when transport requires it
        -> effective value
        -> what is actually sent

Every parameter passes through the same four steps, and every step is recorded. A
parameter that is dropped is recorded as dropped, with the reason. Nothing may reach
the wire that this module did not resolve, and nothing this module resolved may
reach the wire changed - `verify_payload` is what makes that checkable rather than
merely intended.

WHY THE OVERRIDE IS NOT A BUG TO BE FIXED

The stage driver requests temperature 0.0 because a stage wants a reproducible
answer. The repeated-trial live protocol needs a NON-ZERO temperature, because
sampling the same prompt many times at 0.0 measures nothing. Both are correct, and
the experiment is the one that knows which is being run. So the experiment overrides
the stage, deliberately - and the record carries the stage's value alongside, so a
reader can always see what was overridden and by what.

Making `request.temperature` win instead would silently pin every repeated-trial run
to 0.0 and destroy the protocol. That is why this module resolves an override rather
than removing one.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------
# Resolution outcomes. Each names a DIFFERENT reason, because "not sent" covers
# three situations a reader must be able to tell apart: the provider cannot
# transmit it, nobody asked for it, or it is honoured somewhere other than the
# wire.
# --------------------------------------------------------------------------

#: The stage asked, nothing overrode it, it went out unchanged.
SENT_AS_REQUESTED = "SENT_AS_REQUESTED"
#: The experiment stated a different value and that value went out.
SENT_AS_OVERRIDDEN = "SENT_AS_OVERRIDDEN"
#: Transport required a smaller value. The requested one is retained.
SENT_AS_CLAMPED = "SENT_AS_CLAMPED"
#: The provider cannot transmit this parameter at all. Never silently dropped.
NOT_SENT_UNSUPPORTED = "NOT_SENT_UNSUPPORTED"
#: Neither stage nor experiment stated a value.
NOT_SENT_NOT_REQUESTED = "NOT_SENT_NOT_REQUESTED"
#: Requested semantics are honoured off the wire - by the prompt and the parser.
NOT_SENT_PARSER_SIDE = "NOT_SENT_PARSER_SIDE"

#: Statuses in which something actually left the process.
SENT_STATUSES = frozenset({SENT_AS_REQUESTED, SENT_AS_OVERRIDDEN, SENT_AS_CLAMPED})

#: Where a resolved parameter is applied. `payload` is the JSON body, `transport`
#: is the connection itself (a timeout is not a field the model reads), and `none`
#: is a parameter that leaves no trace on the call at all.
PAYLOAD = "payload"
TRANSPORT = "transport"
NOWHERE = "none"


@dataclass(frozen=True)
class ResolvedParameter:
    """One parameter's whole journey, in one object.

    `requested` is what the stage asked for and is retained even when it lost, so
    a record can always answer "what was overridden" rather than only "what was
    sent". That distinction is the entire point of S9-I7.
    """

    name: str
    requested: Any
    override: Any
    effective: Any
    status: str
    channel: str
    #: The key this appears under in the request body, when it appears at all.
    wire_name: Optional[str] = None
    note: str = ""

    @property
    def sent(self) -> bool:
        return self.status in SENT_STATUSES

    def as_record(self) -> Dict[str, Any]:
        return {"requested": self.requested, "override": self.override,
                "effective": self.effective, "status": self.status,
                "channel": self.channel, "sent": self.sent, "note": self.note}


@dataclass(frozen=True)
class ExperimentOverrides:
    """What the EXPERIMENT decides, as opposed to what the stage asks for.

    Every field defaults to None, and None means "state no opinion, let the
    stage's request stand". A default that silently overrode would reintroduce
    exactly the invisible authority this module exists to remove.
    """

    model: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    deadline_s: Optional[float] = None
    #: "json_object" or "text".
    response_format: Optional[str] = None

    def as_record(self) -> Dict[str, Any]:
        return {"model": self.model, "temperature": self.temperature,
                "top_p": self.top_p, "deadline_s": self.deadline_s,
                "response_format": self.response_format}


@dataclass(frozen=True)
class ParameterResolution:
    """The resolved specification. Immutable, and the only source for the payload."""

    parameters: Tuple[ResolvedParameter, ...]

    def by_name(self, name: str) -> ResolvedParameter:
        for p in self.parameters:
            if p.name == name:
                return p
        raise KeyError("no resolved parameter named %r" % name)

    def effective(self, name: str) -> Any:
        return self.by_name(name).effective

    def payload_fragment(self) -> Dict[str, Any]:
        """EXACTLY the parameters that belong in the request body.

        The provider builds its body from this rather than from its own
        attributes, so a parameter cannot reach the wire without having been
        resolved first.
        """
        out: Dict[str, Any] = {}
        for p in self.parameters:
            if p.sent and p.channel == PAYLOAD and p.wire_name:
                out[p.wire_name] = (_response_format_value(p.effective)
                                    if p.name == "response_format" else p.effective)
        return out

    def transport_timeout(self) -> Optional[float]:
        p = self.by_name("deadline_s")
        return p.effective if p.sent else None

    def as_record(self) -> Dict[str, Any]:
        return {p.name: p.as_record() for p in self.parameters}


def _response_format_value(mode: Any) -> Any:
    """DeepSeek spells the format as an object, not a bare string."""
    return {"type": mode}


def resolve(request, overrides: ExperimentOverrides, *,
            max_output_tokens_ceiling: int,
            supports_seed: bool,
            supports_response_schema: bool) -> ParameterResolution:
    """Apply the one rule to every parameter of one call.

    `request` is a GenerationRequest. Capability facts are passed in rather than
    imported so that this function is about resolution and the provider stays the
    authority on what it can transmit.
    """
    resolved: List[ResolvedParameter] = []

    # ---- model ---------------------------------------------------------
    # The stage states no model. Choosing one is an experiment decision, so the
    # override IS the request here and there is nothing for it to override.
    model_requested = getattr(request, "model", None)
    model_effective = overrides.model or model_requested
    resolved.append(ResolvedParameter(
        name="model", requested=model_requested, override=overrides.model,
        effective=model_effective,
        status=(SENT_AS_OVERRIDDEN if overrides.model and overrides.model != model_requested
                else SENT_AS_REQUESTED),
        channel=PAYLOAD, wire_name="model",
        note="the stage states no model; selecting one is an experiment decision"))

    # ---- temperature ---------------------------------------------------
    resolved.append(_scalar_override(
        "temperature", request.temperature, overrides.temperature, "temperature",
        note=("the stage asks for a reproducible answer; the repeated-trial protocol "
              "asks for sampling, and the experiment says which run this is")))

    # ---- top_p ---------------------------------------------------------
    resolved.append(_scalar_override(
        "top_p", request.top_p, overrides.top_p, "top_p",
        note="accepted on the request and no longer discarded without trace"))

    # ---- max_output_tokens ---------------------------------------------
    # The stage owns how much output it needs. Transport owns the ceiling. Under
    # the one rule this is a normalization step, not a separate authority model.
    requested_tokens = request.max_output_tokens
    if requested_tokens is None:
        effective_tokens = max_output_tokens_ceiling
        tokens_status = NOT_SENT_NOT_REQUESTED
    elif requested_tokens > max_output_tokens_ceiling:
        effective_tokens = max_output_tokens_ceiling
        tokens_status = SENT_AS_CLAMPED
    else:
        effective_tokens = requested_tokens
        tokens_status = SENT_AS_REQUESTED
    if tokens_status is NOT_SENT_NOT_REQUESTED:
        # A call with no cap still needs one on the wire; the ceiling is used and
        # recorded as the provider's, not as something the stage asked for.
        tokens_status = SENT_AS_CLAMPED
    resolved.append(ResolvedParameter(
        name="max_output_tokens", requested=requested_tokens, override=None,
        effective=effective_tokens, status=tokens_status,
        channel=PAYLOAD, wire_name="max_tokens",
        note=("clamped to the provider ceiling %d" % max_output_tokens_ceiling
              if tokens_status == SENT_AS_CLAMPED else "")))

    # ---- deadline / transport timeout ----------------------------------
    # Not a payload field: the model never sees it. It still resolves through the
    # same rule, because "which timeout actually applied" was previously
    # unanswerable whenever the adapter set one.
    resolved.append(_scalar_override(
        "deadline_s", request.deadline_s, overrides.deadline_s, None,
        channel=TRANSPORT,
        note="applied to the connection, not sent to the model"))

    # ---- seed ----------------------------------------------------------
    # PRESERVED, NEVER PRETENDED. The stage asks for seed 7; DeepSeek accepts no
    # seed parameter. Recording None here would erase the request; recording it as
    # sent would be inventing determinism the provider does not offer.
    resolved.append(ResolvedParameter(
        name="seed", requested=request.seed, override=None,
        effective=request.seed if supports_seed else None,
        status=(SENT_AS_REQUESTED if supports_seed and request.seed is not None
                else NOT_SENT_UNSUPPORTED if not supports_seed
                else NOT_SENT_NOT_REQUESTED),
        channel=PAYLOAD if supports_seed else NOWHERE,
        wire_name="seed" if supports_seed else None,
        note=("" if supports_seed else
              "the provider accepts no seed parameter; the requested value is "
              "retained and no determinism is claimed")))

    # ---- response format vs response schema ----------------------------
    # Two different things that were previously one silence. The provider can
    # transmit a FORMAT MODE ("give me a JSON object"). It cannot transmit a
    # SCHEMA. The prompt and the parser carry the schema, so the schema is
    # recorded as honoured off the wire rather than dropped.
    fmt_effective = overrides.response_format or "text"
    resolved.append(ResolvedParameter(
        name="response_format", requested=None, override=overrides.response_format,
        effective=fmt_effective,
        status=(SENT_AS_OVERRIDDEN if overrides.response_format
                else NOT_SENT_NOT_REQUESTED),
        channel=PAYLOAD if overrides.response_format else NOWHERE,
        wire_name="response_format" if overrides.response_format else None,
        note="format mode is a transport capability; the shape itself is the parser's"))

    schema = request.response_schema
    resolved.append(ResolvedParameter(
        name="response_schema", requested=("<schema>" if schema is not None else None),
        override=None, effective=None,
        status=(NOT_SENT_NOT_REQUESTED if schema is None
                else SENT_AS_REQUESTED if supports_response_schema
                else NOT_SENT_PARSER_SIDE),
        channel=NOWHERE, wire_name=None,
        note=("the provider transmits no schema; the prompt states the shape and the "
              "parser enforces it" if schema is not None and not supports_response_schema
              else "")))

    return ParameterResolution(parameters=tuple(resolved))


def _scalar_override(name: str, requested: Any, override: Any,
                     wire_name: Optional[str], channel: str = PAYLOAD,
                     note: str = "") -> ResolvedParameter:
    """The common case: stage states a value, experiment may replace it."""
    if override is not None:
        effective, status = override, SENT_AS_OVERRIDDEN
    elif requested is not None:
        effective, status = requested, SENT_AS_REQUESTED
    else:
        return ResolvedParameter(name=name, requested=requested, override=override,
                                 effective=None, status=NOT_SENT_NOT_REQUESTED,
                                 channel=NOWHERE, wire_name=None, note=note)
    return ResolvedParameter(name=name, requested=requested, override=override,
                             effective=effective, status=status, channel=channel,
                             wire_name=wire_name, note=note)


#: Body keys that are not generation parameters. `messages` is the prompt and
#: `stream` is a transport mode; neither is resolved, and both are expected.
STRUCTURAL_KEYS = ("messages", "stream")

#: The key each parameter occupies in the body, whether or not it is sent. Kept
#: even for unsent parameters so that a smuggled one can be named rather than
#: merely noticed - a `seed` that reaches the wire while the resolution says
#: UNSUPPORTED must be reported as seed, not as "some unexpected key".
WIRE_NAMES = {"model": "model", "temperature": "temperature", "top_p": "top_p",
              "max_output_tokens": "max_tokens", "seed": "seed",
              "response_format": "response_format"}


def verify_payload(resolution: ParameterResolution, payload: Dict[str, Any],
                   structural: Tuple[str, ...] = STRUCTURAL_KEYS) -> List[str]:
    """Mismatches between what was resolved and what is about to be sent.

    THE POINT OF S9-I7 IS THAT THIS CANNOT BE SILENT. The provider builds its
    payload from `payload_fragment`, so agreement is structural rather than
    hopeful - but a later edit could reintroduce a hand-built field, and this is
    what would catch it.

    THE CHECK IS EXACT IN BOTH DIRECTIONS. Verifying only that every resolved
    parameter appears correctly would miss the more dangerous direction: a value
    on the wire that nothing resolved. An unsupported `seed` added by hand would
    then be sent while the record went on saying NOT_SENT_UNSUPPORTED - a record
    that contradicts the call it describes, which is the exact failure this
    boundary exists to make impossible.

    A non-empty result is a programming error, not a provider condition: the
    provider interface promises to raise only on a malformed request, and a body
    that contradicts its own resolution is exactly that.
    """
    problems: List[str] = []
    accounted = set(structural)

    for p in resolution.parameters:
        wire = p.wire_name or WIRE_NAMES.get(p.name)
        if p.sent and p.channel == PAYLOAD:
            accounted.add(wire)
            if wire not in payload:
                problems.append("%s resolved as %s but %r is absent from the body"
                                % (p.name, p.status, wire))
                continue
            expected = (_response_format_value(p.effective)
                        if p.name == "response_format" else p.effective)
            if payload[wire] != expected:
                problems.append("%s effective=%r but body carries %r"
                                % (p.name, expected, payload[wire]))
        elif wire and wire in payload:
            # Resolved as not-sent, or applied off the wire, yet present anyway.
            problems.append("%s resolved as %s but %r is in the body anyway"
                            % (p.name, p.status, wire))
            accounted.add(wire)

    for key in sorted(set(payload) - accounted):
        problems.append("%r is in the body but no resolved parameter put it there"
                        % key)
    return problems
