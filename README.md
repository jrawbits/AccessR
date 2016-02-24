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
of R from one of the CRAN mirrors (see http://cran.r-project.org).
For Ubuntu, you can look here: https://cran.r-project.org/bin/linux/ubuntu/

On Ubuntu 14.04 ("trusty") you can do the following to connect a
R repository (replacing "<my.favorite.cran.mirror>" with one of the
mirrors you can find at https://cran.r-project.org/mirrors.html:

    sudo echo "deb https://<my.favorite.cran.mirror>/bin/linux/ubuntu trusty/" > /etc/apt/sources.list.d/cran.list
    
The repository is secured by a specific signature key.  You need to
install the key by doing this:

    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E084DAB9

Then you can run these commands to install R itself, plus the development
environment for compiliing packages from source:

    sudo apt-get update # to read the repository
    sudo apt-get install r-base r-base-dev

You will need several R packages (specifically: sp, raster, rgdal,
gdistance).  You will also need Rserve to allow the NMTK environment
to run R commands.  Installation of Rserve is easy, see the Rserve
documentation: https://www.rforge.net/Rserve/doc.html

It is most convenient to install these packages from within R
using the  function 'install.packages':

    sudo R  # run R as an administrator
    install.packages(c("sp","raster","rgdal","gdistance","Rserve"))

For accessing Rserve from the Python environment, the pyRserve package
is used.  Activate the NMTK python environment from the NMTK root folder,
then install pyRserve using 'pip install -r requirements.txt' Note that
pyRserve requires numpy, which the base NMTK installs.  The complete
sequence for installing pyRserve:

    source ../../venv/bin/activate
    pip install -r requirements.txt

The tool uses "out-of-band" (oob) messages to generate status updates,
so you should start Rserve using the included configuration file oob.conf
prior to running any of the tools.  This is the start command:

    R CMD Rserve --RS-conf oob.conf

To close Rserve cleanly, you can activate the NMTK virtual Python
environment and then use the included Python script

    python endRserve.py

Finally, the included "deploy.sh" script will set everything going once
you have all the pieces installed and have added` "AccessR" to the NMTK's
list of tools in local_settings.py.  It calls the root NMTK deployment script
to reload the NMTK environment and it also starts Rserve.  Like the root NMTK
deployment script, it supports an option "-c" which will clear log files.

    bash deploy.sh  # -c optional to clear log files
