"""Class Actor Represents an actor in a dataflow graph"""

from cmtrace.dataflow.maxplus import mp_plus, mp_max, mp_max2, trace, MP_MINUS_INF, output_sequence

class Actor:
    """Represents an actor in a dataflow graph"""
    def __init__(self, name, act_delay, scenario=None):
        self.name = name
        self.delay = act_delay
        self.inputs = {}
        self.primary_inputs = []
        self.state_inputs = {}
        self.firings = []
        self.scenario = scenario

    def add_channel_input(self, actor, initial_tokens=0, arc_delay=0, initial_time=MP_MINUS_INF):
        """add a channel input dependency to another actor, including
        a time-offset arc_delay"""
        self.inputs[actor.name] = (actor, initial_tokens, arc_delay, initial_time)

    def add_state_input(self, state, token_delay=0, arc_delay=0):
        """Add a dependency on a state token for an SADF graph"""
        self.state_inputs[state.name] = (state, token_delay, arc_delay)
        return

    def add_primary_input(self, prim_input):
        """Add dependency to a primary input to the graph."""
        self.primary_inputs.append(prim_input)

    def completions(self):
        """returns the current completion times of the actor"""
        # add the actor delay to the firing times
        return mp_plus(self.firings, self.delay)

    def firing_intervals(self):
        """ Return a list of (start,end) pairs for all firings """
        return [(f, f+self.delay) for f in self.firings]

    def update_firings(self):
        """Recompute the firings of the actor based on its input dependencies.
        Returns a boolean indicating if the computed firings remained the same."""
        old_firings = len(self.firings)
        traces = []
        # collect all the incoming channels
        for i, (act, tok, arc_del, tok_init) in self.inputs.items():
            traces.append(output_sequence(act.completions(), tok, arc_del, tok_init))
        # collect traces for all primary inputs
        for i in self.primary_inputs:
            traces.append(i)
        if len(traces) == 0:
            raise Exception("Actor must have inputs")

        # determine the firings
        self.firings = mp_max(*traces)
        return old_firings == len(self.firings)

    def set_scenario(self, scenario):
        """set the scenario in which the actor is active"""
        self.scenario = scenario

    def update_firings_sadf(self, scen_seq):
        """Recomput the firings of the SADF actor based on its input dependencies.
        Returns a boolean indicating if the computed firings remained the same."""
        # update the actor firings
        oldfirings = len(self.firings)

        # primary inputs
        # assume for the moment that primary inputs are active in only one scenario!
        # hack to deal with absence of primary inputs. Should be an infinitely
        # long sequence of minus inf.
        if len(self.primary_inputs) > 0:
            self.firings = mp_max(*self.primary_inputs)
        else:
            self.firings = [MP_MINUS_INF] * len(scen_seq)

        # state_inputs
        for _, (state, tokdel, arcdel) in self.state_inputs.items():
            if self.scenario is None:
                raise Exception("SADF actor has no scenario.")
            splicedfirings = state.spliced_firings(scen_seq, self.scenario, tokdel)
            self.firings = mp_max2(self.firings, mp_plus(splicedfirings, arcdel))

        # channel inputs
        for _, (act, tok, arcdel, tokinit) in self.inputs.items():
            self.firings = mp_max2(self.firings, output_sequence(act.completions(), tok, arcdel, tokinit))

        return oldfirings == len(self.firings)


    def get_trace(self, tracelength):
        """Get a string representation of the actor's execution trace."""
        return trace(self.firings, self.delay, tracelength)
