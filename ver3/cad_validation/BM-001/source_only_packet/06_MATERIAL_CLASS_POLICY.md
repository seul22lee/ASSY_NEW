# Material class policy

Use only these classes:

```
GENERIC_RIGID_POLYMER
GENERIC_RIGID_METAL
GENERIC_COMPLIANT_POLYMER
```

Do not name a commercial grade. A material class here is a **semantic
assumption**, not a verified engineering property, and the record should read that
way.

Do not claim `PASS` for strength, fatigue, wear, friction margin, retention force,
manufacturing tolerance capability, durability or impact resistance. There is no
physics solver and no test data in this pilot. Those are `NOT_VERIFIED`.

If any part of your design works only because a body deforms, or because a force
between bodies is large enough, say so explicitly and name the assumption. That
dependence is exactly what a later reviewer needs to see; hiding it inside "it
works" is the failure mode this exercise exists to prevent.
