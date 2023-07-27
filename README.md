# Overview
AirWaves is a website monitoring tv reception signals in the Greater Boston Area. This website utilizes the Plotly JS and Python graphing libraries to explore relationships between signal strength, signal quality, and symbol (picture) quality and weather conditions for real channel frequencies. 

# Data Management
Frequencies recieved by an antenna are run through an HDHomeRun Connect Duo tuner. These frequencies (signal measurements) are fetched from the tuner's API and stored on a database maintained on our server. AirWaves reads signal measurements and weather data from this database.

# Services
AirWaves offers three main services: Track Channel, Channel Distribution, and Scan Summary.

### Track Channel
Plotting Channel Signal Measurements Over Time. Link changes in signal measurements to weather conditions.

![Track Channel](http://www.employees.org/~ad4437/trackchannel.png)

### Channel Distribution
Plotting Signal Measurement Distributions for Various Channels. View the signal measurement distribution of tv reception for your weekly programs via the filter button

![Track Channel](http://www.employees.org/~ad4437/channeldistribution.png)

### Scan Summary
Plotting Channel Signal Measurements for an Individual Scan. View the latest scan data in more detail.

![Track Channel](http://www.employees.org/~ad4437/scansummary.png)

# Electromagentic Interference
AirWaves started as a way to determine the effects of solar panels on TV reception via an antenna. After their installation, the solar panels produced visible effects on VHF channels:

Before Installation:

![Signal Quality Graph of Real Channel 5 Before Solar Panels](http://www.employees.org/~ad4437/channel5snqBeforeSolar.JPG)

After Installation:

![Signal Quality Graph of Real Channel 5 After Solar Panels](http://www.employees.org/~ad4437/channel5snq.png)

As can be seen in the graph, the signal quality is poor during the day (when the sun is up) and strong during the night (when the sun is down). The signal quality is so poor during the day that the signal, at times, cannot be deciphered, as seen with the picture quality graph below.

![Picture Quality Graph of Real Channel 5](http://www.employees.org/~ad4437/channel5seq.png)

Note: A seq value of 100 means the signal is watchable, while a value of 0 means that it cannot be watched (static)

This data suggests that solar panels, when generating electricity, interfere with the radio waves and yield worse TV reception for VHF channels.

# Tested Browsers
| Browser         | Version         |
|-----------------|-----------------|
| Firefox         | 78.0.2          |
| Chrome          | 83.0.4103.112   |
| Microsoft Edge  | 44.18362.449.0  |
| Safari          | 13              |
