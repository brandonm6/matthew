
# Example of Storm Surge from Hurricane Matthew

This example provides the data and Python code to run a simulation of Hurricane Matthew along the Eastern Seaboard. Matthew made landfall approximately 30 miles northeast of Charleston, South Carolina on October 8, 2016 as a Category 1 storm. The simulation models 3 days of the storm, beginning two days before landfall over South Carolina.

Running `make all` will compile all the necessary code for running the simulation.

## Topography

Topography data can be downloaded from https://download.gebco.net/# using boundaries of: 
 - N: 50.0, S: 10.0, W: -90.0, E: -60.0
Use the Esri ASCII Grid format when downloading.

## Storm Data

Storm data is automatically downloaded from the NOAA atcf archive at: 
http://ftp.nhc.noaa.gov/atcf/archive/2016/bal142016.dat.gz

## Gauges

 - Full Domain (all):
    - Mayport (Bar Pilots Dock), FL 		       8720218
    - Dames Point, FL				                    8720219
    - Fort Pulaski, GA				                   8670870
    - Oyster Landing (N Inlet Estuary), SC		 8662245
    - Springmaid Pier, SC				                8661070
    - Wrightsville Beach, NC			              8658163
    - Wilmington, NC				                     8658120


 - Carolinas:
    - Oyster Landing (N Inlet Estuary), SC		 8662245
    - Springmaid Pier, SC				                8661070
    - Wrightsville Beach, NC			              8658163
    - Wilmington, NC				                     8658120
