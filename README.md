# Overview
[AirWaves](http://www.employees.org:58000/) is a website monitoring tv reception signals in the Greater Boston Area. This website utilizes the Plotly JS and Python graphing libraries to explore relationships between signal strength, signal quality, and symbol (picture) quality and weather conditions for real channel frequencies. 
# Data Management
Frequencies recieved by an antenna are run through an HDHomeRun Connect Duo tuner. These frequencies (signal measurements) are fetched from the tuner's API and stored on a database maintained on our server. AirWaves reads signal measurements and weather data from this database. The source code for this program has not been made public.
#Tested Browsers
| Browser         | Version         |
|-----------------|-----------------|
| Firefox         | 78.0.2          |
| Chrome          | 83.0.4103.112   |
| Microsoft Edge  | 44.18362.449.0  |
| Safari          | 13              |