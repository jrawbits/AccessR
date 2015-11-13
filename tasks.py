# At a minimum, you'll want to import the following items to
# communicate with the NMTK.
from celery.task import task
import datetime

# For this specific tool, we import the following helpers
from django.conf import settings
import confighelpers as Config
import decimal
import os
import pyRserve

import csv
import cStringIO as StringIO

# This contains necessary metadata about supported output formats
ImageFormatTable = {
    "PDF" : { "R-device" : "pdf",  "mimetype" : "application/pdf", "extension" : "pdf"},
    "PNG" : { "R-device" : "png",  "mimetype" : "image/png",       "extension" : "png"},
    "JPG" : { "R-device" : "jpeg", "mimetype" : "image/jpeg",      "extension" : "jpg"},
    }

# Raster Format Table needs to provide:
#   "File": The base file system name for the generated file (with extension); it will be appended
#           to a temporary folder path unique for this application
#   "Load": An R function definition template using % expansion for the base file name to load
#           a raster dataset from a file in this format,
#   "Save": An R function definition template using % expansion for the base file name to save the
#           raster dataset to a file in this format
RasterFormatTable = {
    "geoTIFF" :                     { "extension" : ".tif",
                                      "mimetype" : "image/tiff",
                                      "save" : "savefunc<-function(obj){writeRaster(obj,filename='%s',format='GTiff',overwrite=TRUE)}",
                                      "load" : "loadfunc<-function(){raster('%s')}" },
    "Erdas Imagine Images (.img)" : { "extension" : ".img",
                                      "mimetype" : "application/octet-stream",
                                      "save" : "savefunc<-function(obj){writeRaster(obj,filename='%s',format='HFA',overwrite=TRUE)}",
                                      "load" : "loadfunc<-function(){raster('%s')}" },
    "RData" :                       { "extension" : ".rds",
                                      "mimetype" : "application/octet-stream",
                                      "save" : "savefunc<-function(obj){saveRDS(obj,'%s')}",
                                      "load" : "loadfunc<-function(){con<-gzfile('%s'); obj<-readRDS(con); close(con); obj}" },
    }


