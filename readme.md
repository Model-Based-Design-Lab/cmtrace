# CM Trace

A Python tool to transform small traces, e.g., from SDF3 or CMLib into visually attractive Gantt charts or vector charts.

## How to Get It

The `cmtrace` package can de cloned from [GitHub](https://github.com/Model-Based-Design-Lab/cmtrace)

## How to Use It

### Installing

In a proper shell environment type:

``` sh
python3 -m pip install cmtrace
```

### Creating a trace

Use SDF3 to make a trace of the graph. E.g., for an FSM-SADF graph `fsmsadfgraph.xml`:

```
sdf3analyze-fsmsadf --algo trace --graph fsmsadfgraph.xml --seq a,b,b,a --traceFormat XML --traceFile trace.xml
```

This produces a trace file `trace.xml`. With this trace file, make an SVG graph as follows:

``` sh
cmtrace trace.xml gantt.svg
```

This uses default settings. Settings can be configured in a YAML file and used as follows.

``` sh
cmtrace -s settings.yaml trace.xml gantt.svg
```

More information about the settings can be found below.

TODO: for a vector trace?

### Settings

```
graphics:
    # width of the strokes of the firing rectangles
    firing-stroke-width: 0
    # firing-color-mode is one of the following: by-actor, by-scenario, by-token, by-iteration
    firing-color-mode: by-actor
    # alternate light and darker versions of the color for subsequent firings, especially useful when stroke width is 0
    alternate-color: true

layout:
    trace-length: 12
    font-size: 10
    trace-width: 2.5
    horizontal-scale: 5
    unit: 1.0
    # define how the numbers at the ticks on the horizontal axis are formatted in python format notation
    time-stamp-format: ":.2f"
    event-radius: 0.35

structure:
    # rows define the rows shown in the Gantt chart, referring to actors or actor groups defined in structure:groups
    rows: [A, B, C]
    # define groups of actors that can be referred on the row layout and in the color map
    # format:
    # RowName:  [ list of actor names ]
    # actor names are fully qualified with their scenario: scenario@actor
    # as a special case, an actor name in the list can be replaced by a list of two lists, a list of scenarios and a list of actor names
    # in that case the full Cartesian product, all combinations of scenarios and actors are included (see the examples below)
    groups: 
        A: [ a@A, b@A ]
        B: [
            [
                [a, b],
                [B]
            ]
        ]
        C: [
            [
                [a, b],
                [C]
            ]
        ]


colors:
    palette: [
        [255, 255, 0],
        [0, 255, 255],
        [255, 0, 255],
        [255, 0, 0],
        [0, 255, 0],
        [0, 0, 255]
    ]
    # map individual actor names, or groups of actors as defined in the structure section to color indices
    color-map: {
        A: 0,
        B: 1,
        C: 2
    }
    # # map scenario names to color indices, used in by-scenario color mapping
    # color-map: {
    #     ss: 0,
    #     sl: 1,
    #     ls: 2,
    #     ll: 3,
    #     m: 4
    # }
```

## License

The package is licensed under the MIT license.
