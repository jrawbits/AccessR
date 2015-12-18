# AccessR

The AccessR tool set provides a simple set of NMTK tools for preparing an
accessibility map and conducting simple isochrone accessibility analyses
from a set of points.

This tool can be installed under the name "AccessR" in the NMTK's
NMTK_apps subfolder, with a corresponding entry in local_settings.py to
enable the application.  There are system prerequisites detailed below
in in the Installation section.

The tool works in three steps.

The first step takes an input polygon geographic file and rasterizes
it to establish a study area with a base level of accessibility (the
units are arbitrary).  The tool can use either feature values or a
constant value to provide the base level of impedance in each cell.
Any value used for the baseline should be greater than zero; a zero
value is treated as inaccessible.  This step generates a basic raster
file called an "accessibility map".

The second step accepts a spatial layer (areas, lines or points)
and overlays those features onto an existing accessibility map. The
accessibility map can come from the first step, or from a previous
iteration of this second step, which can be conducted as many times
as necessary to include different types of facilities or barriers.
The accessibility value of each feature (or a constant value applied to
all features) is used to update the provided accessibility map, and new
accessibility map is generated; that number should be positive, non-zero
value.  Three "styles" of update are provided: "Barriers" are areas that
will be considered completely untraversable or off-limits.  Areas occupied
by barriers will be considered outside the analysis area.  "Obstacles"
simply reduce the base accessibility by the accessibility value but
still allow passage.  "Facilities" increase the base accessibility.

The third step accepts an accessibility map from one of the previous
steps, plus a file of points for which isochrones are computed using
the accessibility map.

*Installation*

As the name suggests, the tool uses the R Statistical Environment to
perform its computations.  So you'll need to install a recent version
of R from one of the CRAM mirrors (see http://cran.r-project.org).

You will need several R packagesi (sp,raster,rgdal,gdistance).  It is
most convenient to install these from within "sudo R" (the R text GUI
running with admin privileges) using the R function install.packages:

install.packages(c("sp","raster","rgdal","gdistance"))

R is accessed through the Rserve package. Installation is easy, see the
Rserve documentation: https://www.rforge.net/Rserve/doc.html

For accessing Rserve from the Python environment, the pyRserve package
is used.  Install it in the NMTK virtual environment using 'pip install
pyRserve', or by using 'pip install -r requirements.txt' Note that
pyRserve requires numpy, which the base NMTK installs.

The tool uses "out-of-band" (oob) messages to generate status updates,
so you should start Rserve prior to running any of the tools using the
included configuration file oob.conf, like this:

R CMD Rserve --RS-conf oob.conf

To close Rserve cleanly, you can activate the NMTK virtual Python
environment and then use the included Python script

python endRserve.py'.

Finally, the included "bump.sh" script will set everything going once
you have all the pieces installed and have added` "AccessR" to the NMTK's
list of tools in local_settings.py.
