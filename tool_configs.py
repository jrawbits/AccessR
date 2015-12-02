#!/usr/bin/env python
"""
This file describes the AccessR Accessibility Raster tool for the NMTK.

As written here, it uses the "function-based" mechanism for
delivering the tool configuration.

This python file also runs standalone and will build a configuration file
from the Python dictionary contained within.  It looks at the containing
folder name and places the JSON configuration file in the templates
folder as required by the NMTK architecture.  If you pre-build the
files and put them in the right template directory, you can remove
the function and just load the config as a static JSON file.  The file
will be added to the NMTK when the system is installed, or when you
run the Django command python manage.py collectstatic.
"""

tools = ["Access0","Access1","Access2"]

# Access0 prepares a raster base Accessibility layer from a polygon area
# Access1 adds an accessibility layer from a vector (or compatible raster) file
# Access2 computes isochrones from an Accessibility layer and a point file

# If tool_configs.py contains the generateToolConfiguration function,
# that will be used preferentially to generate a Python dictionary
# containing the tool configuration.  If you want to use a file-based
# configuration (in the templates sub-folder), do not define this
# function.
def generateToolConfiguration(tool,sub_tool=None):
    '''
    Simple function-based approach to returning a tool_config
    In this case, we just return the python dictionary that would
    have been used to make tool_config.json
    '''
    if sub_tool:
        return tool_configs[sub_tool]
    else:
        return tool_configs[0]

# Access0: the Accessibility Base Layer (study area)
Access0 = {
    "info" : {
        "name" : "Accessibility: Base Layer",
        "version" : "0.1",
        "text" :
"""
<P>The Accessibility: Base Layer tool is the first step in the Accessibility tool
sequence.  It takes a spatial file of polygons representing an analysis area and
generates a raster base layer (an "accessibility map") for accessibility analysis.
That accessibility map is then used as input for the Accessibility: Overlay tool to
build up an accessibility map that can be sent to the Accessibility: Evaluation tool
to compute accessibility at specific points within the analysis area.</P>

<P>The overall AccessR tool set provides a simple set of NMTK tools for preparing an
accessibility map and conducting simple isochrone accessibility analyses from a set
of points.</P>

<P>The Access R tool set works in three steps (the tool you are currently exploring is
the <strong>FIRST step</strong>:</P>

<OL><LI>The first step (this tool) takes an input polygon geographic file and
rasterizes it to establish a study area with a base level of accessibility (the units
are arbitrary).  The tool can use either feature values or a constant value to
provide the base level of impedance in each cell.  Any value used for the baseline
should be greater than zero; a zero value is treated as inaccessible.  This step
generates a basic raster file called an "accessibility map".</LI>

<LI>The second step accepts a spatial layer (areas, lines or points) and overlays
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
passage.  "Facilities" increase the base accessibility.</LI>

<LI>The third step accepts an accessibility map from one of the previous steps, plus
a file of points for which isochrones are computed using the accessibility map.</LI>
</OL>
""",
        },
#    "documentation" : {},
    "sample" : {
        "files": [
            {
                "namespace":"rasterize",
                "checksum": "51f71bba38057fcc0944478ae8237bda7cf9118f",
                "uri": "/static/AccessR/StudyArea_Vector.zip",
                "content-type":"application/zip"
            },
        ],
        "config" : {
            "rasterize" : {
                "rastervalue" : {
                    "type" : "numeric",
                    "value": 3,
                },
            },
            "rasterization_params" : {
                "raster_x" : {
                    "type" : "numeric",
                    "value": 300,
                },
                "raster_y" : {
                    "type" : "numeric",
                    "value": 300,
                },
            },
            "studyarea_output" : {
                "studyareafile" : {
                    "type":"string",
                    "value":"StudyArea",
                },
            },
        },
    },
    "input" : [
        {
            "type" : "File",            # Elements that can be read in multiple rows from a file
            "name" : "rasterize",       # 'name' and 'namespace' are probably redundant
            "namespace" : "rasterize",
            "description" :
"""
Data file that will be used to establish Accessibility Base Map (must be polygon file)
""",
            "primary" : True,           # True if...
            "required" : True,           # If true, an actual file must be provided
            "label" : "Accessibility Base Area",
            "spatial_types" : ["POLYGON"],# require specific spatial type of Polygon
            "elements" :
                [
                    {
                        "description" : """
The value to be assigned to raster cells coinciding with the polygon feature.  May be a constant or a file property.
""",
                        "default" : 3,
                        "label" : "Raster Value",
                        "type" : "number",
                        "name" : "rastervalue"
                    },
                ],
            },
            {
            "type" : "ConfigurationPage",
            "name" : "rasterization_params",
            "namespace" : "rasterization_params",
            "description" :
"""
Parameters that control how rasterization of the base map will be performed.
These parameters will be used by subsequent Accessibility steps (Overlay and Evaluation).
""",
            "label" : "Rasterization Parameters",
            "expanded" : True,
            "elements" : [
              {
                  "description" : "Number of X (East-West) cells to construct",
                  "default" : 300,
                  "required" : True,
                  "label" : "X Cells",
                  "type" : "numeric",
                  "name" : "raster_x"
              },
              {
                  "description" : "Number of Y (North-South) cells to construct",
                  "default" : 300,
                  "required" : True,
                  "label" : "Y Cells",
                  "type" : "numeric",
                  "name" : "raster_y"
              },
              ],
            },
        ],
    "output" : [
            {
              "type":"ConfigurationPage",
              "name":"studyarea_output",
              "namespace":"studyarea_output",
              "label":"Base Map Output",
              "description":"""
Set a file name for the base layer.
""",
              "elements":[
                {
            "description":"""
Change the default name for the base layer.
""",
                  "default":"StudyArea",
                  "required":True,
                  "label":"Base Map Name",
                  "type":"string",
                  "name":"studyareafile",
                },
              ],
            },
        ],
    }