@task(ignore_result=False)
def performModel(input_files,
                 tool_config,
                 client,
                 subtool_name=False):
    '''
    input_files is the set of data to analyze from the NMTK server
    tool_config is the "header" part of the input
    client is an object of type NMTK_apps.helpers.server_api.NMTKClient
    subtool_name is provided if the tool manages multiple configurations
    '''
    logger=performModel.get_logger()
    logger.debug("input_files: %s"%(input_files,))
    logger.debug("tool_config\n%s\n"%(tool_config,))

    # Use exception handling to generate "error" resulta -- everything that
    # doesn't generate good results should throw an exception Use the extra
    # 'with' syntax to ensure temporary files are promptly cleaned up after tool
    # execution.  With luck, the tool server will also do periodic garbage
    # collection on tools that don't pick up after themselves.

    # Prepare a connection to R
    R = None

    with Config.Job(input_files,tool_config) as job:
        
        try:
            # Initialize the job setup (cant do in __init__ as we would need to
            # try too hard)
            job.setup()

            # Set up a master directory of parameters
            parameters = {}
            compute = parameters["compute"] = {}
            raster = parameters["raster"] = {}
            image = parameters["image"] = {}

            ########################################
            # Computation (Python/R)
            compute_factors = job.getParameters('computation_params')
            logger.debug(compute_factors)

            #   Determine specific computational engines to use, if any
            computetype    = compute["type"] = compute_factors.get('computetype',"None")

            #   Notify the user via a status update
            if computetype != 'None':
                compute_R      = compute["with_R"] = computetype in ['R','Both']
                compute_Python = compute["with_Python"] = computetype in ['Python','Both']

                if compute_R or compute_Python:
                    computemsg = "Computation will occur using"
                    if compute_R:
                        computemsg += " R"
                        if compute_Python:
                            computemsg += " and"
                    if compute_Python:
                        computemsg += " Python"
                else:
                    computemsg = "Computation will not occur"

                #   Determine parameter; default is to square it same as /tool_config
                compute["power"] = compute_factors.get('raisetopower',2)

                #   Determine input (file/constant data) / we'll iterate later
                compute_file = job.getFeatures('computation')

                #   Determine what to return (result file)
                compute_output = job.getParameters('computation_output')
                compute["PythonName"] = compute_output.get('python_result','PowerOfPython')
                compute["RName"] = compute_output.get('r_result','PowerOfR')
            else:
                computemsg = "Computation was not requested."

            client.updateStatus(computemsg)

            ########################################
            # Rasterization (desired, input file provided, default to use instead)
            raster_factors = job.getParameters('rasterization_params')

            # Set up the default files
            default_vector_name = os.path.join(settings.STATIC_ROOT, "Configurator/Vector_Test.geojson")
            default_raster_file = os.path.join(settings.STATIC_ROOT, "Configurator/Raster_Test.tif")

            #   Check if rasterization was requested
            raster["do"] = raster_factors.get('dorasterize',0)

            # Get the filename to rasterize, substituting in a default if no file is
            # provided.  We won't load the file data since we're just going to hand
            # the file path to R for processing.
            try:
                logger.debug("File: %s"%(job.datafile('rasterize')))
                raster["vectorfile"] = job.datafile('rasterize') # the file name
            except Exception as e:  # No file provided, so we'll pull out the default
                logger.debug(str(e))
                logger.debug("Using default vector file for rasterizing")
                raster["vectorfile"] = default_vector_name

            # Pull the rastervalue from the job configuration.  We don't care if it's
            # a literal numeric value or a property name.  The R function to
            # rasterize the file will use the value as a constant if provided, or
            # will use a string as the name of a feature attribute to provide the
            # raster value for that feature.
            raster["value"] = 1
            raster_value_set = job.getParameters('rasterize')
            if "rastervalue" in raster_value_set:
                raster["value"] = raster_value_set.get('rastervalue', 1)
            else:
                raster["value"] = 1
            raster["x_dim"] = raster_value_set.get('raster_x',300)
            raster["y_dim"] = raster_value_set.get('raster_y',300)
            # raster["proportional"] = raster_value_set.get('proportional',0)
            # raster["smoothing"] = raster_value_set.get('smoothing',0)

            #   Set output format (Rdata-RDS, Erdas IMAGINE, geoTIFF)
            raster_output = job.getParameters('rasterization_output')
            raster["returnvector"] = raster_output.get('return_vector',0)
            raster["format"] = raster_output.get('return_raster',"geoTIFF")
            rasterformat = RasterFormatTable.get(raster["format"],{})
            if not rasterformat:  # Did not request return of raster
                raster["returnraster"] = 0
                msg = "Invalid raster format %s"%(raster["format"],)
                client.UpdateStatus(msg)
                raster["rasterfile"] = ""
                raster["mimetype"] = ""
                raster["displayname"] = ""
                raster["savefunc"] = ""
                raster["loadfunc"] = ""
            else:
                raster["returnraster"] = 1
                rasterbasename = raster_output.get('raster_basename','raster')
                if not raster["do"]:
                    raster["format"] = "geoTIFF"
                    rasterformat = RasterFormatTable.get(raster["format"],{})
                raster["rasterfile"] = os.tempnam()+rasterformat["extension"]
                raster["mimetype"] = rasterformat["mimetype"]
                raster["displayname"] = rasterbasename + rasterformat["extension"]     # The name to offer when the raw raster is sent back
                if raster["do"]:
                    raster["savefunc"] = rasterformat["save"]%(raster["rasterfile"],)  # R Function to save a dataset to rastername in selected format
                else:
                    raster["savefunc"] = "savefunc<-function(obj){invisible(0)}"       # don't save over default file (shouldn't call, but just in case!)
                raster["loadfunc"] = rasterformat["load"]%(raster["rasterfile"],)      # R Function to load a raster for plotting

            if raster["do"]: # don't bother setting up unless rasterization requested
                client.updateStatus('Rasterization successfully configured.')
            else:
                client.updateStatus('Rasterization was not requested')

            ########################################
            # Image Generation (desired, output format)
            image_selection = job.getParameters('imaging_params')
            image["vector"] = image_selection.get('imagevector',0)
            image["raster"] = image_selection.get('imageraster',0)

            image_output = job.getParameters('image_output')
            image["format"] = image_output["imageformat"]
            imageformat = ImageFormatTable.get(image["format"][0:3],{})
            if not imageformat:
                # Unknown format, don't do images
                image["vector"] = image["raster"] = 0
                msg = "Invalid image format: %s (%s)"%(image["format"],image["format"][0:3])
                client.updateStatus(msg)
            if image["vector"] or image["raster"]:
                client.updateStatus("Imaging successfully configured.")
            else:
                client.updateStatus("Imaging was not requested.")

            client.updateStatus('Parameter & data file validation complete.')

            ###################################
            # Now perform the requested actions

            ###################################
            # Configuration Summary
            # Assemble an output file of what was configured (essentially for debugging)
            config_summary = StringIO.StringIO()
            dw = csv.DictWriter(config_summary, fieldnames=("Description","Value"), extrasaction='ignore')
            dw.writeheader()
            for section in ["compute","raster","image"]:
                if section in parameters:
                    dw.writerow({"Description":"Section", "Value" : section})
                    for description,value in parameters[section].iteritems():
                        dw.writerow(
                            {
                                "Description"  : "Parameter-%s-%s"%(section,description,),
                                "Value"        : str(value)
                            }
                        )
            del dw


            ###################################
            # Computation

            # Remember that all parameters, regardless of their stated type, arrive
            # in the tool as string representations (the promise is just that the
            # string will probably convert successfully to the tool_config type).
            # Thus all the computation code should perform idempotent conversions...
            if compute_Python:
                pyPower = decimal.Decimal(str(compute["power"]))
            if compute_R:
                if not R:
                    R = pyRserve.connect()
                else:
                    R.connect()
                R.r.rpower = compute["power"] # R.r.r...
                # The JSON parser (used in displaying NMTK results) chokes on a NaN
                # returned directly from R because it doesn't recognize an unquoted
                # NaN as numeric and sees it as a string without quotes; We'll
                # account for that in the R function and return a string
                R.r("""
                # Fun with R closure magic: convert the power from string to number
                # once then embed that in a function and return the function, which
                # we promptly call with the power to make the actual computational
                # function.  Note parenthetical priorities...

                compute <- (function(rp) {
                    rpower <- as.numeric(rp)
                    function(value) {
                        result <- as.numeric(value) ** rpower
                        if (is.nan(result)||is.na(result)) result<-"Nan-R"
                        result
                    }
                })(rpower)
                # Later, just call compute(value)
                """, void=True)

            for row in compute_file: # Loop over the rows in the input file
                for field, value in row.iteritems():
                    if compute_Python:
                        try:
                            pyValue = decimal.Decimal(str(value))
                        except:
                            pyValue = decimal.Decimal.from_float(float('nan'))
                        if not pyValue.is_nan():
                            pyResult = pyValue ** pyPower
                        else:
                            pyResult = "NaN-Python"
                        compute_file.addResult(compute["PythonName"]+"_"+field, pyResult)    
                    if compute_R:
                        Rresult = R.r.compute(value)
                        logger.debug("Computed R result for field %s, Result %s of value %s ** power %s"%(field, Rresult,value,R.r.rpower))
                        compute_file.addResult(compute["RName"]+"_"+field,Rresult)    
            if R:
                R.close()
            
            client.updateStatus('Done with computations')

            ###################################
            # Rasterization

            # If requested, take the input vector (either a supplied or default
            # file) and pass it through the R rasterization
            # If NOT requested, but imaging of a raster was presented, just
            # use the default raster from the world of static data

            if raster["do"]:
                if not R:
                    R = pyRserve.connect()
                else:
                    R.connect()
                R.r.vectorfile = raster["vectorfile"] # File to rasterize
                # Note that output file is built into "savefunc"
                R.r.xdim = raster["x_dim"]  # Desired raster resolution, x and y
                R.r.ydim = raster["y_dim"]
                R.r.rastervalue = raster["value"] # Value for raster cells,  either text/fieldname or numeric value
                R.r(raster["savefunc"]) # Load the function to save the raster in desired format
                # Actions:
                #   Load vector file
                #   Create extent from the file
                #   Create a blank raster with the right resolution (use default values)
                #   Rasterize the input file; raster.field can flexibly be a field name or a value
                #   Write it out in a suitable format for later plotting
                R.r("""
                    require(rgdal)
                    require(sp)
                    require(raster)
                    input.file <- readOGR(vectorfile,layer="OGRGeoJSON")
                    e <- extent(input.file)
                    t <- raster(e,nrows=ydim,ncols=ydim)
                    rsa <- rasterize(input.file,t,field=rastervalue)
                    savefunc(rsa)
                    """, void=True)
                if R:
                    R.close()

            ###################################
            # Imaging

            # If requested, take either the vector, the rasterized result or both
            # and pass them through R

            # Image file is raster["vectorfile"]
            image["vectorplotfile"] = ""
            image["rasterplotfile"] = ""
            if image["vector"] or image["raster"]:
                if not R:
                    R = pyRserve.connect()
                else:
                    R.connect()
                # TODO: Include basic plot parameters (e.g title of what we're plotting)
                R.r.plotformat = imageformat["R-device"] # Select R image output device
                R.r("""
                plotfunc <- function(to.plot, outfile) {
                    plotdev <- get(plotformat)
                    plotdev(file=outfile)
                    plot(to.plot)
                    dev.off()
                }
                """,void=True)

                if image["vector"]:
                    try:
                        R.r.plotfile = raster["vectorfile"]
                        R.r.outfile = image["vectorplotfile"] = os.tempnam()
                        R.r("""
                        library(sp)
                        library(rgdal)
                        to.plot <- readOGR(plotfile,layer="OGRGeoJSON")
                        plotfunc(to.plot,outfile)
                        """,void=True)
                    except Exception as e:
                        logger.debug(str(e))
                        client.updateStatus('Imaging failure(vector): '+str(e))

                if image["raster"]:
                    try:
                        # Change to use RasterFormatTable Load function to obtain the to.plot dataset
                        R.r(raster["loadfunc"]) # install load function for raster in requested format
                        R.r.outfile = image["rasterplotfile"] = os.tempnam()
                        R.r("""
                        library(raster)
                        to.plot <- loadfunc()
                        plotfunc(to.plot,outfile)
                        """,void=True)
                    except Exception as e:
                        logger.debug(str(e))
                        client.updateStatus('Imaging failure(raster): '+str(e))
                if R:
                    R.close()

            ###################################
            # Prepare results
            outfiles = {}
            main_result = "summary"
            comp_result = "computations"
            vector_input = "vectorinput"
            raster_file = "rasterfile"
            vector_plot = "vectorplotfile"
            raster_plot = "rasterplotfile"

            # Result files are a dictionary with a key (the multi-part POST slug),
            # plus a 3-tuple consisting of the recommended file name, the file data,
            # and a MIME type
            outfiles[main_result] = ( 'summary.csv', config_summary.getvalue(), 'text/csv' )
            if compute_R or compute_Python:
                outfiles[comp_result] = ( 'computation.%s'%(compute_file.extension,), compute_file.getDataFile(), compute_file.content_type )

            if image["vectorplotfile"] or raster["do"] or image["rasterplotfile"]:
                # There really should always be an "R" in this case
                if not R:
                    R = pyRserve.connect()
                else:
                    R.connect()

            if raster["returnvector"]:
                try:
                    vecbase = open(raster["vectorfile"])
                    outfiles[vector_input] = ( "vectorbase.geojson", vecbase.read(), "application/json" )
                    client.updateStatus('Returning input vector file as geojson')
                    vecbase.close()
                except Exception as e:
                    logger.debug(str(e))
                    client.updateStatus('Return vector failure: '+str(e))
            if image["vectorplotfile"]:
                try:
                    vecimg = open(image["vectorplotfile"],"rb")
                    outfiles[vector_plot] = ( 'vectorplot.%s'%(imageformat["extension"],), vecimg.read(), imageformat["mimetype"] )
                    vecimg.close()
                    client.updateStatus("Removing temporary vector file: "+image["vectorplotfile"])
                    R.r.unlink(image["vectorplotfile"]) # Get R to unlink the temporary file so we have permission
                except Exception as e:
                    logger.debug(str(e))
                    client.updateStatus("Preparing vector image output file failed: "+str(e))
            if raster["returnraster"]: # if we are expected to return a raster
                try:
                    rasterfile = open(raster["rasterfile"],"rb")
                    outfiles[raster_file] = ( raster["displayname"], rasterfile.read(), raster["mimetype"] )
                    rasterfile.close()
                except Exception as e:
                    logger.debug(str(e))
                    client.updateStatus("Preparing raw raster output file failed: "+str(e))
            if raster["do"]: # clean up the temporary rasterization file (may have done this without return raw file)
                try:
                    client.updateStatus("Removing temporary raster file: "+raster["rasterfile"])
                    R.r.unlink(raster["rasterfile"]) # Get R to unlink the temporary file so we have permission
                except Exception as e:
                    logger.debug(str(e))
                    client.updateStatus("Preparing raw raster output file failed: "+str(e))
            if image["rasterplotfile"]:
                try:
                    rstimg = open(image["rasterplotfile"],"rb")
                    outfiles[raster_plot] = ( 'rasterplot.%s'%(imageformat["extension"],), rstimg.read(), imageformat["mimetype"] )
                    rstimg.close()
                    client.updateStatus("Removing temporary raster file: "+image["rasterplotfile"])
                    R.r.unlink(image["rasterplotfile"]) # Get R to unlink the temporary file so we have permission
                except Exception as e:
                    logger.debug(str(e))
                    client.updateStatus("Preparing raster image output file failed: "+str(e))

            if outfiles:
                client.updateResults(result_field=None,         # Default field to thematize in result_file
                                     units=None,                # Text legend describing the units of 'result_field'
                                     result_file=main_result,   # Supply the file 'key' (see outfiles above)
                                     files=outfiles             # Dictionary of tuples providing result files
                                 )
            if R:
                R.close()

        except Exception as e:
            msg = 'Job failed.'
            logger.exception(msg)
            logger.exception(str(e))
            job.fail(msg)
            job.fail(str(e))
            client.updateResults(payload={'errors': job.failures },
                                 failure=True,
                                 files={}
                                )

    # Clean up R after all is done (harmless if R is None, cleans up
    # connection to Rserve otherwise)
    del R
