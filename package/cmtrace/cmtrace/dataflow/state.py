"""Class State Represents the SADF graph state inbetween scenarios"""
from cmtrace.dataflow.maxplus import delay

class State:
    """Represents the SADF graph state inbetween scenarios"""

    def __init__(self, name, input_scenarios, output_scenarios):
        self.input_scenarios = input_scenarios
        self.output_scenarios = output_scenarios
        self.name = name
        self.providers = dict()
        self.firings = []

    def set_provider(self, scenario, actor):
        """Set the actor that provides the state in the given scenario"""
        # production in scenarion is done by actor at the end of its firing
        self.providers[scenario] = actor
        return

    def spliced_firings(self, scen_seq, scen, tokdel):
        """return the firings, spliced for scenario scen in sequence scen_seq.
        """
        del_firings = delay(self.firings, tokdel)
        kix = mix = 0
        splice = []
        while mix < len(del_firings) and kix < len(scen_seq):
            if scen_seq[kix] in self.input_scenarios:
                if scen_seq[kix] == scen:
                    splice.append(del_firings[mix])
                mix += 1
            kix += 1
        return splice

    def update_state_sadf(self, scen_seq):
        """Update the state from the state providers for the given scenario sequence.
        Return a boolean indicating if the sequence remained the same."""
        old_firings = len(self.firings)
        prov_firings = dict()
        indices = dict()
        for scenario, actor in self.providers.items():
            prov_firings[scenario] = actor.completions()
            indices[scenario] = 0
        self.firings = []
        for (k, _) in enumerate(scen_seq):
            # if the current scenario outputs to this state
            if scen_seq[k] in self.output_scenarios:
                scenario = scen_seq[k]
                # if there are no more remaining events
                if indices[scenario] >= len(prov_firings[scenario]):
                    # then the output stops here
                    break
                # otherwise add the event
                self.firings.append(prov_firings[scenario][indices[scenario]])
                # update the index for the scenario
                indices[scenario] += 1
        return old_firings == len(self.firings)
