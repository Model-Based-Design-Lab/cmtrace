""" support for generating graphics of traces and Gantt charts in SVG """
from math import floor
import os
from functools import reduce
from sys import modules as sysmodules
from cmtrace.graphics.svgcanvas import SVGCanvas, MMPERPT, DEFAULTFONT
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

    def eventradius(self):
        """ get event radius in mm """
        return self.settings.event_radius()*self.settings.scale_mm_per_unit_y()

    def alternate_color(self, col):
        """ modify the color to be used for alternating colors """
        return (col[0] * 0.9, col[1] * 0.9, col[2] * 0.9)

    def draw_firings(self, firing_intervals, lb, ub):
        """ draw firings in figure; firings are tuple (start, end, actor name, scenario name)"""
        # sort the firings on start time
        firing_intervals.sort()

        # determine number of overlapping intervals
        epsilon = 1e-5
        activeIntervals = []
        maxActiveIntervals = 0
        for i in firing_intervals:
            activeIntervals = [f for f in activeIntervals if f[1] > i[0] + epsilon]
            if len(activeIntervals) > maxActiveIntervals:
                maxActiveIntervals = len(activeIntervals)
            activeIntervals.append(i)


        coloring_mode = self.settings.firing_color_mode()
        color_map = self.settings.color_map()
        color_palette = self.settings.color_palette()

        fcount = 0
        # track overlapping firings 
        activeIntervals = []
        
        lastEnd = 0.0
        activeOffset = 0

        for firing in firing_intervals:
            if coloring_mode == "by-actor":
                fcolor = color_map[firing[2]]
            elif coloring_mode == "by-iteration":
                fcolor = color_palette[firing[4] % len(color_palette)]
            elif coloring_mode == "by-scenario":
                fcolor = color_map[firing[3]]
            if self.settings.alternate_color():
                if fcount%2 == 1:
                    fcolor = self.alternate_color(fcolor)


            # make sure that zero-length firings are visible
            if firing[1] - firing[0] < 1e-5:
                fstart = firing[0] - 0.05
                fduration = 0.1
            else:
                # do not draw outside of the range
                fstart = firing[0]
                fduration = firing[1]-firing[0]

            if fstart > lastEnd - epsilon:
                activeOffset = 0
            else:
                activeOffset = (activeOffset+1) % (maxActiveIntervals+1)


            if fstart + fduration > 0.0:
                fstart = max(fstart, 0.0)
                self.canvas.draw_rect((self.settings.origin_x() + fstart*self.settings.scale_mm_per_unit_x(), self.settings.origin_y()+(lb+self.settings.overlap_offset()*activeOffset)*self.settings.scale_mm_per_unit_y()), \
                                    (self.settings.scale_mm_per_unit_x()*(fduration), self.settings.scale_mm_per_unit_y()), fcolor, stroke_width=self.settings.firing_stroke_width())
            fcount += 1
            lastEnd = fstart+fduration

    def draw_label(self, label, ycenter):
        """ draw a label at ycenter """

        lx = self.settings.origin_x() - self.settings.label_separation()
        ly = self.settings.origin_y()+ycenter*self.settings.scale_mm_per_unit_y()
        self.canvas.draw_text(label, (lx, ly), font=self.settings.font(), fontsize=self.settings.fontsize(), textanchor="end", alignmentbaseline="central")

    def draw_traces(self, actors, num_arrivals, traceHeights):
        """ draw the actor traces. arrivals is used to determine the row to start drawing traces. """

        # compute the upper and lower bounds
        lb = []
        ub = []
        ll = 0.0
        for h in traceHeights:
            lb.append(ll)
            ub.append(ll+h)
            ll += h

        unit = self.settings.unit()
        mix = num_arrivals
        for (label, actorlist) in actors:
            self.draw_label(label, 0.5*(lb[mix]+ub[mix]))
            scaled_firings = list()
            for actor in actorlist:
                if not actor is None:
                    fix = 0
                    for firing in actor.firing_intervals():
                        scaled_firings.append([firing[0]/unit, firing[1]/unit, actor.name, actor.scenario, fix])
                        fix += 1
            self.draw_firings(scaled_firings, lb[mix], ub[mix])
            mix += 1

    def draw_arrivals(self, arrivals, offset):
        """ draw the arrival event sequences """
        coloring_mode = self.settings.vector_color_mode()
        color_index = self.settings.color_map()
        nix = offset
        for label in arrivals.keys():
            # draw the label
            self.canvas.draw_text(
                label, 
                (self.settings.origin_x() - self.settings.label_separation(), self.settings.origin_y()+(nix+0.5)*self.settings.scale_mm_per_unit_y()),
                font=self.settings.font(), 
                fontsize=self.settings.fontsize(),
                textanchor="end",
                alignmentbaseline="central"
            )
            # draw the events
            fcolor = [(0,0,0)] * len(arrivals[label])
            self._draw_sequence(arrivals[label], nix, fcolor)
            nix += 1

    def _draw_sequence(self, seq, nix, fcolor):
        eix = 0
        prev = None
        for arriv in seq:
            overlapped = False
            if prev is not None:
                if (arriv - prev) / self.settings.unit()*self.settings.scale_mm_per_unit_x() < self.settings.overlap_horizontal_offset():
                    overlapped = True
                    arriv = prev + self.settings.overlap_horizontal_offset() / self.settings.scale_mm_per_unit_x() *  self.settings.unit()
            prev = arriv
            ccolor = fcolor[eix % len(fcolor)]
            if arriv < 0.0:
                arriv = - self.settings.unit()
            pos = (self.settings.origin_x() + arriv/self.settings.unit()*self.settings.scale_mm_per_unit_x(), self.settings.origin_y() + (nix+0.5)*self.settings.scale_mm_per_unit_y())
            if overlapped:
                self.canvas.draw_circle(pos, self.eventradius()*1.15, (255, 255, 255), 0.0)
            self.canvas.draw_circle(pos, self.eventradius(), ccolor, 0.0)

            eix += 1

    def _make_color_list(self,seq, coloring_mode, color_index, label):
        # determine the color
        if coloring_mode == "by-iteration":
            # TODO: make color by iteration
            fcolor = list()
            # TODO: make the following list in a smarter way
            for k in range(0, len(seq)):
                fcolor.append(self.settings.color_palette()[k % len(self.settings.color_palette())])
        else:
            fcolor = color_index[label] * len(seq)
        return fcolor


    def draw_sequences(self, sequences):
        """ draw event sequences """
        coloring_mode = self.settings.vector_color_mode()
        color_index = self.settings.color_map()
        nix = 0
        for (label, seq) in sequences:
            # draw the label
            lx = self.settings.origin_x() - self.settings.label_separation()
            ly = self.settings.origin_y()+(nix+0.5)*self.settings.scale_mm_per_unit_y() + 3.0*MMPERPT
            self.canvas.draw_text(
                label, 
                (lx, ly),
                font=self.settings.font(), 
                fontsize=self.settings.fontsize(),
                textanchor="end",
                alignmentbaseline="central"
            )
            fcolor = self._make_color_list(seq, coloring_mode, color_index, label)
            self._draw_sequence(seq, nix, fcolor)
            nix += 1

    def draw_axes_back(self, xsize, ysize):
        self.draw_axes_back_variable_height(xsize, [1.0]*ysize)


    def draw_axes_back_variable_height(self, xsize, ysizes):
        """ draw the background part of the axes, xsize measured by the ime axcis, ysizes contains the size, per lane of the Gantt chart, in vertical units"""
        totaly = reduce(lambda x,y: x+y, ysizes)
        self.canvas.draw_rect((self.settings.origin_x(), self.settings.origin_y()), (xsize/self.settings.unit()*self.settings.scale_mm_per_unit_x(), totaly*self.settings.scale_mm_per_unit_y()), self.settings.background_color(), 0.0)

        # draw the even rows darker background
        lower = 0.0
        for yval in range(1, len(ysizes), 2):
            lower = lower + ysizes[yval-1]
            upper = lower + ysizes[yval]
            self.canvas.draw_rect((self.settings.origin_x(), self.settings.origin_y()+lower*self.settings.scale_mm_per_unit_y()),
                                  (xsize/self.settings.unit()*self.settings.scale_mm_per_unit_x(), (upper-lower)*self.settings.scale_mm_per_unit_y()), self.settings.row_background_color(), 0.0)
            lower = upper

        # draw the vertical lines every 5th unit
        xval = 0
        while xval <= xsize:
            # compute the x position for the line
            xpos = self.settings.origin_x()+xval/self.settings.unit()*self.settings.scale_mm_per_unit_x()
            # draw vertical tick line
            self.canvas.draw_line((xpos, self.settings.origin_y()), (xpos, self.settings.origin_y()-self.settings.tick_length()), self.settings.column_linewidth())
            # draw vertical line across the whole chart
            self.canvas.draw_line((xpos, self.settings.origin_y()), (xpos, self.settings.origin_y()+totaly*self.settings.scale_mm_per_unit_y()), self.settings.column_linewidth())
            # determine the time label
            strval = self._formatValue(xval)
            # add the text to the figure
            self.canvas.draw_text(strval, (xpos, self.settings.origin_y() - self.settings.tick_number_separation()), fontsize=self.settings.fontsize(), font=self.settings.font(), textanchor="middle")
            # determine the next value for a line
            xval += 5*self.settings.unit()


    def _formatValue(self, val):
        # ensure the format is set
        if self.settings.time_stamp_format() == 'auto':
            self.settings.set_auto_time_stamp_format()
        strformat = '{' + self.settings.time_stamp_format() + '}'
        return strformat.format(val)
        

    def draw_axes_middle(self, _, ysize):
        """ draw the middle part of the axes; in front of the actor firings, but behind the arrival dots. """
        self.canvas.draw_line(
            (self.settings.origin_x(), self.settings.origin_y() - self.settings.border_linewidth()*0.5), 
            (self.settings.origin_x(), self.settings.origin_y() + self.settings.scale_mm_per_unit_y()*ysize + self.settings.border_linewidth()*0.5),
            self.settings.border_linewidth()
        )

    def draw_axes_front(self, xsize, ysize):
        """ draw the front part of the axes """
        # draw horizontal axes
        self.canvas.draw_line(
            (self.settings.origin_x(), self.settings.origin_y()), 
            (self.settings.origin_x()+self.settings.scale_mm_per_unit_x()*xsize/self.settings.unit(), self.settings.origin_y()),
            self.settings.border_linewidth()
        )
        self.canvas.draw_line(
            (self.settings.origin_x(), self.settings.origin_y()+self.settings.scale_mm_per_unit_y()*ysize), 
            (self.settings.origin_x()+self.settings.scale_mm_per_unit_x()*xsize/self.settings.unit(), self.settings.origin_y()+self.settings.scale_mm_per_unit_y()*ysize),
            self.settings.border_linewidth()
        )

    def __labelsize(self, labels):
        """ estimate the size of the label """
        length = max(map(lambda act: (SVGCanvas.text_extent(act, self.settings.font(), self.settings.fontsize()))[1], labels))
        return length + 2* self.settings.label_separation()
        

    def save(self):
        """ save the figure """
        self.canvas.save()

    def _actornames(self, actors):
        actornames = list()
        for row in actors:
            for act in row[1]:
                if not act is None:
                    actornames.append(act.name)
        return actornames

    def _actorLabels(self, actors):
        return list(map(lambda act: act[0], actors))


    def requiredHeight(self, actorgroup):
        '''Determine the required height for the evensequence depending in max number of overlapping firings '''
        # collect intervals for all actors in actor group
        intervals = list(reduce(lambda fnew, fall: fall+fnew, [list(a.firing_intervals()) for a in actorgroup],list()))
        # sort intervals on start time
        intervals.sort(key=lambda i: i[0])

        # determine max overlapping intervals
        epsilon = 1e-5
        activeIntervals = []
        maxActiveIntervals = 0
        # for each interval
        for i in intervals:
            # which previous intervals are still active?
            activeIntervals = [f for f in activeIntervals if f[1] > i[0] + epsilon]
            # keep track of max
            if len(activeIntervals) > maxActiveIntervals:
                maxActiveIntervals = len(activeIntervals)
            activeIntervals.append(i)
        
        return 1.0 + maxActiveIntervals * self.settings.overlap_offset()


    def make_gantt_svg(self, actors, arrivals, outputs, filename):
        """ 
        make a Gantt chart 
        actors is a dict with names and TraceActor object
        arrivals and outputs are dicts with names and lists of time stamps
        """
        # get the actor names
        actornames = self._actornames(actors)

        # determine required height 
        traceHeights = [1.0] * len(arrivals) + [self.requiredHeight(actorgroup) for (label, actorgroup) in actors] + [1.0]*len(outputs)
        totalHeight = reduce(lambda h, s: h+s, traceHeights)

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
            self.settings.height = totalHeight * self.settings.scale_mm_per_unit_y() + (self.settings.margin_top()+self.settings.margin_bottom())
        offset_x = self.__labelsize(self._actorLabels(actors) + list(arrivals.keys()) + list(outputs.keys()))
        if self.settings.width is None:
            self.settings.width = self._gantt_width(offset_x)

        if self.settings.color_map() is None:
            if self.settings.firing_color_mode() == 'by-scenario':
                self.settings.set_default_scenario_color_map(actors)
            else:
                self.settings.set_default_actor_color_map(actornames)
 
        # create the canvas
        self.canvas = SVGCanvas(filename, self.settings.height, self.settings.width)
        # set the canvas viewbox
        self.canvas.set_viewbox(-offset_x, -self.settings.margin_top(), self.settings.width, self.settings.height)

        timeAxisLengh = self.settings.length()*self.settings.unit()

        # draw the axes, traces and arrivals
        self.draw_axes_back_variable_height(timeAxisLengh, traceHeights)
        self.draw_traces(actors, len(arrivals), traceHeights)
        self.draw_axes_middle(timeAxisLengh, totalHeight)
        self.draw_arrivals(arrivals, 0)
        self.draw_arrivals(outputs, totalHeight - len(outputs))
        self.draw_axes_front(timeAxisLengh, totalHeight)
        
        # return the result
        return self.canvas

    def _gantt_width(self, offset_x):
        """" Determine the width, accounting for the last label """
        m = floor(self.settings.length() / 5)
        labelCenter = m*5*self.settings.scale_mm_per_unit_x()
        lastLabel = self._formatValue(m*5*self.settings.unit())
        lastLabelEnd = labelCenter + 0.5 * SVGCanvas.text_extent(lastLabel, self.settings.font(), self.settings.fontsize())[1]
        gantt_width = (self.settings.length()) * self.settings.scale_mm_per_unit_x()

        return offset_x + max(lastLabelEnd, gantt_width)


    def save_gantt(self, actors, arrivals, outputs, filename='trace.svg'):
        """ make a Gantt chart in svg and save to file """
        canvas = self.make_gantt_svg(actors, arrivals, outputs, filename)
        canvas.save()

    def __make_vector_svg(self, eventseqs, filename='trace.svg', height_in_mm=200, width_in_mm=300):
        """ make a graph in svg of the event sequences and save to file """

        # determine settings
        if self.settings.unit() is None:
            self.settings.set_unit(self.settings.default_unit_vectors(eventseqs))
        if self.settings.unit() == "auto":
            self.settings.set_unit(self.settings.default_unit_vectors(eventseqs))
        if self.settings.length() is None:
            self.settings.set_length(self.settings.default_length_vectors(eventseqs))
        if self.settings.length() == "auto":
            self.settings.set_length(self.settings.default_length_vectors(eventseqs))
        if self.settings.height is None:
            self.settings.height = len(eventseqs) * self.settings.scale_mm_per_unit_y() + (self.settings.margin_top()+self.settings.margin_bottom())
        offset_x = self.__labelsize(list(eventseqs.keys()))
        if self.settings.width is None:
            self.settings.width = self.settings.length() * self.settings.scale_mm_per_unit_x() + offset_x
        if self.settings.color_map() is None:
            tokennames = list()
            for row in eventseqs:
                tokennames.append(row[0])
            self.settings.set_default_sequence_color_map(tokennames)

        # create the canvas
        self.canvas = SVGCanvas(filename, self.settings.height, self.settings.width)
        self.canvas.set_viewbox(-offset_x, -self.settings.margin_top(), self.settings.width, self.settings.height)

        # draw the axes and sequences
        self.draw_axes_back(self.settings.length(), len(eventseqs))
        self.draw_axes_middle(self.settings.length(), len(eventseqs))
        self.draw_sequences(eventseqs)
        self.draw_axes_front(self.settings.length(), len(eventseqs))

        # return the result
        return self.canvas

    def save_vector(self, eventsseqs, filename):
        """ make a graph in svg of the event sequences and save to file """
        canvas = self.__make_vector_svg(eventsseqs, filename)
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

def save_vector_svg(eventsseqs, filename='trace.svg', settings=None):
    """ draw a vector trace """
    drawer = SVGTraceDrawer(settings)
    drawer.save_vector(eventsseqs, filename)

# TODO: add the structural part of actors to the settings (structure)
def save_gantt_svg(actors, arrivals, outputs, filename='trace.svg', settings=None):
    """ 
    draw a Gantt chart trace 
    """
    drawer = SVGTraceDrawer(settings)
    drawer.save_gantt(actors, arrivals, outputs, filename)

