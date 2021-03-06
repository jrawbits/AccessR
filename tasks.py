# At a minimum, you'll want to import the following items to
# communicate with the NMTK.
from celery.task import task
import datetime

# For this specific tool, we import the following helpers
import NMTK_apps.helpers.confighelpers as Config
import decimal
import os
import pyRserve

# subtool implementations

def DoAccess0(job,client):
    "Set up a study area from a vector file."

    # Retrieve job configuration
    rasterize = job.getParameters('rasterize')  # Properties/Constants for file
    parameters = job.getParameters('rasterization_params')
    output = job.getParameters('studyarea_output')

    # Set up values in R
    job.R.r.infile   = job.datafile('rasterize') # incoming temporary file
    job.R.r.pixels_x = parameters["raster_x"]
    job.R.r.pixels_y = parameters["raster_y"]
    job.R.r.value    = rasterize["rastervalue"]  # either a field or value
    outputfile       = os.tempnam()+".tif" # writeRaster adds extension if not present
                                           # so we lose control of the name if we don't
                                           # make it explicit here.
    job.R.r.outfile  = outputfile

    # Run R analysis
    analysis = """
    require(sp)
    require(rgdal)
    require(raster)
    studyarea = readOGR(infile,layer="OGRGeoJSON")
    self.oobSend("Loaded data; starting analysis.")
    output.CRS <- CRS("+init=epsg:4326")
    studyarea = spTransform(studyarea,output.CRS)
    ex <- extent(studyarea)
    r.study <- raster(ex,pixels_x,pixels_y,crs=output.CRS)
    r.study <- rasterize(studyarea,r.study,field=value)
    self.oobSend("Analysis complete; writing output.")
    writeRaster(r.study,filename=outfile,format="GTiff",overwrite=TRUE)
    """
    job.R.oobCallback = lambda msg, code: client.updateStatus("R: "+msg)
    job.R.r(analysis,void=True)

    # Prepare results
    if os.path.exists(outputfile):         # File exists, so we should clean it up
        job.tempfiles.append(outputfile)
    outputdata             = open(outputfile,"rb")
    resultfilename         = output.get('studyareafile','StudyArea')+".tif"
    outfiles               = { "studyarea" : ( resultfilename, outputdata.read(),"image/tiff" ) }
    outputdata.close()

    results = {}
    results["result_file"] = "studyarea"
    results["files"]       = outfiles
    return results

OverlayFunctions = {
    "Barrier"  : "function(x,y) ifelse(!is.na(y),0.0,x)",
    "Obstacle" : "function(x,y) pmin(x,y,na.rm=TRUE)",
    "Facility" : "function(x,y) pmax(x,y,na.rm=TRUE)",
    }

def DoAccess1(job,client):
    "Add vector of barriers, obstacles and facilities to a study raster"

    # Retrieve job configuration
    overlay = job.getParameters('overlay')  # Properties/Constants for file
    parameters = job.getParameters('overlay_type')
    output = job.getParameters('accessibility_output')

    # Retrieve accessibility file (raster)
    # Retrieve layer file for rasterization and overlay (geoJSON)
    # Retrieve processing type and install suitable overlay function
    # Construct temporary file name (and stash for unlinking in wrapper)
    # Run R analysis
    job.R.r.rasterfile = job.datafile('accessibility')  # path to input raster
    job.R.r.vectorfile = job.datafile('overlay')       # path to input vector (for overlay)
    job.R.r.value      = overlay["accessibility"]      # field name or value for computing raster values
    outputfile         = os.tempnam()+".tif"           # Temporary file name for output
    job.R.r.outfile    = outputfile

    # Select overlay functions:
    #   "Barrier" = turn overlapped cells to NA
    #   "Obstacle" = turn overlapped cells to minimum of two cell values (NA stays NA)
    #   "Facility" = turn overlapped cells to maximum of two cell values (NA stays NA)
    factype = parameters["overlay_style"]
    if factype in OverlayFunctions:
        job.R.r("overfun<-"+OverlayFunctions[factype])
    else:
        raise Exception("Unknown Overlay Style:",factype)