# Access1 : Overlay accessibility features on an accessibility base layer
Access1 = {
    "info" : {
        "name" : "Accessibility: Overlay",
        "version" : "0.1",
        "text" :
"""
<P>The Accessibility: Overlay tool is the second step in the Accessibility tool set.
It adds accessibility barriers or facilities to an accessibility generated by the
Accessiblity: Base Layer tool, or from a previous iteration of this Accessibility:
Overlay tool.  The accessibility features are overlaid from a spatial data overlay
file representing characteristics of barriers or features that modify the base level
of accessibility.  The tool computes the increase or decrease in accessibility due to
the overlay features.</P>

<P>The overall AccessR tool set provides a simple set of NMTK tools for preparing an
accessibility map and conducting simple isochrone accessibility analyses from a set
of points.</P>

<P>The Access R tool set works in three steps (the tool you are currently exploring is
the <strong>SECOND step</strong>:</P>

<OL><LI>The first step takes an input polygon geographic file and rasterizes it to
establish a study area with a base level of accessibility (the units are
arbitrary).  The tool can use either feature values or a constant value to
provide the base level of impedance in each cell.  Any value used for the
baseline should be greater than zero; a zero value is treated as inaccessible.
This step generates a basic raster file called an "accessibility map".</LI>

<LI>The second step (this tool) accepts a spatial layer (areas, lines or points) and
overlays those features onto an existing accessibility map. The accessibility map can
come from the first step, or from a previous iteration of this second step, which can
be conducted as many times as necessary to include different types of facilities or
barriers.  The accessibility value of each feature (or a constant value applied to
all features) is used to update the provided accessibility map, and new accessibility
map is generated; that number should be positive, non-zero value.  Three "styles" of
update are provided: "Barriers" are areas that will be considered completely
untraversable or off-limits.  Areas occupied by barriers will be considered outside
the analysis area.  "Obstacles" simply reduce the base accessibility by the
accessibility value but still allow passage.  "Facilities" increase the base
accessibility.</LI>

<LI>The third step accepts an accessibility map from one of the previous steps, plus
a file of points for which isochrones are computed using the accessibility map.</LI>
</OL>
""",
        },
#    "documentation" : {},
    "sample" : {
        "files": [
            {
                "namespace":"accessibility",
                "checksum": "7d3a43a90492a8931f59f081fb6199769b8ef0a0",
                "uri": "/static/AccessR/StudyArea_Raster.tif",
                "content-type":"image/tif"
            },
            {
                "namespace":"overlay",
                "checksum": "c1260eb7d85616321943730a4af22c4972cf7ee1",
                "uri": "/static/AccessR/StudyArea_Roads.zip",
                "content-type":"application/zip"
            },
        ],
        "config" : {
            "overlay": {
                "accessibility" : {
                    "type" : "numeric",
                    "value": 6,
                },
            },
            "overlay_type": {
                "overlay_style" : {
                    "type" : "string",
                    "value": "Facility",
                },
            },
            "accessibility_output" : {
                "accessibilityfile" : {
                    "type":"string",
                    "value":"Accessibility",
                },
            },
        },
    },
    "input" : [
        {
            "type" : "File",
            "name" : "accessibility",     # 'name' and 'namespace' are probably redundant
            "namespace" : "accessibility",
            "description" :
"""
This file is a raster generated by the Accessibility: Base Map tool or resulting from an earlier
applicaton of this Accessbility: Overlay tool.
""",
            "primary" : False,            # True if...
            "required" : True,           # If true, an actual file must be provided
            "label" : "Study area for rasterization",
            # This file is essentially a "blob" from the standpoint of the toolkit framework
            # It has no "elements"
            # The tool determines whether the file is a suitable type internally and will
            # report a status error if it is not.
        },
        {
            "type" : "File",
            "name" : "overlay",       # 'name' and 'namespace' are probably redundant
            "namespace" : "overlay",
            "description" :
"""
Spatial data file that will be used to overlay the Accessibility base area
""",
            "primary" : False,            # True if...
            "required" : True,           # If true, an actual file must be provided
            "label" : "Data used for rasterization",
            "spatial_types" : ["POLYGON","POINT","LINE"], # expect specific spatial types
            "elements" :
                [
                    {
                        "description" : """
The value to be assigned to raster cells coinciding with each feature.  May be a constant or a file property.
""",
                        "default" : 6,
                        "label" : "Accessibility",
                        "type" : "number",
                        "name" : "accessibility"
                    },
                ],
            },
            {
              "type":"ConfigurationPage",
              "name":"overlay_type",
              "namespace":"overlay_type",
              "label":"Overlay Type",
              "description":"""
Set the Overlay style for this Accessibility layer.
""",
              "elements":[
                # Overlay style (choices):
                #    Absolute Barrier
                #    Obstacle
                #    Facility
                  {
                    "description":"""
Overlay style says whether to treat features in this layer as Barriers (completely impassable), as Obstacles that
reduce accessibility, or as Facilities that increase accessibility.  The Accessibility layer is modified accordingly.
""",
                    "default":"Facility",
                    "required":True,
                    "label":"Overlay Style",
                    "type":"string",
                    "choices":["Barrier","Obstacle","Facility"],
                    "name":"overlay_style",
                  },
              ],
          }.
        ],
    "output" : [
            {
              "type":"ConfigurationPage",
              "name":"accessibility_output",
              "namespace":"accessibility_output",
              "label":"Accessibility Output",
              "description":"""
Set a file name for the Accessibility layer.
""",
              "elements":[
                {
            "description":"""
Change the default name for the Accessibility layer.
""",
                  "default":"Accessibility",
                  "required":True,
                  "label":"Accessibility File Name",
                  "type":"string",
                  "name":"accessibilityfile",
                },
              ],
            },
        ],
    }

