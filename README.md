# AccessR

The AccessR tool set provides a simple set of NMTK tools for preparing an
accessibility map and conducting simple isochrone accessibility analyses from
a set of points.

This tool can be installed under the name "AccessR" in the NMTK's
NMTK_apps subfolder, with a corresponding entry in local_settings.py to
enable the application.

The tool works in three steps.

The first step takes an input polygon geographic file and rasterizes it to
establish a study area with a base level of accessibility (the units are
arbitrary).  The tool can use either feature values or a constant value to
provide the base level of impedance in each cell.  Any value used for the
baseline should be greater than zero; a zero value is treated as inaccessible.
This step generates a basic raster file called an "accessibility map".

The second step accepts a spatial layer (areas, lines or points) and overlays
those features onto an existing accessibility map. The accessibility map can
come from the first step, or from a previous iteration of this second step,
which can be conducted as many times as necessary to include
different types of facilities or barriers.  The accessibility value of each
feature (or a constant value applied to all features) is used to update
the provided accessibility map, and new accessibility map is generated; that
number should be positive, non-zero value.  Three "styles" of update are provided:
"Barriers" are areas that will be considered completely untraversable or off-limits.
Areas occupied by barriers will be considered outside the analysis area.  "Obstacles"
simply reduce the base accessibility by the accessibility value but still allow
passage.  "Facilities" increase the base accessibility.

The third step accepts an accessibility map from one of the previous steps, plus
a file of points for which isochrones are computed using the accessibility map.

*Running R*

As the name suggests, the tool uses the R Statistical Environment to perform
its computations.  R is served from the Rserve package which must be running
as a daemon. Installation is easy, see the Rserve documentation:
https://www.rforge.net/Rserve/doc.html

For accessing R from the Python harness, the pyRserve package is used.  Install
it in the NMTK virtual environment using 'pip install pyRserve', or by using
'pip install -r requirements.txt' Note that pyRserve requires numpy, which the
NMTK installs by default because it is expected most tools will need it.

If Rserve is not running when the tool processes a job, an error status will
be reported.

To start Rserve once it has been installed, see its documentation which says to
execute 'R CMD Rserve' -- an R interpreter will be launched and set running in
daemon mode.  To close Rserve cleanly, you can activate the NMTK virtual Python
environment and then use the included Python script with 'python endRserve.py'.
Note that pyRserve must be installed as a Python package to use that command 
(see requirements.txt).
