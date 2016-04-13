# This file is a hard-coded sequence that will establish a study area and build accessibility
# isochrones from a set of sample points.

# These are the procedures that the AccessR set of tools implement.

require(rgdal)
require(sp)
require(raster)
require(gdistance)

# Load the pre-digested files

message("Loading data from URL")
load(url("https://www.dropbox.com/s/oeol5opggniyhic/ALX_NMTK_Shapes2.RData?dl=1"))

##################################################
# Study Area Preparation (base Accessibility map)
##################################################

# Prepare extent and rasterization
ex <- extent(alx.study.area)
pixels_x <- 300
pixels_y <- 300
value <- 1.000000

r.study <- raster(ex,pixels_x,pixels_y,crs=alx.study.area@proj4string)
r.study <- rasterize(alx.study.area,r.study)
Accessibility <- calc(r.study,function(x){ifelse(is.na(x),NA,value)})

##################################################
# Add Accessibility layers
##################################################

# Ugly Roads (0)
r.ugly <- rasterize(alx.network.ugly,r.study,field=0.0)
Accessibility <- overlay(Accessibility,r.ugly,fun=function(x,y) pmin(x,y,na.rm=TRUE))

# Buildings (0)
r.buildings <- rasterize(alx.buildings,r.study,field=0.0,silent=TRUE)
Accessibility <- overlay(Accessibility,r.buildings,fun=function(x,y) pmin(x,y,na.rm=TRUE))

# Nice Roads (increment)
r.nice <- rasterize(alx.network.nice,r.study,field=2.0)
Accessibility <- overlay(Accessibility,r.nice,fun=function(x,y) pmax(x,y,na.rm=TRUE))

# Bike Facilities (on-road)
r.bikelanes <- rasterize(alx.bike.lanes,r.study,field=3.0)
Accessibility <- overlay(Accessibility,r.bikelanes,fun=function(x,y) pmax(x,y,na.rm=TRUE))

# Bike Trails (off-road)
r.bikepaths <- rasterize(alx.bike.trails,r.study,field=4.0)
Accessibility <- overlay(Accessibility,r.bikepaths,fun=function(x,y) pmax(x,y,na.rm=TRUE))

# Sidewalks
value = 4.0
r.sidewalks <- rasterize(alx.sidewalks,r.study,getCover=TRUE,field=value)
r.sidewalks <- calc(r.sidewalks,function(x){ pmin(x,50) * value / 50.0 })
Accessibility <- overlay(Accessibility,r.sidewalks,fun=function(x,y) pmax(x,y,na.rm=TRUE))

# Save the Accessibility Raster, using the standard EPSG version of its projection
# Question:  How often (or when) do we need to assign projection?
projection(Accessibility) <- CRS("+init=epsg:26918")
writeRaster(Accessibility,filename="Accessibility.tif",format="GTiff",overwrite=TRUE)

##################################################
# Compute Accessibility Isochrones
##################################################

# Need point file of "stations" for isochrones

# Perform geographic corrections
# scale to X resolution of map, so geoCorrection produces weighted distance
# that correction is needed so shortest path statistics come out right
map.unit <- xres(Accessibility)
tr.func <- function(x) mean(x)*map.unit
tr.matrix <- transition(Accessibility,tr.func,8)
geo.correct <- geoCorrection(tr.matrix,multpl=TRUE)
cost.network <- geo.correct * tr.matrix

# Compute isochrones from sample points
cost <- function(x,y) accCost(cost.network,c(x,y))
vcost <- Vectorize(cost,c("x","y"))
Isochrones <- brick(vcost(alx.stations$coords.x1,alx.stations$coords.x2)) # RasterBrick

# accCost produces Inf for cells that can't be reached; make those NA
values(Isochrones)[which(is.infinite(values(Isochrones)))] <- NA
# accCost produces 0 for cells that coincide with Points; make those half the non-zero shortest distance
values(Isochrones)[which(values(Isochrones)==0)] <- min(values(Isochrones)[which(values(Isochrones)>0)])/2

# Scale the results for display (parameter)
Isochrones <- Isochrones * 10

# Summarize individual Isochrones
Destinations <- min(Isochrones)               # RasterLayer from RasterBrick
ResultIsochrones <- brick(list(Destinations,Isochrones))

# Save resulting Brick out as a geoTIFF for display within the NMTK
writeRaster(ResultIsochrones,filename="Isochrones.tif",format="GTiff",overwrite=TRUE)

# Save image
save.image(file="DoAccessibilityResults.Rdata")