# Access2 : Compute isochrones on an Accessibilty layer from a set of points
Access2 = {
    "info" : {
        "name" : "Accessibility: Evaluation",
        "version" : "0.1",
        "text" :
"""

<P>This Accessibility: Evaluation tool is the third step in the Accessibility tool
set.  It takes an accessibility mapy, typically generated by Accessibility: Overlay,
and evaluates access to a set of points provided in a spatial points layer.  The
result is returned as a set of raster maps showing "isochrones" (cumulative travel
time) to each of the points that are provided.  In addition to an individual raster
band for each provided point, a cumulative raster for all points is returned, which
can be used to provide an estimate of accessibility to any of the points.</P>

<P>The overall AccessR tool set provides a simple set of NMTK tools for preparing an
accessibility map and conducting simple isochrone accessibility analyses from a set
of points.</P>

<P>The Access R tool set works in three steps (the tool you are currently exploring is
the <strong>THIRD step</strong>:</P>

<OL><LI>The first step takes an input polygon geographic file and rasterizes it to
establish a study area with a base level of accessibility (the units are
arbitrary).  The tool can use either feature values or a constant value to
provide the base level of impedance in each cell.  Any value used for the
baseline should be greater than zero; a zero value is treated as inaccessible.
This step generates a basic raster file called an "accessibility map".</LI>

<LI>The second step accepts a spatial layer (areas, lines or points) and
overlays those features onto an existing accessibility map. The accessibility map can
come from the first step, or from a previous iteration of this second step, which can
be conducted as many times as necessary to include different types of facilities or
barriers.  The accessibility value of each feature (or a constant value applied to
all features) is used to update the provided accessibility map, and new accessibility
map is generated; that number should be positive, non-zero value.  Three "styles" of
update are provided: "Barriers" are areas that will be considered completely
untraversable or off-limits.  Areas occupied by barriers will be considered outside
the analysis area.  "Obstacles" simply reduce the base accessibility by the
accessibility value but still allow passage.  "Facilities" increase the base
accessibility.</LI>

<LI>The third step (this tool) accepts an accessibility map from one of the previous steps, plus
a file of points for which isochrones are computed using the accessibility map.</LI>
</OL>
""",
        },
#    "documentation" : {},
    "sample" : {
        "files": [
            {
                "namespace":"accessibility",
                "checksum": "a1b1a7d6e736889413626f2912920346f9fbe174",
                "uri": "/static/AccessR/AccessibilityDemo.tif",
                "content-type":"image/tif"
            },
            {
                "namespace":"points",
                "checksum": "b1c107451b61054f22fe3a0d4bad0aab662a3158",
                "uri": "/static/AccessR/Points.zip",
                "content-type":"application/zip"
            },
        ],
        "config" : {
            "overlay": {
                "accessibility" : {
                    "type" : "numeric",
                    "value": 6,
                },
            },
            "overlay_type": {
                "overlay_style" : {
                    "type" : "string",
                    "value": "Facility",
                },
            },
            "accessibility_output" : {
                "accessibilityfile" : {
                    "type":"string",
                    "value":"Accessibility",
                },
            },
        },
    },
    "input" : [
        {
            "type" : "File",
            "name" : "accessibility",     # 'name' and 'namespace' are probably redundant
            "namespace" : "accessibility",
            "description" :
"""
This file is a raster generated by the Accessibility: Base Map tool or by the Accessbility: Overlay tool.
""",
            "primary" : False,            # True if...
            "required" : False,           # If true, an actual file must be provided
            "label" : "Accessibility layer to evaluate",
            # This file is essentially a "blob" from the standpoint of the toolkit framework
            # It has no "elements"
        },
        {
            "type" : "File",            # Elements that can be read in multiple rows from a file
            "name" : "points",       # 'name' and 'namespace' are probably redundant
            "namespace" : "points",
            "description" :
"""
Spatial data file at which to evaluate Accessibility
""",
            "primary" : False,            # True if...
            "required" : False,           # If true, an actual file must be provided
            "label" : "Points at which to evaluate accessibility",
            "spatial_types" : ["POINT"], # require specific spatial types
            },
        ],
    "output" : [
            {
              "type":"ConfigurationPage",
              "name":"isochrone_output",
              "namespace":"isochrone_output",
              "label":"Accessibility Output",
              "description":"""
Set a file name for the Accessibility layer.
""",
              "elements":[
                {
            "description":"""
Change the default name for the Accessibility layer.
""",
                  "default":"isochrone",
                  "required":True,
                  "label":"Accessibility File Name",
                  "type":"string",
                  "name":"isochronefile",
                },
              ],
            },
        ],
    }

tool_configs = [ Access0, Access1, Access2 ]

# Here's a simple function that you can use to dump the tool
# configuration file into a JSON file in the templates folder.
# Run this file as a standalone python script.
# Note that if you define the function generateToolConfiguration,
# then that function will be called to deliver the tool configuration
# to the NMTK, and the file-based configuration will not be used.
if __name__ == "__main__":
    import json
    if not tools:
        tools = ["tool_config"]
    for tool_name in tools:
        print "Configurating tool %s"%(tool_name,)
        tool_data = eval(tool_name)
        js = json.dumps(tool_data,indent=2, separators=(',',':'))
        print js
#        f = file("templates/Configurator/%s.json"%(tool_name,),"w")
#        f.write(js)
#        f.close()
