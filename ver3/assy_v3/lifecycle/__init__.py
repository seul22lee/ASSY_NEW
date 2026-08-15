"""Lifecycle. WHAT IS STILL TRUE AFTER THE DESIGN MOVES.

Nothing in here owns a family, decides an engineering question or authors a
verdict. A module in this package may only ask the responsibilities that DO own
those questions to answer them again over the current state, and then record
what changed.

Two mechanisms, and they are complementary rather than alternatives:

    A NAMED PREMISE CHANGED        the state engine walks the premise graph and
                                   withdraws unqualified authority from
                                   everything that rests on it, transitively.

    EVIDENCE APPEARED WHERE THERE  no id could have been named, because the fact
    WAS NONE                       being depended on was an ABSENCE. Nothing to
                                   propagate from, so the deterministic
                                   responsibilities are asked again and their
                                   new answers are compared with what stands.

The second is why this package exists. A feasibility assessment that says
NOT_ESTABLISHED because no load path exists cannot name the load path that is
missing, and when one is finally authored no graph edge leads to the answer that
was waiting for it.
"""
