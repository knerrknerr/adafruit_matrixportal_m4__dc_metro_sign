# adafruit_matrixportal_m4__dc_metro_sign
A Display for the AdaFruit Matrix Portal M4 using the WMATA Metro API

This display is inspired by https://github.com/metro-sign/dc-metro. In addition to displaying arrival and departure times, it also adds a small tracker along the bottom of the sign showing trains as they approach your station from the east and west. 

You will need to generate a free WMATA API key in order to use this code. Go to https://developer.wmata.com/ to do this. You should add the key (along with your WiFi credentials) in your secrets.py file.

This code is configured for the Courthouse metro station. If you want to use it for your own station:

* Update the station_name parameter with your station code. You can use the WMATA API request https://api.wmata.com/Rail.svc/json/jStations to learn the station codes.
* Update the west_stations array with a list of station codes west of your station. This will be used to deterimine the direction that trains travel across the bottom of the display.
* Update the get_line_color function to reflect the lines that pass through your station.
