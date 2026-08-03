# Dossier bounded-two-state-closure — FROZEN (micro-oracle)

> Renamed from `DOS-hinge-and-stop.md` at correction F-3C-001. Evidence sections
> S1-S7 are unchanged.

**Tier:** micro_oracle. Constrains **one reusable mechanical capability**, never a
product and never a mechanism. Legacy fixtures below are cited as evidence and as
sources of negative cases; they are **not** acceptance targets.

## S1. Capability
A closure that reaches two defined states by a bounded motion, where the bound
at each extreme is physically produced.

## S2. Legacy fixtures (rank 4 evidence, not targets)
| Fixture | Path | What it is |
|---|---|---|
| Hinge box with stop | `/home/ftk3187/github/ASSY_Ver1.0/tasks/m0_hinge_box_stop.json`, `/home/ftk3187/github/ASSY_Ver1.0/m0/out/stop/` | matched pair, WITH a limit |
| Hinge box without stop | `/home/ftk3187/github/ASSY_Ver1.0/tasks/m0_hinge_box_nostop.json`, `/home/ftk3187/github/ASSY_Ver1.0/m0/out/nostop/` | matched pair, WITHOUT a limit |
| Builder | `/home/ftk3187/github/ASSY_Ver1.0/m0/hinge_box.py` | — |

## S3. Explicit observables — the matched pair, verbatim
Both `t2_verdict_V-B_ring.json`, mode **V-B**, strategy ring (16 wedges/knuckle),
`friction_mu 0.3`, `solref [0.001, 1.0]`, `g_conv true`, bore 2.150 / pin 2.000,
min wall 2.192 mm.

| criterion (seed 0) | stop | nostop | threshold |
|---|---|---|---|
| pin retention: radial drift | 0.2452 pass | 0.3367 pass | <= 0.4 |
| pin retention: axial drift | 0.0257 pass | 0.0812 pass | <= 3.0 |
| theta_max >= 90 deg | **115.37** pass | **219.65** pass | >= 90 |
| travel interference (non-intended) | 0.0 pass | 0.0434 pass | <= 0.2 |
| pin/bore interface | 0.0689 pass | 0.2347 pass | <= 0.3 |
| settles closed | 2.84 pass | 2.70 pass | <= 5.0 |
| **verdict** | **True** | **False** | — |
| **seeds_passed** | **5/5** | **1/5** | — |

## S4. Missing criteria
No capability-level open angle, holding requirement, load, or life exists.
`theta >= 90 deg` is the m0 fixture's own threshold.

## S5. Evidence fidelity and limitations — **recorded carefully**
This is genuine **V-B contact** evidence with a matched control differing in one
feature, which makes it the strongest pair in the corpus.

**However:** every seed-0 criterion **passes in both**. The nostop verdict is
False only through seed aggregation (1/5 vs 5/5). The visible seed-0 difference
is `theta_max` 115.37 vs 219.65 deg — but both exceed the >= 90 threshold, so
`theta_max` as thresholded does **not** discriminate them either.

Consequently the pair supports: *"removing the limit produced seed-level
instability across a 5-seed sweep"*. It does **not** supply a single-run
criterion that distinguishes a limited from an unlimited closure.

## S6. Decisions made only by legacy realizations
Pin hinge with ring-meshed knuckles; discrete stop flange
(`/home/ftk3187/github/ASSY_Ver1.0/knowledge/cards/stop_flange.py`); 90 deg target; prismatic box.

## S7. Legacy behaviour that must not define correctness
The corpus bounds motion only by a discrete stop feature. Gravity rest,
over-centre, detent, friction and geometric run-out are absent from the library.
