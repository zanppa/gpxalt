# -*- coding: utf-8 -*-
"""
A python program to read a GPX track and to replace its elevation 
data with data from National Land Survey of Finland.

Copyright (C) 2018, 2019 Lauri Peltonen
"""

import sys		# sys.exit
import os		# os.environ
import gpxpy
from tilecache import TileCache
import argparse


def fix_gpx_file():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='A program to fix GPX track altitudes by using altitude data from National Land Survey of Finland', 
        epilog='Example: python gpxalt.py my_gps_track.gpx my_fixed_gps_track.gpx')
    parser.add_argument("input", help='input GPX file name')
    parser.add_argument("output", nargs='?', help='output GPX file name', default='')  # Optional output
    parser.add_argument('--api-key', help='api key for NLS open data access')
    parser.add_argument('--cache', default='.\\cache\\', help='path to the cache folder, default: .\\cache\\')
    parser.add_argument('-v', '--verbose', action='count', help='verbose output, add multiple for more info', default=0)
    args = parser.parse_args()
    
    input_file = args.input
    if args.output and args.output is not '':
        output_file = args.output
    else:
        output_file = '_altfix.gpx'.join(input_file.split('.gpx', 1))
    
    api_key = None    
    if args.api_key:
        api_key = args.api_key
    elif 'NLS_API_KEY' in os.environ:
        # Read api key frome environment variable
        api_key = os.environ['NLS_API_KEY']
    else:
		# Read api key from file
        try:
            with open('api_key') as f:
                api_key = f.read()
            api_key = api_key.strip()
        except:
            api_key = None
            
    if not api_key:
        print("Warning! No api key provided, cannot download new tiles.")
        print("Can only use the tiles already downloaded to cache.")
        print()
        
    if args.verbose > 0:
        print("Input file:", input_file)
        print("Output file:", output_file)
        if args.verbose > 1:
            print("Api key:", api_key)     
        
    cache = TileCache(api_key=api_key, verbose=args.verbose)

    try:
        gpx = gpxpy.parse(open(input_file))
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    new_alt = cache.altitude(point.latitude, point.longitude)
                    # Replace the altitude with the new value
                    if new_alt:
                        point.elevation = new_alt
    except IOError:
        print("Error! Could not open input file:", input_file)
        sys.exit(-1)


    # Write to file
    try:
        with open(output_file, 'w') as output_f:
            output_f.write(gpx.to_xml())
    except IOError:
        print("Error while writing output file:", output_file)
        print("Disk full or write protected?")
        sys.exit(-1)


if __name__ == '__main__':
    fix_gpx_file()
