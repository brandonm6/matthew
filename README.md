
# Example of Storm Surge from Hurricane Matthew

This example provides the data and Python code to run a simulation of Hurricane Matthew along the Eastern Seaboard. 
Matthew made landfall approximately 30 miles northeast of Charleston, South Carolina on October 8, 2016 as a Category 1 
storm. The simulation models 3 days of the storm, beginning two days before landfall over South Carolina.

Running `make all` will compile all the necessary code for running the simulation.

## Topography

Topography data can be downloaded from 
* https://download.gebco.net
  * Use boundaries of N: 50.0, S: 10.0, W: -90.0, E: -60.0 
  * Use the Esri ASCII Grid format when downloading.
  
* https://www.ngdc.noaa.gov/thredds/fileServer/crm/crm_vol2.nc

It is automatically downloaded, however, by _setrun_.py
* The GEBCO topography file is stored here 
  * https://www.dropbox.com/s/s58bi1l45tw9uka/gebco_2020_n50.0_s10.0_w-90.0_e-60.0.asc?dl=1

into the `matthew/scratch` directory.

## Storm Data

Storm data is automatically downloaded from the NOAA atcf archive at 
http://ftp.nhc.noaa.gov/atcf/archive/2016/bal142016.dat.gz

into the `matthew/scratch` directory.

## Gauges

Gauges 1-5 in the example correspond to five NOAA Tides and Currents Stations (selected from https://stn.wim.usgs.gov/FEV/#MatthewOctober2016) along the Eastern Seaboard.
The`fetch_noaa_tide_data()` method is used to compare the observed gauge data (de-tided) to the simulated gauge data in _setplot.py_. 

1. Mayport (Bar Pilots Dock), FL 8720218 
2. Fort Pulaski, GA 8670870 
3. Charleston, Cooper River Entrance, SC 8665530 
4. Wrightsville Beach, NC 8658163 
5. Wilmington, NC 8658120

Coordinates for each gauge can be found in _setrun.py_.

## AMR Flagregions

Regions that are refined at higher levels are drawn in Google Earth as polygons and downloaded to _regions.kml_. The 
.kml file is then run through _kml2slu.py_, which makes it useable for setting AMR flagregions. Raising the levels 
assigned to each region in _setrun_.py may provide more accurate storm surge predictions but will increase runtime.

The flagregions in this example are "Ruled Rectangles," covering the bodies of water surrounding each gauge. Opening 
_regions.kml_ in Google Earth will display the locations of the gauges along with their respective flagregions. 

Levels assigned to each flagregion can be found in _setrun.py_.





