""" support for generating graphics in SVG """
import svgwrite
import cairo
from cmtrace.latexsvg.latexsvg import latex_to_svg

# conversion constants
MM_PER_PT = 0.352778

# default font size
DEFAULT_FONT_SIZE = 10
DEFAULT_FONT = "Calibri, Arial"

# scaling factor to make latex formulas appear in the correct size
LATEX_SCALE = 1.4

class SVGCanvas:
    """ Canvas object to create SVG drawings. """

    def __init__(self, filename='canvas.svg', height_in_mm=200, width_in_mm=300):
        height = str(height_in_mm)+'mm'
        width = str(width_in_mm)+'mm'
        # create the SVG drawing
        self.drawing = svgwrite.Drawing(filename, size=(width, height), profile='full')
        # set the view box
        self.drawing.viewbox(0, 0, width_in_mm, height_in_mm)
        # add marker to be used for arrows
        self.arrow_marker = self.drawing.marker(id='arrow', insert=(9, 3), \
                            size=(6, 6), orient='auto', markerUnits='strokeWidth')
        self.arrow_marker.add(self.drawing.path(d='M0,0 L0,6 L9,3 z', fill='#f00'))
        # add the arrow marker to defs section of the drawing
        self.drawing.defs.add(self.arrow_marker)
        # set the font size to the default size
        self.font_size= DEFAULT_FONT_SIZE

    def set_font_size(self, font_size):
        """ set the default font size for draw_text """
        self.font_size = font_size

    def set_view_box(self, xmin, ymin, width, height):
        """ set the viewbox """
        self.drawing.viewbox(xmin, ymin, width, height)

    @staticmethod
    def text_extent(text, font=DEFAULT_FONT, font_size=14):
        """ Return height and width of the text in given font and font """
        surface = cairo.SVGSurface(None, 1000, 1000)
        # surface.set_document_unit(cairo.SVG_UNIT_MM)
        cr = cairo.Context(surface)
        cr.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(font_size)
        xbearing, ybearing, width, height, xadvance, yadvance = cr.text_extents(text)
        return height, width

    def draw_text(self, text, insert, fill=(0, 0, 0), font_size=None,
                  font=DEFAULT_FONT, text_anchor="start", alignment_baseline="auto"):
        """ draw a piece of text at point 'insert' using color 'fill' anchoring
        according to 'text_anchor' """
        # if font size is not specified, use the default
        if font_size is None:
            the_font_size = self.font_size
        else:
            # else set from argument
            the_font_size = font_size

        y_offset = 0.0
        if alignment_baseline=="central":
            y_offset = 0.25*the_font_size

        # add text element to the drawing
        self.drawing.add(self.drawing.text(text, insert=(insert[0], insert[1] + \
                                    y_offset), fill=svgwrite.rgb(*fill), \
            font_size=the_font_size, font_family=font, text_anchor=text_anchor, \
                alignment_baseline="auto"))

    def draw_rect(self, insert, size, fillcolor=(0, 0, 0), stroke_width=MM_PER_PT, \
                  stroke_color=(0, 0, 0)):
        """ draw a rectangle """
        # add rectangle to the drawing
        self.drawing.add(self.drawing.rect(insert=(insert[0], insert[1]), size=(size[0], size[1]), \
                    fill=svgwrite.rgb(*fillcolor), stroke_width=stroke_width, \
                    stroke=svgwrite.rgb(*stroke_color)))

    def draw_line(self, start, end, stroke_width=MM_PER_PT, stroke_color=(0, 0, 0)):
        """
        draw a line from start (x1, y1) to end (x2, y2), using stroke_width
        """
        self.drawing.add(self.drawing.line(start=(start[0], start[1]), end=(end[0], end[1]), \
                    stroke_width=stroke_width, stroke=svgwrite.rgb(*stroke_color)))

    def draw_path(self, path_spec, stroke_width=MM_PER_PT, stroke_color=(0, 0, 0), is_arrow=False, \
                  fill='none', offset_pre=None, offset_post=None,
                  scale=None):
        """ add a path to the drawing, optionally apply offset and scale and optionally make
        it an arrow """
        # check if adding a transformation is required
        if (offset_pre is None) and (offset_post is None) and (scale is None):
            container = self.drawing
        else:
            if scale is None:
                scale = 1.0
            if offset_pre is None:
                offset_pre = (0, 0)
            if offset_post is None:
                offset_post = (0, 0)
            # create a container with the appropriate transformation
            # first translate moves anchor point to origin, then scaling is applied,
            # finally the anchor point is moved to its final location
            container = svgwrite.container.Group(
                transform=f'translate({offset_pre[0]},{offset_pre[1]}) scale({scale})" \
                    f"translate({offset_post[0]},{offset_post[1]})')
            self.drawing.add(container)

        # create the path
        path = container.add(self.drawing.path(d=path_spec, \
                    stroke_width=stroke_width, stroke=svgwrite.rgb(*stroke_color), fill=fill))
        # if it is an arrow, add the arrow head marker to the end of the path
        if is_arrow:
            path.set_markers((None, None, self.arrow_marker))

    def draw_circle(self, insert, radius, fillcolor=(0, 0, 0), stroke_width=MM_PER_PT,
                    stroke_color=(0, 0, 0)):
        """ draw a circle """
        self.drawing.add(self.drawing.circle(center=(insert[0], insert[1]), r=radius, \
                    fill=svgwrite.rgb(*fillcolor), stroke_width=stroke_width, \
                    stroke=svgwrite.rgb(*stroke_color)))

    def draw_text_latex(self, latex_str, color, position, anchor=(0, 0), scale=1.0):
        """ Add text with LaTeX equation formatting at the relative anchor point
        and apply optional scale."""
        # invoke to latex_to_svg to deliver a collection of glyphs and instances of those glyphs
        glyphs, instances, width, height = latex_to_svg(latex_str)
        # determine the absolute anchor point
        anchor_abs = (-anchor[0]*width, -anchor[1]*height)
        # draw all the instances in the LaTeX result
        for (coords, glyph) in instances:
            # compute the offset for the current glyph instance from the absolute
            # anchor and the coors of the glyph
            offset = [sum(x) for x in zip(coords, anchor_abs)]
            # draw the glyph as a path on the SVG drawing
            self.draw_path(glyphs[glyph[1:]], stroke_width=0.0, fill=color, \
                           offset_post=offset, offset_pre=position, scale=LATEX_SCALE*scale)

    def save(self):
        """ save the canvas to a file """
        self.drawing.save()
