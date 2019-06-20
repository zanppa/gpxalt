# gpxalt
A simple program to replace GPX track elevation with accurate laser-scanned elevation data of National Land Survey of Finland.

Note that this program only works for tracks that are inside Finnish borders.

## Background
Since at least 2014 the National Land Survey of Finland (NLS, Maanmittauslaitos) has opened up lots of their 
data, including the laser scanned elevation data. There is elevation data for whole Finland with [10 m grid](https://www.maanmittauslaitos.fi/en/maps-and-spatial-data/expert-users/product-descriptions/elevation-model-10-m), 
and part of Finland also has [2m grid](https://www.maanmittauslaitos.fi/en/maps-and-spatial-data/expert-users/product-descriptions/elevation-model-2-m). The first has elevation accuracy of 1.4 m while the second has 0.3 m accuracy.

Because Finland is so close to the North Pole, the GPS elevation accuracy is very low. To increase the elevation accuracy 
in the GPS tracks, I wrote this program to download relevant parts of the elevation data from NLS (the data is only 
available in tiles) and use those to replace the inaccurate elevation data of the GPX track with more accurate measured one.

The program takes the input track and for each point, converts the WGS84 GPS coordinates to ETRS-TM35FIN according to 
[this file](http://www.jhs-suositukset.fi/c/document_library/get_file?folderId=43384&name=DLFE-1012.pdf) and 
[this file](http://www.jhs-suositukset.fi/c/document_library/get_file?folderId=43384&name=DLFE-1006.pdf). Then, using the 
converted coordinates the program first checks if the tile exists in local cache. If not, it calculates the tile path in NLS 
file service, and tries to download the 2 m tile and if that fails, the 10 m tile is downloaded into the cache.

The geotiff tile is then read from the cache and the altitude is read from the correct coordinates, and the track point 
elevation data is replaced with the new value. When all points are handled, the new gpx track is written to disk.

## Getting started
This program is updated to Python 3. It requires some external libraries; two necessary ones are included in the repository.

### Prerequisites
Following external libraries are required:
```
numpy
urllib
gpxpy
argparse
```
They can all be installed with ```pip```.

### Running the program
First you need to get an API key to the file service of NLS: [Link to the order page](https://tiedostopalvelu.maanmittauslaitos.fi/tp/mtp/tilaus?lang=en).

After you get the key, create a file called ```api_key``` inside the repository and place the key there (Note: it is 
also possible to provide the key with command line argument or via environment variable if preferred).

Then simply run the following command inside the repository root:
```
python gpxalt.py /path/to/your/track.gpx
```
This will go through the track point-by-point and download relevant tiles from the NLS file server
and cache them locally to ```./cache/```. From those tiles it will read the laser scanned elevation.
The final elevation corrected file will be named in the working directory as ```track_altfix.gpx```
(if the original was ```track.gpx```).

### Parameters
The full list of command line arguments is:
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
If ```--api-key``` is not used, the program tries to read the key from environment variable ```NLS_API_KEY```. If that does not exist, the program tries to load the key from a file called ```api_key```. If no api key is provided, only local cache will be used.

### Known bugs / notes
* With some tracks the gpx parser dies to an exception about stripping a Nonetype, I'm not sure why this happens...
* For automatic output file naming, the original file name must end with lowercase ``´.gpx``´.
* The tifffile library I used is very slow; however it was only one I found that could properly read the GeoTIFFs from NLS.

## Comparison
I made few comparisons of the laser scanned data with other sources. In the graphs, X axis is the gpx track point number and Y axis is the elevation in meters (from sea level, I assume). The ```old``` line is the original elevation from the gpx file and ```new``` line is the result after using this program.

First is a comparison of one of track with just GPS elevation (Garmin Forerunner 110).
![GPS comparison 1](https://github.com/zanppa/gpxalt/raw/master/docs/comparison.png)
As can be seen, both elevatino profiles have similar shape but the new one has much more details.

For the second track I first compared the GPS elevation (Garmin Forerunner 110) to the output of this program:
![GPS comparison 2](https://github.com/zanppa/gpxalt/raw/master/docs/comparison_to_gps.png)
Again the shape is similar but there is much more details in the new graph.

I then applied an elevation fix algorithm from [Garmin Connect](https://connect.garmin.com) to the track and compared that result:
![Garmin comparison](https://github.com/zanppa/gpxalt/raw/master/docs/comparison_to_garmin_fix.png)
The Garmin fix has quite a bit of offset, and it does not have anywhere near as much detail as the fixed track.

Lately I've got a new watch from Suunto (Spartan Ultra), which has barometer and uses [FusedAlti](https://www.suunto.com/Support/Product-support/suunto_traverse/suunto_traverse/features/fusedalti/) technology to mix barometer and GPS to achieve an accurate elevation profile. I compared a track with that method to the output of this program:
![Suunto FusedAlti comparison](https://github.com/zanppa/gpxalt/raw/master/docs/comparison_to_suunto.png)
It can be seen that in this case both lines are almost on top of each other, which indicates that this program has quite accurate output (typically barometer measurement is rather accurate). Only slight divergence is visible, probably due to changing atmospheric pressure. The start and end elevation should be the same.

## License
Copyright (C) 2018, 2019 Lauri Peltonen
 
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
 
## Included libraries
The two libraries that I used but which were difficult to find are included in the repository. They have their own licenses which are
included in the respective directories and also included in the source code.

* ```tifffile.py```, [original link](https://www.lfd.uci.edu/~gohlke/code/tifffile.py.html). For reading geotiff files.
* ```coordinates.py```, [original link](https://olammi.iki.fi/sw/coordinates/). For converting WGS84 to ETRS-TM35FIN.
