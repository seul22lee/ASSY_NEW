"""Ver3 namespace.

This package exists so that `ver3.assy_v3` is importable as a package rather than
by path injection. FORBIDDEN_LEGACY_DEPENDENCIES FP-03 forbids sys.path surgery
inside assy_v3, and path surgery is how a legacy import arrives without appearing
as a dependency.

Nothing else lives here. The sibling trees (oracles, oracle_tools, cad_validation,
phase0, contracts, benchmarks, tests) are deliberately NOT Python packages under
this namespace: assy_v3 must not be able to reach them by import.
"""
