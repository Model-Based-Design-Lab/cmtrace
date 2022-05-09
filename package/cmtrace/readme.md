* If you want go generate PDF output, you need to install CairoSVG

See:
http://weasyprint.readthedocs.io/en/latest/install.html



* The tools to include LaTeX in your SVG image have the following requirement:

usage:

generate a trace as follows:
sdf3analyze-fsmsadf --algo trace --graph fsmsadfgraph.xml --seq a,b,b,a --traceFormat XML --traceFile trace.xml

command line:
cmtrace -s settings.yaml trace.xml gantt.svg





install and use on Linux:

check out the repo:
git clone ....

...

if necessary, install pip
sudo apt-get install python3-pip

inside the package/cmtrace folder
python3 -m pip install .

it should install the packages: pyyaml, pyparsing, svgwrite and cmtrace

Now you can use the command line:


need pdflatex and ... dvi to svg...
to add LaTeX
sudo apt install texlive-latexl-base


cairosvg is required for conversion to pdf

- install the cairo, python3-dev and libffi-dev packages 
sudo apt install libcairo2-dev
sudo apt install python3-dev
sudo apt install libffi-dev
python3 -m pip install cairosvg

(the script still says cairosvg is not installed. check why)