#     client.updateStatus(" ".join(("Rasterfile:",rasterfile,"R Rasterfile:",job.R.r.rasterfile)))
#     client.updateStatus(" ".join(("Vectorfile:",vectorfile,"R Rasterfile:",job.R.r.vectorfile)))
#     client.updateStatus(" ".join(("Outfile:",outputfile,"R Rasterfile:",job.R.r.outfile)))

    analysis = """
    require(sp)
    require(rgdal)
    require(raster)
    r.raster <- raster(rasterfile)
    r.vector <- readOGR(vectorfile,layer="OGRGeoJSON")
    self.oobSend("Loaded data; starting analysis.")
    r.vector <- spTransform(r.vector,projection(r.raster)) # Force the same projection
    r.over <- rasterize(r.vector,r.raster,field=value)
    self.oobSend("Overlay prepared; starting analysis.")
    Accessibility <- overlay(r.raster,r.over,fun=overfun)
    Accessibility <- projectRaster(Accessibility,crs=CRS("+init=epsg:4326")) # NMTK struggles with rasters not in longlat
    self.oobSend("Analysis complete; writing output.")
    writeRaster(Accessibility,filename=outfile,format="GTiff",overwrite=TRUE)
    """
    job.R.oobCallback = lambda msg, code: client.updateStatus("R: "+msg)
    job.R.r(analysis,void=True)

    # Prepare results
    if os.path.exists(outputfile):         # File exists, so we should clean it up
        job.tempfiles.append(outputfile)
    outputdata             = open(outputfile,"rb")
    resultfilename         = output.get('accessibilityfile','Accessibility')+".tif"
    outfiles               = { "Accessibility" : ( resultfilename, outputdata.read(),"image/tiff" ) }
    outputdata.close()

    results = {}
    results["result_file"] = "Accessibility"
    results["files"]       = outfiles
    return results

# def BugDemo(job,client):
#     "Just copy a raster to output (for debugging projection problem)"
# 
#     output = job.getParameters('studyarea_output')
#     job.R.r.rasterfile = job.datafile('rasterbug')  # path to input raster
#     outputfile         = os.tempnam()+".tif"        # Temporary file name for output
#     job.R.r.outfile    = outputfile
# 
#     analysis = """
#     require(raster)
#     r.raster <- raster(rasterfile)
#     writeRaster(r.raster,filename=outfile,format="GTiff",overwrite=TRUE)
#     """
#     job.R.r(analysis,void=True)
# 
#     # Prepare results
#     if os.path.exists(outputfile):         # File exists, so we should clean it up
#         job.tempfiles.append(outputfile)
#     outputdata             = open(outputfile,"rb")
#     resultfilename         = output.get('studyareafile','BugDemo')+".tif"
#     outfiles               = { "bugdemo" : ( resultfilename, outputdata.read(),"image/tiff" ) }
#     outputdata.close()
# 
#     results = {}
#     results["result_file"] = "bugdemo"
#     results["files"]       = outfiles
#     return results

# We have to do some reformatting of the raw JSON points file since the
# NMTK sometimes wants to deliver "MultiPoint" features, but R can
# only handle "Point" features
import json

