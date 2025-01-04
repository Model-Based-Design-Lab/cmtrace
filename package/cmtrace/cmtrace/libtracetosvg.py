'''Script to create an SVG figures from a trace '''
from functools import reduce
import os
import xml.etree.ElementTree as ET
from cmtrace.graphics.svggraphics import save_gantt_svg, save_vector_svg, convert_svg_to_pdf
from cmtrace.graphics.colorpalette import COLORPALETTE_FILLS
from cmtrace.graphics.tracesettings import TraceSettings
from cmtrace.dataflow.maxplus import MPMINUSINF
from cmtrace.utils.utils import warn, error

from cmtrace.graphics.tracesettings import SCENARIO_SEPARATOR

def ensure_path(path):
    ''' make sure that a path exists '''
    if not os.path.exists(path):
        os.makedirs(path)

class TraceActor:
    """A TraceActor has a list of firings, and possibly a scenario"""

    def __init__(self, name, scenario=None):
        self.firings = list()
        self.scenario = scenario
        self.name = name

    def add_firing(self, start, end, iteration):
        """ add a firing to the list of firings """
        self.firings.append((float(start), float(end), iteration))

    def firing_intervals(self):
        """ Return a list of (start,end, iteration) triples for all firings """
        return self.firings

    def max_firing_time(self):
        """ return the largest of completion times of all firing intervals or zero if the list is empty """
        l = self.firing_intervals()
        if len(l) == 0:
            return 0.0
        return max(map(lambda i: i[1], l))

    def min_firing_time(self):
        """ return the smallest of starting times of all firing intervals or zero if the list is empty"""
        l = self.firing_intervals()
        if len(l) == 0:
            return 0.0
        return min(map(lambda i: i[0], l))


def read_trace_xml(filename, scale=1.0):
    """ 
    read the xml trace file and apply an optional scaling to the time stamps
    return actorfirings, input arrivals and output arrivals.
    arrivals are in the form of a dictionary with names as keys and list of time stamps as value
    actor is a dict from actor name to TraceActor objects
    """

    # check if trace file exists
    if not os.path.isfile(filename):
        error("Trace file ({0}) does not exist.".format(filename))

    # parse the XML
    try:
        root = ET.parse(filename)
    except ET.ParseError as e:
        error("Failed to parse xml file ({0}).\nReason: {1}".format(filename, str(e)))

    # dictionary to collect the actor traces
    # keys will be actor scenarios plus actor names
    actors = dict()

    # find all the firing nodes in the XML
    for firing in root.findall("./firings/firing"):
        # get the firing data from it
        act = firing.attrib['actor']
        start = scale*float(firing.attrib['start'])
        end = scale*float(firing.attrib['end'])
        if 'scenario' in firing.attrib:
            scenario = firing.attrib['scenario']
        else:
            scenario = None
        if 'iteration' in firing.attrib:
            iteration = firing.attrib['iteration']
        else:
            iteration = None

        # create a new entry if it is a new actor
        if not scenario+SCENARIO_SEPARATOR+act in actors:
            actors[scenario+SCENARIO_SEPARATOR+act] = TraceActor(scenario+SCENARIO_SEPARATOR+act, scenario)

        # add the new firing
        actors[scenario+SCENARIO_SEPARATOR+act].add_firing(start, end, iteration)

    inputs = dict()
    for inp in root.findall("./inputs/input"):
        # get the timestamp data from it
        timestamp = scale*float(inp.attrib['timestamp'])

        # is the input named?
        if 'name' in inp.attrib:
            name = inp.attrib['name']
        else:
            name = 'Inputs'
        if name not in inputs:
            inputs[name] = list()
        inputs[name].append(timestamp)

    outputs = dict()
    for outp in root.findall("./outputs/output"):
        # get the timestamp data from it
        timestamp = scale*float(outp.attrib['timestamp'])

        # is the input named?
        if 'name' in outp.attrib:
            name = outp.attrib['name']
        else:
            name = 'Outputs'
        if name not in outputs:
            outputs[name] = list()

        outputs[name].append(timestamp)

    return actors, inputs, outputs

# TODO: extend event traces with an iteration number to enable weakly consistent graph
# missing tokens in some iterations
def read_vector_trace_xml(filename, scale=1.0):
    """ read the xml vector trace file and apply an optional scaling to the time stamps. ensure that the sequences all have the same length """

    # parse the XML
    root = ET.parse(filename)

    # dictionary to collect the token traces
    # keys will be token names
    sequences = dict()

    length = 1
    # find all the vector nodes in the XML
    for vector in root.findall("./vectors/vector"):
        iteration = int(vector.attrib['id'])
        for token in vector.findall("token"):
            name = token.attrib['name']
            timestamp = scale*float(token.attrib['timestamp'])

            # create a new entry if it is a new token; fill it with minus infinities for the length of the existing sequences
            if not name in sequences:
                sequences[name] = [MPMINUSINF] * (length-1)
            sequences[name].append(timestamp)

        # fill up all sequences to length
        for tok in sequences:
            if len(sequences[tok]) < length:
                sequences[tok].append(MPMINUSINF)
        length += 1

    return sequences


