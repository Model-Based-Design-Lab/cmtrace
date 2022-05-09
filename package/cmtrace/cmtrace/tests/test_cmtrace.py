from unittest import TestCase

import cmtrace

from cmtrace.graphics.tracesettings import TraceSettings
from cmtrace.libtracetosvg import create_gantt_fig, create_vector_fig

import os

class Testcmtrace(TestCase):

    def _make_trace_test(self, tracefile, outfile):
        """ make a gantt chart named outfile, from tracefile with default settings """
        settings = TraceSettings()
        create_gantt_fig(tracefile, outfile, settings=settings)

    def _make_trace_vector_test(self, tracefile, outfile):
        """ make a vector trace chart named outfile, from tracefile with default settings """
        settings = TraceSettings()
        create_vector_fig(tracefile, outfile, settings=settings)

    def test_default_trace(self):
        """Create a Gantt chart for a simple example trace."""
        # Create traces for simple example examples/trace.xml
        settings = TraceSettings()
        exampledir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'example')
        tracefile = os.path.join(exampledir, 'trace.xml')

        # Create Gantt chart with default settings
        outputfile = os.path.join(exampledir, 'trace_default.svg')
        create_gantt_fig(tracefile, outputfile, settings=settings)

        # Create a Gantt chart with settings from specification
        outputfile = os.path.join(exampledir, 'trace_settings.svg')
        settingsfile = os.path.join(exampledir, 'settings.yaml')
        settings.parse_settings(settingsfile)
        create_gantt_fig(tracefile, outputfile, settings=settings)

    def test_default_vector_trace(self):
        """Create a Gantt chart for a simple example trace."""
        # To be done.
        self.assertTrue(False)

    def test_example_traces(self):
        """ make charts for the traces in example/traces """
        
        # get the example directory
        exampledir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'example')
        # get the output directory
        outputdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'output')
        # get the directory with Gantt input traces
        tracesdir = os.path.join(exampledir, 'traces', 'gantt')

        # for each trace file
        for tracefile in os.listdir(tracesdir):
            # get the base filename without extension
            filebase, _ = os.path.splitext(tracefile)
            # make the output file name
            outputname = filebase + '.svg'
            fulloutputfile = os.path.join(outputdir, outputname)
            # make the full input path
            fulltracefile = os.path.join(tracesdir, tracefile)
            # make the trace
            self._make_trace_test(fulltracefile, fulloutputfile)

        # get the directory with vector input traces
        tracesdir = os.path.join(exampledir, 'traces', 'vector')
        # for each trace file
        for tracefile in os.listdir(tracesdir):
            # get the base filename without extension
            filebase, _ = os.path.splitext(tracefile)
            # make the output file name
            outputname = filebase + '_vector_'+'.svg'
            fulloutputfile = os.path.join(outputdir, outputname)
            # make the full input path
            fulltracefile = os.path.join(tracesdir, tracefile)
            # make the trace
            self._make_trace_vector_test(fulltracefile, fulloutputfile)