def DoAccess2(job,client):
    "Compute isochrones on an accessibility map from a set of points"

    # Retrieve job configuration
    # Note: this tool does not use properties of the input files
    output = job.getParameters('isochrone_output')

    # Get the raster accessibility map
    job.R.r.rasterfile = job.datafile('accessibility') # path to input raster

    # Get the points at which to evaluate isochrones
    points = json.load(file(job.datafile('points')))  # Work around NMTK-R incompatibility
    for feature in points["features"]:
        if feature["geometry"]["type"] == "MultiPoint":
            feature["geometry"]["type"] = "Point"
            feature["geometry"]["coordinates"] = feature["geometry"]["coordinates"][0]
    pointfilename = os.tmpnam()+".geojson"
    ptfile = file(pointfilename,"w")
    json.dump(points,ptfile)
    ptfile.close()  # Explicitly close the file (rather than rely on garbage collection)
                    # so R can open and later delete it reliably

    job.R.r.pointfile  = pointfilename
    outputfile         = os.tempnam()+".tif"           # Temporary file name for output
    job.R.r.outfile    = outputfile

    analysis = """
    require(sp)
    require(rgdal)
    require(raster)
    require(gdistance)
    r.raster = raster(rasterfile)
    r.points = readOGR(pointfile,layer="OGRGeoJSON")
    r.points = spTransform(r.points,projection(r.raster))
    self.oobSend("Loaded data; starting analysis.")

    # Perform geographic corrections, scaling to X resolution of map
    # in order to get weighted distances.
    # Does this work with EPSG:4326?
    map.unit <- xres(r.raster)
    tr.func <- function(x) mean(x)*map.unit
    tr.matrix <- transition(r.raster,tr.func,8)
    geo.correct <- geoCorrection(tr.matrix,multpl=TRUE)
    cost.network <- geo.correct * tr.matrix
    self.oobSend("Network prep complete; starting evaluation.")

    # Use cost.network to compute isochrones from sample points
    cost <- function(x,y) accCost(cost.network,c(x,y))
    vcost <- Vectorize(cost,c("x","y"))
    Isochrones <- brick(vcost(r.points$coords.x1,r.points$coords.x2)) # RasterBrick

    # accCost produces Inf for cells that can't be reached; make those NA
    values(Isochrones)[which(is.infinite(values(Isochrones)))] <- NA
    # accCost produces 0 for cells that coincide with Points; make those half the non-zero shortest distance
    values(Isochrones)[which(values(Isochrones)==0)] <- min(values(Isochrones)[which(values(Isochrones)>0)])/2

    # Scale results for display (probably want to parameterize normalization)
    # max.isochrone = max(values(Isochrones),na.rm=TRUE)
    # min.isochrone = min(values(Isochrones),na.rm=TRUE)
    # self.oobSend(paste("Isochrone min:",min.isochrone,"Isochrone max:",max.isochrone,sep=" "))
    # Isochrones <- ( Isochrones / max.isochrone ) * 10
    self.oobSend("analysis complete; writing output.")

    # Summarize individual Isochrones
    Destinations <- min(Isochrones) # RasterLayer from RasterBrick
    ResultIsochrones <- brick(list(Destinations,Isochrones))

    writeRaster(ResultIsochrones,filename=outfile,format="GTiff",overwrite=TRUE)
    """
    job.R.oobCallback = lambda msg, code: client.updateStatus("R: "+msg)
    job.R.r(analysis,void=True)

    # Prepare results
    if os.path.exists(pointfilename):      # File exists, so we should clean it up
        job.tempfiles.append(pointfilename)
    if os.path.exists(outputfile):
        job.tempfiles.append(outputfile)
    outputdata     = open(outputfile,"rb")
    resultfilename = output.get('isochronefile','Isochrone')+".tif"
    outputkey = "Isochrone"
    outfiles       = { outputkey : ( resultfilename, outputdata.read(),"image/tiff" ) }
    outputdata.close()

    results = {}
    results["result_file"] = outputkey
    results["files"]       = outfiles
    return results

# dispatch dictionary
doSubTool = {
    "Access0" : DoAccess0,
    "Access1" : DoAccess1,
    "Access2" : DoAccess2,
#    "BugDemo" : BugDemo,
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

    # AccessR - Dispatch to subtools
    with Config.Job(input_files,tool_config) as job:
        try:
            job.setup()
            job.logger = logger  # in case we need it...
            job.tempfiles = []
            job.R = pyRserve.connect()
            if subtool_name in doSubTool:
                results = doSubTool[subtool_name](job,client)
                if results:
                    client.updateResults(result_field=results.get("field",None),
                                         units=results.get("units",None),
                                         result_file=results.get("result_file",None),
                                         files=results.get("files",None)
                                     )
                else:
                    raise Exception("No results returned from subtool '%s'"%(subtool_name,))
            else:
                raise Exception("SubTool not found: "+subtool_name)

        except Exception as e:
            # Every failure should result in an Exception
            # use job.fail to add additional failure messages before
            # raising the Exception, as illustrated here
            msg = 'Job failed.'
            logger.exception(msg)
            logger.exception(str(e))
            job.fail(msg)
            job.fail(str(e))
            client.updateResults(payload={'errors': job.failures },
                                 failure=True,
                                 files={}
                             )
        finally:
            if hasattr(job,"tempfiles"):
                if not hasattr(job,"R"): # low likelihood...
                    job.R = pyRserve.connect()
                for file in job.tempfiles:
                    job.R.r.unlink(file)
            if hasattr(job,"R")and job.R:
                job.R.close()
