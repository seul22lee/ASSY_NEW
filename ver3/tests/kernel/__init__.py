"""Kernel tests: the ones that need a real CAD kernel to mean anything.

They live OUTSIDE `ver3/tests/meta` on purpose. The boundaries CI job runs
`unittest discover -s ver3/tests/meta` with nothing but PyYAML installed, so a
test placed there is a test that job will import and run - and an OpenCascade
test placed there fails that job for an environment reason that has nothing to
do with the boundary it was meant to check.

The separation is by DEPENDENCY, not by decoration. Nothing in this package is
skip-guarded: the downstream job installs the pinned kernel, asserts it is
actually present in its own step, and then runs these by name. A failure here is
therefore always a real failure - the kernel is guaranteed present by the time
they run, so there is no environment in which they quietly pass by not running.

What belongs here: anything that compiles geometry. What does NOT: opcode
vocabulary, solver formulation, contract and representability checks. Those are
kernel-independent and stay in meta, where they run on every push.
"""
