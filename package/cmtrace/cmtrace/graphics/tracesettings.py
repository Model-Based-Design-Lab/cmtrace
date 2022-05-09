""" Class to manage trace settings, defaults and reading from yaml file """

from ast import Str
from math import floor, log10, pow as mathpow
from yaml import Loader as yaml_Loader, load as yaml_load
from cmtrace.graphics.colorpalette import COLORPALETTE_FILLS, COLORPALETTE_LINES
from cmtrace.utils.utils import warn, error

SCENARIO_SEPARATOR = '@'

DEFAULTS = {
    'layout:unit': 'auto',
    'layout:horizontal-scale': 5.0,
    'layout:trace-width': 5.0,
    'layout:event-radius': 0.35,
    'layout:trace-length': 'auto',
    'layout:trace-length-extension': 0.05,
    'layout:origin': [0.0, 0.0],
    'layout:margin-top': 5.5,
    'layout:margin-bottom': 2.0,
    'layout:label-separation': 2.5,
    'layout:tick-length': 1.5,
    'layout:tick-number-separation': 2.0,
    'layout:column-linewidth': 0.25,
    'layout:border-linewidth': 0.4,
    'layout:time-stamp-format': 'auto', # e.g., ':.0f'
    'layout:overlap-vertical-offset': 0.3333,
    'layout:overlap-horizontal-offset': 1.0,
    'layout:font-size': 5.0,
    'layout:font': "Calibri, Arial",
    'graphics:firing-stroke-width': 0,
    'graphics:firing-color-mode': 'by-actor',
    'graphics:vector-color-mode': 'by-iteration',
    'graphics:alternate-color': True,
    'graphics:background-color': (255, 255, 255),
    'graphics:row-background-color': (240, 240, 240)
}

# TODO: raise exception on invalid settings

class TraceSettingsException(Exception):
    pass



