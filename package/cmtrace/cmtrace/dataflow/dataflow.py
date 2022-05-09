"""Implements the denotational semantics of open datflow models."""

def compute_fixpoint(actors):
    """Perform the Kahn fix-point computation of the SDF semantics."""
    fixpoint = False
    # continue till a fixpoint is reached
    while not fixpoint:
        fixpoint = True
        for actor in actors:
            res = actor.update_firings()
            # do not combine this line with the above, because and is lazy
            fixpoint = fixpoint and res


def compute_fixpoint_sadf(scen_seq, actors, states):
    """Perform the Kahn fix-point computation of the SADF semantics."""
    fixpoint = False
    # continue till a fixpoint is reached
    while not fixpoint:
        fixpoint = True
        # splice traces across scenarios following the scenario sequence
        # update the actors in all scenarios
        for actor in actors:
            # update actor a
            res = actor.update_firings_sadf(scen_seq)
            # do not combine this line with the above, because and is lazy
            fixpoint = fixpoint and res
        # update the states
        for state in states:
            res = state.update_state_sadf(scen_seq)
            fixpoint = fixpoint and res

    return