def create_gantt_actors_all(actors):
    """ create a gantt actor list for all actors occurring in the trace, coloring accrding to the default color palette"""

    # count the ctors found
    act_nr = 0

    # make the list
    gantt_actors = list()
    # for all actors
    for (act_name, tact) in actors.items():
        # add to the list, with a color from the default palette
        gantt_actors.append((act_name, [tact], COLORPALETTE_FILLS[act_nr % (len(COLORPALETTE_FILLS))]))
        act_nr += 1
    return gantt_actors


def __scenario_actors(actors, actor_names, scenarios):
    """ create a list of actors with names in actor_names and scenarios in scenarios """
    res = []
    for scen in scenarios:
        for actor_name in actor_names:
            if scen+SCENARIO_SEPARATOR+actor_name in actors:
                res.append(actors[scen+SCENARIO_SEPARATOR+actor_name])
    return res

def create_gantt_fig(tracefilename, svgfilename, settings=None):
    """ create figure for the trace """

    # create default settings if none are provided
    if settings is None:
        settings = TraceSettings()

    # read trace from file
    actors, arrivals, outputs = read_trace_xml(tracefilename, 1.0)

    actor_color_map = settings.color_map()
    if actor_color_map is None:
        actor_color_map = dict()

    # assign colors to the remaining actors not specified in settings
    color_palette = settings.color_palette()
    cidx = 0
    for act_name, act in actors.items():
        if not act_name in actor_color_map:
            actor_color_map[act_name] = color_palette[cidx]
            cidx = (cidx + 1) % len(color_palette)

    gantt_actors = list()

    # check if there are row layout settings specified
    # a row contains a collection of actor or actor groups as defined in 'groups'
    structure = settings.structure()
    rows = settings.rows()
    if len(rows) > 0:
        for row in rows:
            # collect the actors to be represented in this row
            if row in structure:
                actslist = [(actors[act] if act in actors else None) for act in structure[row]] 
            else:
                actslist = [actors[row]]
            gantt_actors.append((row, actslist))
    else:
        # make a default structure
        # gantt_actors: list of tuples with name, list of Actors
        #TODO: group same actor in different scenarios together
        cidx = 0
        sorted_actors = sorted(actors.items(), key=lambda a: a[1].min_firing_time())
        for act_name, act in sorted_actors:
            parts = act_name.split(SCENARIO_SEPARATOR)
            act_name = parts[len(parts)-1]
            gantt_actors.append((act_name, [act]))
            cidx = (cidx + 1) % len(COLORPALETTE_FILLS)

    save_gantt_svg(gantt_actors, arrivals, outputs, svgfilename, settings=settings)
    convert_svg_to_pdf(svgfilename)

# TODO: maybe allow to make plots with both gantt and tokens

def create_vector_fig(tracefilename, svgfilename, settings=None):
    """ create vector figure for the  trace """

    if settings is None:
        settings = TraceSettings()

    event_seqs = read_vector_trace_xml(tracefilename, 1.0)

    structure = settings.structure()

    token_color_map = settings.color_map()
    if token_color_map is None:
        token_color_map = dict()

    # assign colors to the remaining actors not specified in settings
    color_palette = settings.color_palette_lines()
    cidx = 0
    for token_name, _ in event_seqs.items():
        if not token_name in token_color_map:
            token_color_map[token_name] = color_palette[cidx]
            cidx = (cidx + 1) % len(color_palette)

    event_seq_rows = list()

    # check if there are row layout settings specified
    rows = settings.rows()

    if len(rows) > 0:
        for row in rows:
            # collect the actors to be represented in this row
            if row in structure:
                tokslist = [(event_seqs[seq] if seq in event_seqs else None) for seq in structure[row]]
            else:
                tokslist = [event_seqs[row]]
            event_seq_rows.append((row, tokslist))
    else:
        # create default layout, one row per token
        # vector_tokens: list of tuples with name, list of event sequences
        cidx = 0
        sorted_tokens = sorted(event_seqs.items(), key=lambda a: a[1][0])
        for tok_name, seq in sorted_tokens:
            event_seq_rows.append((tok_name, seq))
            cidx = (cidx + 1) % len(COLORPALETTE_FILLS)


    save_vector_svg(event_seq_rows, svgfilename, settings)



#    save_gantt_svg(event_seq_rows, [], [], svgfilename, settings=settings)
    convert_svg_to_pdf(svgfilename)
