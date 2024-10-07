""" support for generating graphics of traces and Gantt charts in SVG """
from math import floor
import os
from functools import reduce
from sys import modules as sysmodules
from cmtrace.graphics.svgcanvas import SVGCanvas, MM_PER_PT
from cmtrace.graphics.tracesettings import TraceSettings
if 'cairosvg' in sysmodules:
    import cairosvg

class SVGTraceDrawer:
    """ Helper for drawing trace figures """

    def __init__(self, settings=None):
        """initialization"""
        self.font_size = "10pt"
        self.canvas = None
        self.settings = settings if not settings is None else TraceSettings()

    def event_radius(self):
        """ get event radius in mm """
        return self.settings.event_radius()*self.settings.scale_mm_per_unit_y()

    def alternate_color(self, col):
        """ modify the color to be used for alternating colors """
        return (col[0] * 0.9, col[1] * 0.9, col[2] * 0.9)

    def draw_firings(self, firing_intervals, lb, _ub):
        """ draw firings in figure; firings are tuple (start, end, actor name, scenario name)"""
        # sort the firings on start time
        firing_intervals.sort()

        # determine number of overlapping intervals
        epsilon = 1e-5
        active_intervals = []
        max_active_intervals = 0
        for i in firing_intervals:
            active_intervals = [f for f in active_intervals if f[1] > i[0] + epsilon]
            if len(active_intervals) > max_active_intervals:
                max_active_intervals = len(active_intervals)
            active_intervals.append(i)

        coloring_mode = self.settings.firing_color_mode()
        color_map = self.settings.color_map()
        color_palette = self.settings.color_palette()

        f_count = 0
        # track overlapping firings
        active_intervals = []

        last_end = 0.0
        active_offset = 0

        for firing in firing_intervals:
            if coloring_mode == "by-actor":
                f_color = color_map[firing[2]]
            elif coloring_mode == "by-iteration":
                f_color = color_palette[firing[5] % len(color_palette)]
            elif coloring_mode == "by-scenario":
                f_color = color_map[firing[3]]
            if self.settings.alternate_color():
                if f_count%2 == 1:
                    f_color = self.alternate_color(f_color)


            # make sure that zero-length firings are visible
            if firing[1] - firing[0] < 1e-5:
                f_start = firing[0] - 0.05
                f_duration = 0.1
            else:
                # do not draw outside of the range
                f_start = firing[0]
                f_duration = firing[1]-firing[0]

            if f_start > last_end - epsilon:
                active_offset = 0
            else:
                active_offset = (active_offset+1) % (max_active_intervals+1)


            if f_start + f_duration > 0.0:
                f_start = max(f_start, 0.0)
                top_left = self.settings.origin_x() + f_start * \
                            self.settings.scale_mm_per_unit_x(), self.settings.origin_y() \
                            +(lb+self.settings.overlap_offset()*active_offset)* \
                            self.settings.scale_mm_per_unit_y()
                width_height = self.settings.scale_mm_per_unit_x()*(f_duration), \
                            self.settings.scale_mm_per_unit_y()
                self.canvas.draw_rect(top_left, width_height, f_color,
                                      stroke_width=self.settings.firing_stroke_width())
                if firing[4] is not None:
                    self.canvas.draw_text(
                        firing[4],
                        (top_left[0]+width_height[0]/2, top_left[1]+width_height[1]/2),
                        font=self.settings.font(),
                        font_size=0.5*self.settings.font_size(),
                        text_anchor="middle",
                        alignment_baseline="central"
                    )

            f_count += 1
            last_end = f_start+f_duration

    def draw_label(self, label, y_center):
        """ draw a label at y_center """

        lx = self.settings.origin_x() - self.settings.label_separation()
        ly = self.settings.origin_y()+y_center*self.settings.scale_mm_per_unit_y()
        self.canvas.draw_text(label, (lx, ly), font=self.settings.font(),
                              font_size=self.settings.font_size(), text_anchor="end",
                              alignment_baseline="central")

    def draw_traces(self, actors, num_arrivals, trace_heights):
        """ draw the actor traces. arrivals is used to determine the row to
        start drawing traces. """

        # compute the upper and lower bounds
        lb = []
        ub = []
        ll = 0.0
        for h in trace_heights:
            lb.append(ll)
            ub.append(ll+h)
            ll += h

        unit = self.settings.unit()
        mix = num_arrivals
        for (label, actor_list) in actors:
            self.draw_label(label, 0.5*(lb[mix]+ub[mix]))
            scaled_firings = []
            for actor in actor_list:
                if not actor is None:
                    fix = 0
                    for firing in actor.firing_intervals():
                        scaled_firings.append([firing[0]/unit, firing[1]/unit,
                                               actor.name, actor.scenario, firing[3], fix])
                        fix += 1
            self.draw_firings(scaled_firings, lb[mix], ub[mix])
            mix += 1

    def draw_arrivals(self, arrivals, offset):
        """ draw the arrival event sequences """
        # coloring_mode = self.settings.vector_color_mode()
        # color_index = self.settings.color_map()
        nix = offset
        for label in arrivals.keys():
            # draw the label
            self.canvas.draw_text(
                label,
                (self.settings.origin_x() - self.settings.label_separation(),
                 self.settings.origin_y()+(nix+0.5)*self.settings.scale_mm_per_unit_y()),
                font=self.settings.font(),
                font_size=self.settings.font_size(),
                text_anchor="end",
                alignment_baseline="central"
            )
            # draw the events
            f_color = [(0,0,0)] * len(arrivals[label])
            self._draw_sequence(arrivals[label], nix, f_color)
            nix += 1

    def _draw_sequence(self, seq, nix, f_color):
        eix = 0
        prev = None
        for arrival in seq:
            overlapped = False
            if prev is not None:
                if (arrival - prev) / self.settings.unit()*self.settings.scale_mm_per_unit_x() < \
                self.settings.overlap_horizontal_offset():
                    overlapped = True
                    arrival = prev + self.settings.overlap_horizontal_offset() / \
                        self.settings.scale_mm_per_unit_x() *  self.settings.unit()
            prev = arrival
            c_color = f_color[eix % len(f_color)]
            if arrival < 0.0:
                arrival = - self.settings.unit()
            pos = (self.settings.origin_x() + arrival/self.settings.unit()* \
                   self.settings.scale_mm_per_unit_x(), self.settings.origin_y() + \
                   (nix+0.5)*self.settings.scale_mm_per_unit_y())
            if overlapped:
                self.canvas.draw_circle(pos, self.event_radius()*1.15, (255, 255, 255), 0.0)
            self.canvas.draw_circle(pos, self.event_radius(), c_color, 0.0)

            eix += 1

    def _make_color_list(self,seq, coloring_mode, color_index, label):
        # determine the color
        if coloring_mode == "by-iteration":
            # TODO: make color by iteration
            f_color = []
            # TODO: make the following list in a smarter way
            for k in range(0, len(seq)):
                f_color.append(self.settings.color_palette()[k % \
                                                             len(self.settings.color_palette())])
        else:
            f_color = color_index[label] * len(seq)
        return f_color


    def draw_sequences(self, sequences):
        """ draw event sequences """
        coloring_mode = self.settings.vector_color_mode()
        color_index = self.settings.color_map()
        nix = 0
        for (label, seq) in sequences:
            # draw the label
            lx = self.settings.origin_x() - self.settings.label_separation()
            ly = self.settings.origin_y()+(nix+0.5)*self.settings.scale_mm_per_unit_y() + \
                3.0*MM_PER_PT
            self.canvas.draw_text(
                label,
                (lx, ly),
                font=self.settings.font(),
                font_size=self.settings.font_size(),
                text_anchor="end",
                alignment_baseline="central"
            )
            f_color = self._make_color_list(seq, coloring_mode, color_index, label)
            self._draw_sequence(seq, nix, f_color)
            nix += 1

    def draw_axes_back(self, xsize, ysize):
        """draw the background part of the axes"""
        self.draw_axes_back_variable_height(xsize, [1.0]*ysize)

    def draw_axes_back_variable_height(self, x_size, y_sizes):
        """ draw the background part of the axes, xsize measured by the time axis,
        y_sizes contains the size, per lane of the Gantt chart, in vertical units"""
        total_y = reduce(lambda x,y: x+y, y_sizes)
        self.canvas.draw_rect((self.settings.origin_x(), self.settings.origin_y()), \
                              (x_size/self.settings.unit()*self.settings.scale_mm_per_unit_x(), \
                               total_y*self.settings.scale_mm_per_unit_y()), \
                                self.settings.background_color(), 0.0)

        # draw the even rows darker background
        lower = 0.0
        for y_val in range(1, len(y_sizes), 2):
            lower = lower + y_sizes[y_val-1]
            upper = lower + y_sizes[y_val]
            self.canvas.draw_rect((self.settings.origin_x(), self.settings.origin_y()+ \
                            lower*self.settings.scale_mm_per_unit_y()),
                            (x_size/self.settings.unit()*self.settings.scale_mm_per_unit_x(), \
                             (upper-lower)*self.settings.scale_mm_per_unit_y()), \
                                self.settings.row_background_color(), 0.0)
            lower = upper

        # draw the vertical lines every 5th unit
        x_val = 0
        while x_val <= x_size:
            # compute the x position for the line
            x_pos = self.settings.origin_x()+x_val/self.settings.unit()* \
                self.settings.scale_mm_per_unit_x()
            # draw vertical tick line
            self.canvas.draw_line((x_pos, self.settings.origin_y()), (x_pos, \
                                            self.settings.origin_y()-self.settings.tick_length()), \
                                                self.settings.column_line_width())
            # draw vertical line across the whole chart
            self.canvas.draw_line((x_pos, self.settings.origin_y()), (x_pos, \
                            self.settings.origin_y()+total_y*self.settings.scale_mm_per_unit_y()), \
                            self.settings.column_line_width())
            # determine the time label
            strval = self._format_value(x_val)
            # add the text to the figure
            self.canvas.draw_text(strval, (x_pos, self.settings.origin_y() - \
                    self.settings.tick_number_separation()), font_size=self.settings.font_size(), \
                    font=self.settings.font(), text_anchor="middle")
            # determine the next value for a line
            x_val += 5*self.settings.unit()


    def _format_value(self, val):
        # ensure the format is set
        if self.settings.time_stamp_format() == 'auto':
            self.settings.set_auto_time_stamp_format()
        str_format = '{' + self.settings.time_stamp_format() + '}'
        return str_format.format(val)


    def draw_axes_middle(self, _, ysize):
        """ draw the middle part of the axes; in front of the actor firings, but behind
        the arrival dots. """
        self.canvas.draw_line(
            (self.settings.origin_x(), self.settings.origin_y() - \
             self.settings.border_line_width()*0.5),
            (self.settings.origin_x(), self.settings.origin_y() + \
             self.settings.scale_mm_per_unit_y()*ysize + self.settings.border_line_width()*0.5),
            self.settings.border_line_width()
        )

    def draw_axes_front(self, xsize, ysize):
        """ draw the front part of the axes """
        # draw horizontal axes
        self.canvas.draw_line(
            (self.settings.origin_x(), self.settings.origin_y()),
            (self.settings.origin_x()+self.settings.scale_mm_per_unit_x()* \
             xsize/self.settings.unit(), self.settings.origin_y()),
            self.settings.border_line_width()
        )
        self.canvas.draw_line(
            (self.settings.origin_x(), self.settings.origin_y()+ \
             self.settings.scale_mm_per_unit_y()*ysize),
            (self.settings.origin_x()+self.settings.scale_mm_per_unit_x()*xsize/ \
             self.settings.unit(), self.settings.origin_y()+ \
                self.settings.scale_mm_per_unit_y()*ysize),
            self.settings.border_line_width()
        )

    def __label_size(self, labels):
        """ estimate the size of the label """
        length = max(map(lambda act: (SVGCanvas.text_extent(act, self.settings.font(),
                                                            self.settings.font_size()))[1], labels))
        return length + 2* self.settings.label_separation()

    def save(self):
        """ save the figure """
        self.canvas.save()

    def _actor_names(self, actors):
        actor_names = []
        for row in actors:
            for act in row[1]:
                if not act is None:
                    actor_names.append(act.name)
        return actor_names

    def _actor_labels(self, actors):
        return list(map(lambda act: act[0], actors))


    def required_height(self, actor_group):
        '''Determine the required height for the event sequence depending in max
        number of overlapping firings '''
        # collect intervals for all actors in actor group
        intervals = list(reduce(lambda f_new, fall: fall+f_new, [(list(a.firing_intervals()) if
                                        a is not None else []) for a in actor_group],[]))
        # sort intervals on start time
        intervals.sort(key=lambda i: i[0])

        # determine max overlapping intervals
        epsilon = 1e-5
        active_intervals = []
        max_active_intervals = 0
        # for each interval
        for i in intervals:
            # which previous intervals are still active?
            active_intervals = [f for f in active_intervals if f[1] > i[0] + epsilon]
            # keep track of max
            if len(active_intervals) > max_active_intervals:
                max_active_intervals = len(active_intervals)
            active_intervals.append(i)

        return 1.0 + max_active_intervals * self.settings.overlap_offset()


    def make_gantt_svg(self, actors, arrivals, outputs, filename):
        """
        make a Gantt chart
        actors is a dict with names and TraceActor object
        arrivals and outputs are dicts with names and lists of time stamps
        """
        # get the actor names
        actor_names = self._actor_names(actors)

        # determine required height
        trace_heights = [1.0] * len(arrivals) + [self.required_height(actor_group) for (label,
                                actor_group) in actors] + [1.0]*len(outputs)
        total_height = reduce(lambda h, s: h+s, trace_heights)

        # determine settings
        if self.settings.unit() is None:
            self.settings.set_unit(self.settings.default_unit(actors))
        if self.settings.unit() == 'auto':
            self.settings.set_unit(self.settings.default_unit(actors))
        if self.settings.length() is None:
            self.settings.set_length(self.settings.default_length_gantt(actors))
        if self.settings.length() == 'auto':
            self.settings.set_length(self.settings.default_length_gantt(actors))
        if self.settings.height is None:
            self.settings.height = total_height * self.settings.scale_mm_per_unit_y() + \
                (self.settings.margin_top()+self.settings.margin_bottom())
        offset_x = self.__label_size(self._actor_labels(actors) + list(arrivals.keys()) + \
                                     list(outputs.keys()))
        if self.settings.width is None:
            self.settings.width = self._gantt_width(offset_x)

        if self.settings.color_map() is None:
            if self.settings.firing_color_mode() == 'by-scenario':
                self.settings.set_default_scenario_color_map(actors)
            else:
                self.settings.set_default_actor_color_map(actor_names)

        # create the canvas
        self.canvas = SVGCanvas(filename, self.settings.height, self.settings.width)
        # set the canvas view box
        self.canvas.set_view_box(-offset_x, -self.settings.margin_top(), self.settings.width, self.settings.height)

        time_axis_length = self.settings.length()*self.settings.unit()

        # draw the axes, traces and arrivals
        self.draw_axes_back_variable_height(time_axis_length, trace_heights)
        self.draw_traces(actors, len(arrivals), trace_heights)
        self.draw_axes_middle(time_axis_length, total_height)
        self.draw_arrivals(arrivals, 0)
        self.draw_arrivals(outputs, total_height - len(outputs))
        self.draw_axes_front(time_axis_length, total_height)

        # return the result
        return self.canvas

    def _gantt_width(self, offset_x):
        """" Determine the width, accounting for the last label """
        m = floor(self.settings.length() / 5)
        label_center = m*5*self.settings.scale_mm_per_unit_x()
        last_label = self._format_value(m*5*self.settings.unit())
        last_label_end = label_center + 0.5 * SVGCanvas.text_extent(last_label,
                                            self.settings.font(), self.settings.font_size())[1]
        gantt_width = (self.settings.length()) * self.settings.scale_mm_per_unit_x()

        return offset_x + max(last_label_end, gantt_width)


    def save_gantt(self, actors, arrivals, outputs, filename='trace.svg'):
        """ make a Gantt chart in svg and save to file """
        canvas = self.make_gantt_svg(actors, arrivals, outputs, filename)
        canvas.save()

    def __make_vector_svg(self, event_seqs, filename='trace.svg', _height_in_mm=200,
                          _width_in_mm=300):
        """ make a graph in svg of the event sequences and save to file """

        # determine settings
        if self.settings.unit() is None:
            self.settings.set_unit(self.settings.default_unit_vectors(event_seqs))
        if self.settings.unit() == "auto":
            self.settings.set_unit(self.settings.default_unit_vectors(event_seqs))
        if self.settings.length() is None:
            self.settings.set_length(self.settings.default_length_vectors(event_seqs))
        if self.settings.length() == "auto":
            self.settings.set_length(self.settings.default_length_vectors(event_seqs))
        if self.settings.height is None:
            self.settings.height = len(event_seqs) * self.settings.scale_mm_per_unit_y() + \
                (self.settings.margin_top()+self.settings.margin_bottom())
        offset_x = self.__label_size(list(event_seqs.keys()))
        if self.settings.width is None:
            self.settings.width = self.settings.length() * self.settings.scale_mm_per_unit_x() + \
                offset_x
        if self.settings.color_map() is None:
            token_names = list()
            for row in event_seqs:
                token_names.append(row[0])
            self.settings.set_default_sequence_color_map(token_names)

        # create the canvas
        self.canvas = SVGCanvas(filename, self.settings.height, self.settings.width)
        self.canvas.set_view_box(-offset_x, -self.settings.margin_top(), self.settings.width,
                                 self.settings.height)

        # draw the axes and sequences
        self.draw_axes_back(self.settings.length(), len(event_seqs))
        self.draw_axes_middle(self.settings.length(), len(event_seqs))
        self.draw_sequences(event_seqs)
        self.draw_axes_front(self.settings.length(), len(event_seqs))

        # return the result
        return self.canvas

    def save_vector(self, events_seqs, filename):
        """ make a graph in svg of the event sequences and save to file """
        canvas = self.__make_vector_svg(events_seqs, filename)
        canvas.save()

def darken(color, factor=0.8):
    """ make a color darker """
    return (int(factor*color[0]), int(factor*color[1]), int(factor*color[2]))

def convert_svg_to_pdf(svg_file, pdf_file=None):
    """ convert svg drawing file to pdf file """
    if pdf_file is None:
        pdf_file = (os.path.splitext(svg_file)[0]) + ".pdf"
    # if not 'cairosvg' in sysmodules:
    #     print("Module cairosvg is not installed. Cannot convert SVG to PDF.")
    # else:
    #     cairosvg.svg2pdf(
    #         file_obj=open(svg_file, "rb"), write_to=pdf_file)

def save_vector_svg(events_seqs, filename='trace.svg', settings=None):
    """ draw a vector trace """
    drawer = SVGTraceDrawer(settings)
    drawer.save_vector(events_seqs, filename)

# TODO: add the structural part of actors to the settings (structure)
def save_gantt_svg(actors, arrivals, outputs, filename='trace.svg', settings=None):
    """
    draw a Gantt chart trace
    """
    drawer = SVGTraceDrawer(settings)
    drawer.save_gantt(actors, arrivals, outputs, filename)
