from setuptools import setup, find_packages

setup(
    name='cmtrace',
    version='0.1',
    description=
    'Script to convert xml Gantt or vector trace into an SVG or PDF drawing for a paper or presentation.',
    url='https://github.com/Model-Based-Design-Lab/cmtrace',
    author='Marc Geilen',
    author_email='m.c.w.geilen@tue.nl',
    license='MIT',
    packages=find_packages(),
    zip_safe=True,
    install_requires=[
        'pyyaml',
        'svgwrite',
        'pycairo',
    ],
    entry_points={"console_scripts": ['cmtrace = cmtrace.utils.commandline:main']},
    test_suite='nose.collector',
    tests_require=['nose'],
)
