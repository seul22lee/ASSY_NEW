# Status vocabulary

| Status | Means |
|---|---|
| `PASS` | computed or reviewed evidence supports the claim |
| `FAIL` | evidence contradicts the claim |
| `NOT_VERIFIED` | no evidence of adequate fidelity exists |
| `NOT_EVALUABLE` | the record does not contain what the check needs (`REPRESENTATION_INCOMPLETE`) |
| `UNSUPPORTED` | the toolchain cannot evaluate it |

Two distinctions matter more than they look.

**`NOT_VERIFIED` is not `FAIL`.** Absent evidence is not contrary evidence. If you
have no way to establish something, say so; do not convert it into either verdict.

**`NOT_EVALUABLE` is not `FAIL`.** A design can be perfectly buildable while its
record is incomplete. That is a defect in the record, not in the product, and
reporting it as a physical failure tells the designer their design is wrong when
it is the paperwork that is wrong.

Do not convert missing evidence into `PASS`. A tag or field you wrote yourself is
not evidence for the requirement that asks for it.
