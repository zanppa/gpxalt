# gpxalt
A simple program to replace GPX track altitudes with accurate altitude data of National Land Survey of Finland.

Note that this program only works for tracks that are inside Finnish borderd.

## Background
Since at least 2014 the National Land Survey of Finland (NLS, Maanmittauslaitos) has opened up lots of their 
data, including the laser scanned elevation data. There is elevation data for whole Finaldn with [10 m grid](https://www.maanmittauslaitos.fi/en/maps-and-spatial-data/expert-users/product-descriptions/elevation-model-10-m), 
and part of Finland also has [2m grid](https://www.maanmittauslaitos.fi/en/maps-and-spatial-data/expert-users/product-descriptions/elevation-model-2-m). The first has accuracy of 1.4 m while the second has 0.3 m accuracy.

Because Finland is so close to the North Pole, the GPS elevation accuracy is very low. to increase the accuracy, 
I wrote this program to download relevant parts of the elevation data from NLS (the data is only available in tiles) 
and use that to replace the inaccurate elevation data of the GPX track with more accurate measured one.

## Getting started
This program is written in Python 2.7. It uses some external libraries, and I've included two in the repository.

### Prerequisites
This program needs following external libraries:
```
numpy
urllib
gpxpy
argparse
```
They can all be installed with ```pip```.

### Running the program
First you need to get an API key to the file service of NLS: [Link to the order page](https://tiedostopalvelu.maanmittauslaitos.fi/tp/mtp/tilaus?lang=en).

After you get the key, create a file called ```api_key``` inside the repository and place the key there.
Then simply run the following command inside the repository root:
```
python gpxalt.py /path/to/your/track.gpx
```
This will go through the track point-by-point and download relevant tiles from the NLS file server
and cache them locally to ```./cache/```. From those tiles it will read the laser scanned altitude.
The final altitude corrected file will be named in the working directory as ```track_altfix.gpx```
(if the original was ```track.gpx```).

### Parameters
The full command line is as follows:
```
usage: gpxalt.py [-h] [--api-key API_KEY] [--cache CACHE] [-v] input [output]

positional arguments:
  input              input GPX file name
  output             output GPX file name

optional arguments:
  -h, --help         show this help message and exit
  --api-key API_KEY  api key for NLS open data access
  --cache CACHE      path to the cache folder, default: .\cache\
  -v, --verbose      verbose output, add multiple for more info
```
It should be noted that if ```--api-key``` is not used, the program tries to load the key from a file called ```api_key```.

### Known bugs
With some track the gpx parser dies to an exception about stripping a Nonetype, I'm not sure why this happens...

## Comparison
I made few comparisons of the laser scanned data and other sources.

First is a comparison of one of my tracks. Old is the original GPS elevation while new is what this program outputted.
![GPS comparison 1](https://github.com/zanppa/gpxalt/raw/master/docs/comparison.png)
As can be seen, both have similar shape but the new one has much more details.

The second track I first compared with raw GPS elevation data:
![GPS comparison 2](https://github.com/zanppa/gpxalt/raw/master/docs/comparison_to_gps.png)
Again the shape is similar but there is much more details in the new one.

 also checked the same track against the elevation fix algorithm (data?) from [Garmin Connect](https://connect.garmin.com):
 ![Garmin comparison](https://github.com/zanppa/gpxalt/raw/master/docs/comparison_to_garmin_fix.png)
 The Garmin fix has quite a bit of offset, and it does not have anywhere near as much detail as this one.
 
 ## Licenses
 I included the two libraries that I used but were not very simple to find. They have their own licenses which are
 included in the respective directories and also included in the source code.