class TraceSettings():
    """Class TraceSetting manages trace settings, defaults and reading from yaml file"""
    def __init__(self):
        """"nothing """
        self.settings = dict()
        self.__color_palette = None
        self.__color_index_map = None
        self.__color_map = None
        self.__structure = None
        self.height = None
        self.width = None

    def flatten_settings(self, settings):
        """ reduce the hierarchical dictionary to a flat one, inserting ':' between keys """
        res = dict()
        for key, val in settings.items():
            if isinstance(val, dict):
                flat_val = self.flatten_settings(val)
                for vkey, vval in flat_val.items():
                    res[key+':'+vkey] = vval
            else:
                res[key] = val
        return res

    def parse_settings(self, settingsfile):
        """ parse YAML file with settings. """
        try:
            stream = open(settingsfile, 'r')
            yaml_settings = yaml_load(stream, yaml_Loader)
            self.__init__()
            self.settings = self.flatten_settings(yaml_settings)
        except FileNotFoundError:
            raise TraceSettingsException("Warning: Settings file ({0}) does not exist.".format(settingsfile))

    def read_yaml(self, file):
        """ read the YAML file and parse it """
        self.parse_settings(file)

    def __get_value(self, tag):
        if tag in self.settings:
            return self.settings[tag]
        elif tag in DEFAULTS:
            return DEFAULTS[tag]
        else:
            return None

    def __set_value(self, tag, value):
        self.settings[tag] = value

    def unit(self):
        """ return the unit of the time axis, the amount of time per unit tick """
        val = self.__get_value('layout:unit')
        if val is None:
            return None
        if val == 'auto':
            return 'auto'
        try:
            _unit = float(val)
        except ValueError:
            raise TraceSettingsException("layout:unit must be 'auto' or a number in settings.")
            return 1.0
        return _unit

    def set_unit(self, value):
        """ sets the unit """
        return self.__set_value('layout:unit', value)

    def set_auto_unit(self):
        print("warning: set_auto_unit not implemented, setting default value 1.0")
        return self.__set_value('layout:unit', 1.0)

    def scale_mm_per_unit_x(self):
        """ returns the horizontal scale in mm per unit"""
        return self.__get_value('layout:horizontal-scale')

    def scale_mm_per_unit_y(self):
        """ returns the vertical size of a row in mm """
        return self.__get_value('layout:trace-width')

    def event_radius(self):
        """ returns the radius of an event dot """
        return self.__get_value('layout:event-radius')

    def font(self):
        """ returns the font """
        return self.__get_value('layout:font')

    def fontsize(self):
        """ returns the font """
        return self.__get_value('layout:font-size')

    def overlap_offset(self):
        """ returns the vertical offset to apply to overlapping firing in a Gantt chart """
        return self.__get_value('layout:overlap-vertical-offset')

    def overlap_horizontal_offset(self):
        """ returns the horizontal offset to apply to overlapping events """
        return self.__get_value('layout:overlap-horizontal-offset')

    def length(self):
        """ return the length of the plot in units """
        _val = self.__get_value('layout:trace-length')
        try:
            _tlen = float(_val)
        except ValueError:
            if _val=='auto':
                return _val
            raise TraceSettingsException("layout:trace-length should be a number in settings.")
        return  _tlen

    def length_extension(self):
        """ return the relative extension of the trace length """
        _val = self.__get_value('layout:trace-length-extension')
        try:
            _tlen = float(_val)
        except ValueError:
            raise TraceSettingsException("layout:trace-length-extension should be a number in settings.")
        return  _tlen


    def margin_top(self):
        """ return the top margin in mm """
        _val = self.__get_value('layout:margin-top')
        try:
            _tlen = float(_val)
        except ValueError:
            if _val=='auto':
                return _val
            raise TraceSettingsException("layout:margin-top should be a number in settings.")
        return  _tlen

    def margin_bottom(self):
        """ return the bottom margin in mm """
        _val = self.__get_value('layout:margin-bottom')
        try:
            _tlen = float(_val)
        except ValueError:
            if _val=='auto':
                return _val
            raise TraceSettingsException("layout:margin-bottom should be a number in settings.")
        return  _tlen

    def label_separation(self):
        """ return the horizontal distance between labels and chart in mm """
        _val = self.__get_value('layout:label-separation')
        try:
            _tlen = float(_val)
        except ValueError:
            if _val=='auto':
                return _val
            raise TraceSettingsException("layout:label-separation should be a number in settings.")
        return  _tlen

    def tick_length(self):
        """ return the length of the extending tick marks along the chart in mm """
        _val = self.__get_value('layout:tick-length')
        try:
            _tlen = float(_val)
        except ValueError:
            if _val=='auto':
                return _val
            raise TraceSettingsException("layout:tick-length should be a number in settings.")
        return  _tlen

    def tick_number_separation(self):
        """ return the separation between tick and numbers """
        _val = self.__get_value('layout:tick-number-separation')
        try:
            _tlen = float(_val)
        except ValueError:
            if _val=='auto':
                return _val
            raise TraceSettingsException("layout:tick-number-separation should be a number in settings.")
        return  _tlen

    def column_linewidth(self):
        """ return the line width of the vertical lines in the chart """
        _val = self.__get_value('layout:column-linewidth')
        try:
            _tlen = float(_val)
        except ValueError:
            if _val=='auto':
                return _val
            raise TraceSettingsException("layout:column-linewidth should be a number in settings.")
        return  _tlen

    def border_linewidth(self):
        """ return the line width of the border lines in the chart """
        _val = self.__get_value('layout:border-linewidth')
        try:
            _tlen = float(_val)
        except ValueError:
            if _val=='auto':
                return _val
            raise TraceSettingsException("layout:border-linewidth should be a number in settings.")
        return  _tlen

    def origin(self):
        """ return the coordinates of the origin in units """
        _val = self.__get_value('layout:origin')
        if not type(_val) is list:
            raise TraceSettingsException("layout:origin should be a pair of numbers in settings.")
        if not len(_val) == 2:
            raise TraceSettingsException("layout:origin should be a pair of numbers in settings.")

        if _val=='auto':
            return _val

        return  _val

    def origin_x(self):
        """ return the x coordinate of the origin in units """
        orig = self.origin()
        return  orig[0]

    def origin_y(self):
        """ return the y coordinate of the origin in units """
        orig = self.origin()
        return  orig[1]


    def set_length(self, length):
        """ set the length of the graph in units """
        self.__set_value('layout:trace-length', length)

    def set_auto_length(self):
        print("warning: set_auto_length not implemented, setting default value 100.0")
        return self.__set_value('layout:trace-length', 100.0)

    def firing_stroke_width(self):
        """ returns the stroke width of the Gantt chart bars """
        return self.__get_value('graphics:firing-stroke-width')

    def set_firing_stroke_width(self, width):
        """ set the stroke width of the Gantt chart bars """
        self.__set_value('graphics:firing-stroke-width', width)

    def firing_color_mode(self):
        """ returns the firing color mode """
        return self.__get_value('graphics:firing-color-mode')

    def set_firing_color_mode(self, mode):
        """ sets the firing color mode """
        self.__set_value('graphics:firing-color-mode', mode)

    def vector_color_mode(self):
        """ returns the vector color mode """
        return self.__get_value('graphics:vector-color-mode')

    def set_vector_color_mode(self, mode):
        """ sets the vector color mode """
        self.__set_value('graphics:vector-color-mode', mode)

    def alternate_color(self):
        """ returns the alternate colors setting """
        return self.__get_value('graphics:alternate-color')

    def background_color(self):
        """ returns the background color for the chart """
        return self.__get_value('graphics:background-color')

    def row_background_color(self):
        """ returns the background color for alternate rows of the chart """
        return self.__get_value('graphics:row-background-color')

    def set_alternate_color(self, alt_value):
        """ sets the alternate colors setting """
        self.__set_value('graphics:alternate-color', alt_value)

    def time_stamp_format(self):
        """ Get the number format used for ticks labels """
        return self.__get_value("layout:time-stamp-format")

    def set_time_stamp_format(self, formatvalue):
        """ set the number format used for ticks labels """
        self.__set_value("layout:time-stamp-format", formatvalue)

    def set_auto_time_stamp_format(self):
        """ set the number format used for ticks labels """
        lu = floor(log10(self.unit()))
        if lu<0:
            if lu<=-5:
                self.set_time_stamp_format(":.1E")
            else:
                self.set_time_stamp_format(":.{}f".format(-lu))
        else:
            if lu>=5:
                self.set_time_stamp_format(":.1E")
            else:
                self.set_time_stamp_format(":.0f")


    def rows(self):
        """ returns the collection of rows """
        if 'structure:rows' in self.settings:
            return self.settings['structure:rows']
        else:
            return []

    def set_height(self, height):
        """ sets the height of the canvas """
        self.height = height

    def set_width(self, width):
        """ sets the width of the canvas of the graph """
        self.width = width

    def __max_firing_time(self, actor):
        firings = actor.firing_intervals()
        result = 0.0
        for firing in firings:
            if firing[1]>result:
                result = firing[1]
        return result

    def __max_time_gantt(self, actors):
        result = 0.0
        for _, group in actors:
            for act in group:
                if not act is None:
                    act_max = self.__max_firing_time(act)
                    if act_max > result:
                        result = act_max
        return result

    def __max_time_eventseqs(self, eventseqs):
        result = 0.0
        for _, seq in eventseqs:
            if not seq is None:
                seq_max = seq[len(seq) - 1]
                if seq_max > result:
                    result = seq_max
        return result

    def default_unit(self, actors):
        length = self.__max_time_gantt(actors)
        return mathpow(10.0, floor(log10(length))-1)

    def default_unit_vectors(self, eventseqs):
        length = self.__max_time_eventseqs(eventseqs)
        return mathpow(10.0, floor(log10(length))-1)

    def default_length_gantt(self, actors):
        """ determine the length of the trace based on the firings in the trace in units. """
        result = self.__max_time_gantt(actors)
        if not self.unit() is None:
            result = result / self.unit()
        return result * (1+self.length_extension())

    def default_length_vectors(self, eventseqs):
        """ determine the length of the figure based on the event sequences in the trace in units. """
        result = self.__max_time_eventseqs(eventseqs)
        if not self.unit() is None:
            result = result / self.unit()
        return result * (1+self.length_extension())


    def __includes_label(self, label):
        if self.settings is None:
            return False
        for key in self.settings:
            if key.startswith(label):
                return True
        return False

    def __get_subtree(self, node_label):
        result = dict()
        if self.settings is None:
            return result
        for key in self.settings:
            if key.startswith(node_label):
                result[key[len(node_label)+1:]] = self.settings[key]
        return result

    def groups(self):
        """ returns the groups of actors that are drawn on a single row """
        if self.__includes_label('structure:groups'):
            return self.__get_subtree('structure:groups')
        else:
            return []

    def group(self, group):
        return self.settings['structure:groups:'+group]

    def __read_color_palette(self):
        self.__color_palette = self.settings['colors:palette']

    def __read_structure(self):
        """ get the structure information """
        if not self.__structure is None:
            return
        groups = self.groups()
        self.__structure = dict()
        for group in groups:
            # collect the actors to be represented in this row
            self.__structure[group] = list()
            acts = self.group(group)
            for act in acts:
                # they may be specified as a single name of a list of two lists
                # in the latter case the names are created by the cartesian product of
                # both lists to allow easy scenario specification
                if isinstance(act, list):
                    for scen in act[0]:
                        for scact in act[1]:
                            self.__structure[group].append(scen+SCENARIO_SEPARATOR+scact)
                else:
                    self.__structure[group].append(act)

    def structure(self):
        self.__read_structure()
        return self.__structure


    def __read_color_map(self):
        self.__color_index_map = self.__get_subtree('colors:color-map')

        color_palette = self.color_palette()
        self.__color_map = dict()

        self.__read_structure()

        # assign colors according to settings
        for act_or_group in self.__color_index_map:
            if act_or_group in self.__structure:
                for act in self.__structure[act_or_group]:
                    self.__color_map[act] = color_palette[self.__color_index_map[act_or_group]]
            else:
                self.__color_map[act_or_group] = color_palette[self.__color_index_map[act_or_group]]

    # return the color palette, default to the given default palette
    def _color_palette_with_default(self, default):
        if not self.__color_palette is None:
            return self.__color_palette
        #if none specified return DEFAULT
        if not 'colors:palette' in self.settings:
            self.__color_palette = default
            return self.__color_palette
        #if not already parsed then parse
        if self.__color_palette is None:
            self.__read_color_palette()
            return self.__color_palette

    def color_palette(self):
        """ return the color palette, but default to the fill color palette """
        return self._color_palette_with_default(COLORPALETTE_FILLS)

    def color_palette_lines(self):
        """ return the color palette, but default to the lines color palette """
        return self._color_palette_with_default(COLORPALETTE_LINES)

    def set_default_color_palette_fill(self):
        """ set the defult color palette for fills"""
        if 'colors:palette' in self.settings:
            self.settings.pop('colors:palette')
        self.__color_palette = COLORPALETTE_FILLS
        return self.__color_palette

    def set_default_color_palette_lines(self):
        """ set the defult color palette for lines"""
        if 'colors:palette' in self.settings:
            self.settings.pop('colors:palette')
        self.__color_palette = COLORPALETTE_LINES
        return self.__color_palette

    def color_map(self):
        """ return a dict mapping actor names to colors. If nothing is specified in the settings it returns an empty dict. """
        # if none specified return empty map
        if not self.__includes_label('colors:color-map'):
            return None
        # if specified parse if needed
        if self.__color_map is None:
            self.__read_color_map()
        # return map
        return self.__color_map

    def set_default_actor_color_map(self, actornames):
        """ set the color map for the given list of actor names """
        self.color_palette()
        self.__color_index_map = dict()
        self.__color_map = dict()
        cix = 0
        for actname in actornames:
            self.__color_index_map[actname] = cix
            self.__color_map[actname] = self.__color_palette[cix]
            cix = (cix + 1) % len(self.__color_palette)
        self.settings['colors:color-map'] = self.__color_map

    def set_default_scenario_color_map(self, actors):
        """ set the scenario color map for the given list of actors """
        self.color_palette()
        self.__color_index_map = dict()
        self.__color_map = dict()
        scenarios = set()
        for _, acts in actors:
            for act in acts:
                scenarios.add(act.scenario)
        cix = 0
        for sc in scenarios:
            self.__color_index_map[sc] = cix
            self.__color_map[sc] = self.__color_palette[cix]
            cix = (cix + 1) % len(self.__color_palette)
        self.settings['colors:color-map'] = self.__color_map

    def set_default_sequence_color_map(self, tokennames):
        """ set the color map for the given list of token names """
        self.color_palette_lines()
        self.__color_index_map = dict()
        self.__color_map = dict()
        cix = 0
        for token in tokennames:
            self.__color_index_map[token] = cix
            self.__color_map[token] = self.__color_palette[cix]
            cix = (cix + 1) % len(self.__color_palette)
        self.settings['colors:color-map'] = self.__color_map

    def set_color_map(self, color_map):
        """ set the color map """
        self.settings['colors:color-map'] = color_map
        self.__color_map = color_map

 