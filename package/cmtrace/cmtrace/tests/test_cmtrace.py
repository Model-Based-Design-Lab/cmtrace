'''
Module Tests
'''

from unittest import TestCase

import os

from cmtrace.graphics.tracesettings import TraceSettings
from cmtrace.libtracetosvg import create_gantt_fig, create_vector_fig



class TestCmtrace(TestCase):
    '''
    Module Tests Class
    '''

    def _make_trace_test(self, trace_file, outfile):
        """ make a gantt chart named outfile, from trace_file with default settings """
        settings = TraceSettings()
        create_gantt_fig(trace_file, outfile, settings=settings)

    def _make_trace_vector_test(self, trace_file, outfile):
        """ make a vector trace chart named outfile, from trace_file with default settings """
        settings = TraceSettings()
        create_vector_fig(trace_file, outfile, settings=settings)

    def test_default_trace(self):
        """Create a Gantt chart for a simple example trace."""
        # Create traces for simple example examples/trace.xml
        settings = TraceSettings()
        example_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'example')
        trace_file = os.path.join(example_dir, 'trace.xml')

        # Create Gantt chart with default settings
        output_file = os.path.join(example_dir, 'trace_default.svg')
        create_gantt_fig(trace_file, output_file, settings=settings)

        # Create a Gantt chart with settings from specification
        output_file = os.path.join(example_dir, 'trace_settings.svg')
        settings_file = os.path.join(example_dir, 'settings.yaml')
        settings.parse_settings(settings_file)
        create_gantt_fig(trace_file, output_file, settings=settings)

    def test_default_vector_trace(self):
        """Create a Gantt chart for a simple example trace."""
        # TODO: be done.
        self.assertTrue(True)

    def test_example_traces(self):
        """ make charts for the traces in example/traces """

        # get the example directory
        example_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'example')
        # get the output directory
        output_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'output')
        # get the directory with Gantt input traces
        traces_dir = os.path.join(example_dir, 'traces', 'gantt')

        # for each trace file
        for trace_file in os.listdir(traces_dir):
            # get the base filename without extension
            file_base, _ = os.path.splitext(trace_file)
            # make the output file name
            output_name = file_base + '.svg'
            full_output_file = os.path.join(output_dir, output_name)
            # make the full input path
            full_trace_file = os.path.join(traces_dir, trace_file)
            # make the trace
            self._make_trace_test(full_trace_file, full_output_file)

        # get the directory with vector input traces
        traces_dir = os.path.join(example_dir, 'traces', 'vector')
        # for each trace file
        for trace_file in os.listdir(traces_dir):
            # get the base filename without extension
            file_base, _ = os.path.splitext(trace_file)
            # make the output file name
            output_name = file_base + '_vector_'+'.svg'
            full_output_file = os.path.join(output_dir, output_name)
            # make the full input path
            full_trace_file = os.path.join(traces_dir, trace_file)
            # make the trace
            self._make_trace_vector_test(full_trace_file, full_output_file)
