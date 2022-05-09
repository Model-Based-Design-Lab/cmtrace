
'''Script to create an SVG figures from a trace '''

import argparse
from cmtrace.graphics.tracesettings import TraceSettings
from cmtrace.libtracetosvg import create_gantt_fig, create_vector_fig

from cmtrace.graphics.tracesettings import TraceSettingsException


def main():
    parser = argparse.ArgumentParser(description='Create an svg or pdf figure from a trace file.')
    parser.add_argument('tracefile', help="the xml trace file")
    parser.add_argument('outputfile', help="the outputfile to write the pdf or svg file to")
    parser.add_argument('-s', '--settings', dest='settings', help="YAML file with settings for the layout of the figure")
    parser.add_argument('-t', '--type', dest='type', choices=['Gantt', 'vector'], default='Gantt', help="type is either Gantt (default) or vector")

    args = parser.parse_args()

    settings = TraceSettings()
    if 'settings' in args:
        if not args.settings is None:
            try:
                settings.parse_settings(args.settings)
            except TraceSettingsException:
                # TODO: show exception message
                print("There was an error reading the settings file.")


    if args.type == 'Gantt':
        create_gantt_fig(args.tracefile, args.outputfile, settings=settings)
    else:
        create_vector_fig(args.tracefile, args.outputfile, settings=settings)
