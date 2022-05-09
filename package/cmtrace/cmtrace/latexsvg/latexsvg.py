""" convert LaTeX string to svg and extract data """

import os
import tempfile
import xml.etree.ElementTree as ET
from cmtrace.utils.shell import run_win_cmd

# get a temp folder to store temporary files
TEMPPATH = tempfile.gettempdir()

# a TeX document pre and post-ambe to encapsulate the formula
LTXPREAMBLE = """\\documentclass{article}
                \\usepackage{amssymb,amsmath}
                %\\usepackage{mathptmx}% Times Roman font
                \\usepackage{bm}
                \\pagestyle{empty}
                \\begin{document}
                \\begin{displaymath}
                \\setbox0\\hbox{$"""

LTXPOSTAMBLE = """$}%
                \\message{//\\the\\dp0//}%
                \\box0%
                \\end{displaymath}
                \\newpage
                \\end{document}"""


def latex_to_svg(latextstr, svgfilename='output.svg'):
    """ convert latex formula string to SVG file """

    # define temporary tex and dvi files
    temptexfile = os.path.join(TEMPPATH, 'tempinput.tex')
    tempdvifile = os.path.join(TEMPPATH, 'tempinput.dvi')

    # create the tex file
    with open(temptexfile, 'w') as file:
        file.write(LTXPREAMBLE)
        file.write(latextstr)
        file.write(LTXPOSTAMBLE)

    # run pdflatex and dvisvgm to convert the formula to SVG
    run_win_cmd("pdflatex  -interaction=nonstopmode -output-format=dvi -output-directory={0} {1}".format(TEMPPATH, temptexfile), True)
    run_win_cmd("dvisvgm --bbox=min -n {1} --stdout >{0}".format(svgfilename, tempdvifile), True)

    # parse the SVG file to find the content
    root = ET.parse(svgfilename)

    # a dictionary to store all the glyphs found in the SVG
    glyphs = dict()

    # get the top svg element
    svgel = root.find(".")
    # get the viewbox parameters as floats
    viewbox = list(map(lambda x: float(x), svgel.attrib['viewBox'].split()))
    xmin = viewbox[0]
    ymin = viewbox[1]
    width = viewbox[2]
    height = viewbox[3]

    # get all the path glyph definitions, def elements
    for elem in root.findall("./{http://www.w3.org/2000/svg}defs/{http://www.w3.org/2000/svg}path"):
        # store nanme and path
        glyphs[elem.attrib['id']] = elem.attrib['d']

    # get the path instances, use elements
    instances = list()
    for elem in root.findall("./{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}use"):
        # record the position, corrected for the viewport and the glyph it refers to
        instances.append(
            (
                (
                    float(elem.attrib['x']) - xmin, float(elem.attrib['y']) - ymin
                ),
                elem.attrib['{http://www.w3.org/1999/xlink}href']
            ))

    # delete the temporary tex and dvi files
    os.remove(temptexfile)
    os.remove(tempdvifile)

    # return the graphical data
    return glyphs, instances, width, height
