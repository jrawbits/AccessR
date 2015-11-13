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

tools = [] # A single configuration contained here

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
    return tool_config

tool_config = {
    "info" : {
        "name" : "Accessibility Rasters",
        "text" : """
<p>This tool performs simple raster-based accessibility analysis.</p>
<p>The input files consist of rasterization parameters (essentially the
resolution on N-S and E-W directions, plus four geospatial files.</p>
<p>The tool returns an accessibility surface as a geoTIFF file, and a set
of isochrones showing accessibility to point locations provided</p>
<p>The input structure is the folloowing:</P>
<ol>
<li>Rasterization parameters (X- and Y-Resolutions)</li>
<li>A polygon file for the study area (required), with one property:
    <ul>
    <li>Either a feature attribute or a constant value to set default accessibility</li>
    </ul>
</li>
<li>A second polygon file for facility areas (optional):
    <ul>
    <li>To ignore this file, use the supplied "NoFeatures" sample file</li>
    <li>A property that identifies either a feature attribute or a constant value as an accessibility increment</li>
    <li>Positive increments are added to the default accessibility</li>
    <li>Negative increments are subtracted from the default accessibility</li>
    </ul>
</li>
<li>A line file for road-like paths (optional)
    <ul>
    <li>To ignore this file, use the supplied "NoFeatures" sample file</li>
    <li>A property that identifies either a feature attribute or a constant value as an accessibility increment</li>
    <li>Positive increments are added to the default accessibility</li>
    <li>Negative increments are subtracted from the default accessibility</li>
    </ul>
<li>A point file of locations from which to compute isochrones:
    <ul>
    <li>To ignore this file, use the supplied "NoFeatures" sample file</li>
    <li>If ignored, no isochrones will be computed</li>
    <li>Otherwise, an isochrone will be computed for each point</li>
    <li>A maximum of five isochrones will be computed</li>
    </ul>
</li>
</ol>

<strong>Return values</strong>

<ol>
<li>Return a single accumulated accessibility surface as a geoTIFF
    <ul>
    <li>The base area</li>
    <li>Plus the additional polygons</li>
    <li>Plus the additional roads</li>
    </ul>
</li>
<li>Return the isochrones in a single geoTIFF file
    <ul>
    <li>The first band is the multi-isochrone (distance to nearest point)</li>
    <li>The second and subsequent bands are for each individual point feature</li>
    </ul>
</li>
</ol>
""",
        "version" : "1.0"
    },

# Future documentation will include the submitted TRB paper/presentation from 2012.
#     "documentation" : {
#         "links" : [
#               {
#                 "url":"http://nmtk.jeremyraw.com/Configurator/config",
#                 "title":"See the Configurator's raw configuration file"
#               },
#               {
#                 "url":"http://github.com/jrawbits/Configurator",
#                 "title":"Visit the Configurator source code on Github"
#               },
#         ],
#         "docs" : [
#             {
#                 "url" : "ToolSpec_2015-07-31.docx",
#                 "mimetype" : "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
#                 "name" : "Tool Configuration Specification (.docx, 2015-07-31)",
#             }
#         ],
#     },

# The sample section should be developed after the input and output
# sections. 
    "sample" : {
        "files": [
            # The "files" portion lists the files to use for each File namespace in
            # the "input" section. If the file is not required and not used in the
            # sample job, then it may be omitted here (then the corresponding config
            # entry will either have constant values, where the type is explicit
            # rather than "property", or it will also be omitted).  The tool itself
            # should be written to handle the absence of optional sections and
            # elements.  Checksums are generated by the Linux utility sha1sum
            # (see checksums.txt in the static section of the Configurator web
            # space).
            {
                "namespace":"computation",
                "checksum": "02d53b787eaff4a6e34b44a420541813e54e3261",
                "uri": "/static/Configurator/Some_Numbers.csv",
                "content-type":"text/csv"
            },
            {
                "namespace":"rasterize",
                "checksum": "e3a7cd4720f9c88cbc84a79b655e033df66bae6b",
                "uri": "/static/Configurator/Vector_Test.geojson",
                "content-type":"application/json"
            }
        ],
        "config" : {
            # The "config" section provides values for all "required" (and
            # optionally, "optional") elements in each namespace.  It is very similar
            # in structure to what is passed to the tool when a job is submitted.
            # "property" types only apply to a File namespace, and are strings that
            # contain the name of a field in the input file for that namespace that
            # should be used to supply that value.  Other types ("numeric",
            # "boolean", or "string" are currently supported) have corresponding
            # values: note that because of JSON limitations, "boolean" types are
            # represented as numeric values of 1 (true) or 0 (false).
            "rasterize": {
                "rastervalue" : {
                    "type" : "property",
                    "value": "TAZ",
                },
            },
            "rasterization_params": {
                "dorasterize" : {
                    "type" : "boolean",
                    "value": 1,
                },
                "raster_x" : {
                    "type" : "numeric",
                    "value": 300,
                },
                "raster_y" : {
                    "type" : "numeric",
                    "value": 300,
                },
            },
            "imaging_params" : {
                "imagevector" : {
                    "type" : "boolean",
                    "value": 0,
                },
                "imageraster" : {
                    "type" : "boolean",
                    "value": 1,
                },
            },
            "rasterization_output" : {
                "return_raster" : {
                    "type" : "string",
                    "value": "geoTIFF",
                },
                "raster_basename" : {
                    "type" : "string",
                    "value": "raster",
                },
                "return_vector" : {
                    "type" : "boolean",
                    "value": 0,
                },
            },
            "image_output" : {
                "image_format" : {
                    "type" : "string",
                    "value": "PNG",
                },
            },
        },
    },
    "input" : [
        {
            "type" : "ConfigurationPage",  # Elements that are provided as a single instance (global)
            "name" : "rasterization_params",
            "namespace" : "rasterization_params",
            "description" :
"""
Parameters that control how rasterization will be performed.
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
        {
            "type" : "ConfigurationPage",  # Elements that are provided as a single instance (global)
            "name" : "imaging_params",
            "namespace" : "imaging_params",
            "description" : """
                    Parameters that control whether images of the rasters will be generated.
                    """,
            "label" : "Imaging Parameters",
            "expanded" : True,
            "elements" : [
              {
                  "description" : """
                    If true, make an image of the input file that will be rasterized.
                    If this is checked but no rasterization input is provided,
                    a default shapefile will be imaged.
                    """,
                  "default" : 0,
                  "required" : True,
                  "label" : "Image Input",
                  "type" : "boolean",
                  "name" : "imagevector"
              },
              {
                  "description" : """
                    If true, make an image of the rasterized file.
                    If this is checked but no rasterization was attempted (due to missing input
                    or not requested), a default raster will be imaged.
                    """,
                  "default" : 0,
                  "required" : True,
                  "label" : "Image Raster",
                  "type" : "boolean",
                  "name" : "imageraster"
              },
            ],
        }
    ], 
    "output" : [
      {
        "type":"ConfigurationPage",
        "name":"rasterization_output",
        "namespace":"rasterization_output",
        "label":"Rasterization Outputs",
        "description":"""
You can force certain rasterization output to occur, regardless of whether you actually attempted rasterization.
The boolean parameters below will control what is returned.
""",
        "elements":[
          {
            "description":"""
Return a raw raster file.  The tool will return either the raster resulting from rasterization,
or if rasterization was not attempted, then a pre-constructed geographic raster.  If you choose
'None', then no raster will be returned, even if rasterization was attempted.
""",
            "default":"geoTIFF",
            "required":True,
            "label":"Return Raster",
            "type":"string",
            "choices":["geoTIFF","Erdas Imagine Images (.img)","RData","None"],
            "name":"return_raster",
          },
          {
            "description":"""
If you choose to return a raster, use this setting to change the default base name for the file.
""",
            "default":"raster",
            "required":True,
            "label":"Raster Base Name",
            "type":"string",
            "name":"raster_basename",
          },
          {
            "description":"""
Mirror (return) the input vector file used for rasterization as a geoJSON file.  If no rasterization input file
was provided, return a pre-determined sample geographic vector file (the same that will be used if rasterization
is requested but no input is provided).
""",
            "default":0,
            "required":True,
            "label":"Mirror Input Vector",
            "type":"boolean",
            "name":"return_vector",
          },
        ],
      },
      {
        "type":"ConfigurationPage",
        "name":"image_output",
        "namespace":"image_output",
        "label":"Image Output",
        "description":"""
If you requested images, you can set the format that will be returned here from a couple of supported types (plus
one unsupported type, PDF, that can be downloaded but not viewed).
""",
        "elements":[
          {
            "description":"""
Select the output format for the image versions of vectors or rasters that you may have requested.  All images
will be generated in the same format.
""",
            "default":"PNG",
            "choices" : ["PNG","JPG","PDF (Download Only)"],
            "required":True,
            "label":"Image Format",
            "type":"string",
            "name":"imageformat"
          },
        ],
      },
    ],
}

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
