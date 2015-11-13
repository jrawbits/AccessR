# AccessTool

The AccessTool provides a simple NMTK tool for preparing an accessibility
raster file and conducting simple isochrone accessibility analyses from
a set of points.

This tool can be installed under the name "AccessR" in the NMTK's
NMTK_apps subfolder, with a corresponding entry in local_settings.py to
enable the application.

The tool takes an input polygon geographic file and rasterizes it, using
either feature values or a constant value to provide the base level
of impedance in each cell.  Any value used for the baseline should be
greater than zero; a zero value is treated as inaccessible.

In addition, it accepts one file of "areas" (optional) and one file of
"lines" (roads) which modify the base level of accesibility.  These values
may be positive, negative or zero.  Positive values are added to the
base accessibility, negative values are substracted, and zero values
are marked as zero.  Any resulting value less than zero will be treated
as zero.  If no area or road file is provided, the base accessibility
map is not altered.

Finally, the tool accepts a file of points (optional) for which isochrones
are computed using the accessibility surface.  If no points are provided
then a point at the centroid of the study area is used.  If that cell
is zero accessibility, however, no isochrone will be produced.

*Running R*
R is served from the Rserve package which must be running as a daemon.
Installation is easy, see the Rserve documentation:
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
