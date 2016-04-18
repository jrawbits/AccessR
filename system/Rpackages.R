package.list <- c("sp","raster","rgdal","gdistance","Rserve","RSclient")
for (p in package.list) {
    if (! require(p,character.only=T)) {
        install.packages(p,lib='/usr/local/lib/R/site-library',repos='https://mirrors.nics.utk.edu/cran/')
    }
}
