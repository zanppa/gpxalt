# -*- coding: utf-8 -*-
"""
Created on Sat Jun 23 14:09:59 2018

@author: Raksunaksu
"""

import coordinates.coordinates as coord
import tifffile.tifffile as tiff

import numpy  # Geotiff is converted to numpy array
import urllib # For downloading files over http

import math

# According to  http://www.jhs-suositukset.fi/c/document_library/get_file?folderId=43384&name=DLFE-1012.pdf
# and http://www.jhs-suositukset.fi/c/document_library/get_file?folderId=43384&name=DLFE-1006.pdf

NLS_2M_PATH = 'https://tiedostopalvelu.maanmittauslaitos.fi/tp/tilauslataus/tuotteet/korkeusmalli/hila_2m/etrs-tm35fin-n2000/'
NLS_10M_PATH = 'https://tiedostopalvelu.maanmittauslaitos.fi/tp/tilauslataus/tuotteet/korkeusmalli/hila_10m/etrs-tm35fin-n2000/'


scale500E = 192000 # 1:500000 lehdet are 192 km in east-west
scale500N = 92000  # 1:500000 lehdet are 92 km in north-south
letters500 = ['K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']
letters025 = ['A', 'C', 'E', 'G', 'B', 'D', 'F', 'H']


def etrs_tile(coords, scale):
    """Convert given ETRS-TM35FIN coordinates to a tile
    name and number, and also return x and y coordinates inside that tile
    
    Inputs:
    coords -- meter coordinates in a dict format {"type":xx, "N":xx, "Y":xx}, from coordinates.py
    scale -- scale in 1:XXXX where XXXX is 200000, 100000, 50000, 25000, 10000 or 5000

    Returns:
    tuple of format (tile, X, Y)
    """
    
    # Allowed scales, 1:200000, 1:100000 etc
    scales = [200000, 100000, 50000, 25000, 10000, 5000]
    
    if coords['type'] != coord.COORD_TYPE_ETRSTM35FIN:
        print "Wrong coordinate type, must be ETRS-TM35FIN"
        return None 
    if not scale in scales:
        print "Scale not allowed"
        return None

    # Assert coordinate region E: 20000m ... 788000m, N: 6570000m ... 7818000m
    if coords['E'] < 20000:
        print "Coordinate out of bounds to west"
        return None
    if coords['E'] > 788000:
        print "Coordinate out of bounds to east"
        return None
    if coords['N'] < 6570000:
        print "Coordinate out of bounds to south"
        return None
    if coords['N'] > 7818000:
        print "Coordinate out of bounds to north"
        return None

    # 1:500000 leaf
    # 27 degrees east (center) is 500000m, however the westmost leaf starts at -76000 meters
    # however it is only half leaf...
    # leafs are 192000m in east-west and 92000m in north-south
    east = coords['E'] + 76000.0
    east_base = int(math.floor(east / 192000.0))
    north = coords['N'] - 6570000.0 
    north_base = int(math.floor(north / 96000.0))
    tile = str(letters500[north_base]) + str(east_base + 2)

    #print "200000: ", east, east_base, north, north_base

    east_base *= 192000.0
    east -= east_base
    north_base *= 96000.0
    north -= north_base

    if scale == 200000:
        return (tile, east, north)

    # 1:100000 divides previous in four parts
    #  2  |  4
    #-----------
    #  1  |  3

    if east < 96000:
        add = 1
    else:
        add = 3
        east -= 96000
    if north >= 48000:
        add += 1
        north -= 48000

    tile += str(add)

    #print "100000: ", add, east, north

    if scale == 100000:
        return (tile, east, north)

    # 1:50000 further divides in similar way
    if east < 48000:
        add = 1
    else:
        add = 3
        east -= 48000
    if north > 24000:
        add += 1
        north -= 24000

    tile += str(add)

    #print "50000: ", add, east, north

    if scale == 50000:
        return (tile, east, north)


    # 1:25000 further divides in similar way
    if east < 24000:
        add = 1
    else:
        add = 3
        east -= 24000
    if north > 12000:
        add += 1
        north -= 12000

    tile += str(add)

    #print "25000: ", add, east, north

    if scale == 25000:
        return (tile, east, north)
        
    # 1:10000 is after division by 8, denoted by letters:
    #  B D F H
    #  A C E G
    if north > 6000:
        add = 4
        north -= 6000
    else:
        add = 0
    
    east_base = int(math.floor(east / 6000.0))
    add += east_base
    east -= east_base * 6000.0
    tile += str(letters025[int(add)])    
    
    #print "10000: ", add, east_base, east, north
    
    if scale == 10000:
        return (tile, east, north)
        
    
    # Last 1:5000 is after division to four parts
    #   2 | 4
    #  ---+--
    #   1 | 3
    
    if north >= 3000:
        add = 2
        north -= 3000
    else:
        add = 1
    if east >= 3000:
        add += 2
        east -= 3000
        
    tile += str(add)
    return (tile, east, north)



class TileCache:
    global NLS_2M_PATH
    global NLS_10M_PATH
    
    root_path = '.\\cache\\'
    api_key = None
    http_path_2m = NLS_2M_PATH
    http_path_10m = NLS_10M_PATH
    verbose = 0    
    
    last_x = 0  # X and Y on current leaf
    last_y = 0      
    last_tile_name = None
    last_global_x = 0   # X and Y in meters, global coordinates
    last_global_y = 0
    
    cache = {}
    
    def __init__(self, root=None, api_key=None, verbose=0):
        if root is not None:
            self.root_path = root
        self.http_path = self.http_path_2m
        
        if api_key:
            self.api_key = api_key
            
        self.verbose = verbose

        if verbose > 0:
            print "Cache path", self.root_path

    
    def altitude(self, N, E):
        """Get altitude at given N and E in WGS84 coordinates.
        Tries to return data from 2m grid, but if that fails,
        returns 10m grid data."""
        
        # First try to get 2m altitude
        alt = self.__get_altitude(N, E, scale=2)

        # If not found, try to get 10m altitude
        if not alt:
            alt = self.__get_altitude(N, E, scale=10)

        return alt


    def last_coords(self):
        """Return previous X and Y coordinates in the tile"""
        return (self.last_x, self.last_y)

    def last_tile(self):
        """Returns the name of the last used tile"""
        return self.last_tile_name

    def last_global_coords(self):
        """Returns the previous global (ETRS-TM35FIN) coordinates"""
        return (self.last_global_x, self.last_global_y)


    def __get_altitude(self, N, E, scale=2):
        """Convert N and E from WGS84 to ETRS-TM35FIN and get the
        tile name and coordinates inside the tile.
        Then try to load the tile from cache (disk) or from online.
        If succesfull, reads the altitude at the given point."""
        
        if scale == 2:  # 2m grid
            scale = 10000       # 2m grid is 1:10000
            self.http_path = self.http_path_2m
        else:   # 10m grid
            scale = 25000       # 10m grid is in 1:25000
            self.http_path = self.http_path_10m

        # Convert lat (N) and lon (E) from WGS84 to ETRS-TM35FIN for correct coordinates
        latlon = {'type':coord.COORD_TYPE_WGS84, 'N':N, 'E':E}
        local_coords = coord.Translate(latlon, coord.COORD_TYPE_ETRSTM35FIN)
        self.last_global_x = local_coords['E'] + 76000.0
        self.last_global_y = local_coords['N'] - 6570000.0

        if self.verbose > 2:
            print latlon['N'], latlon['E'], "(lat, lon) -->", self.last_global_y, self.last_global_x, " (N, E)"

        # Get the correct map leaf and coordinates inside it
        (tile, x, y) = etrs_tile(local_coords, scale)     # Geotiff is at 1:10000 level
        self.last_tile_name = tile
        #print tile, x, y

        # Scale to nearest pixel 
        # TODO: could also do some filtering, but not yet
        if scale == 10000:
            x = int(math.floor(x / 2.0)) # 2 meters / pixel
            y = int(math.floor(y / 2.0)) # 2 meters / pixel
            #print x, y
        else:
            x = int(math.floor(x / 10.0)) # 2 meters / pixel
            y = int(math.floor(y / 10.0)) # 2 meters / pixel

        self.last_x = x
        self.last_y = y

        # First check if we have the map in cache?
        if self.cache.has_key(tile):
            # Use the cached tile directly and return the altitude

            # See if we already tried downloading this and failed
            if self.cache[tile] is None:
                return None

            # Check the array dimensions (corrupted files?)
            if x >= self.cache[tile].shape[0] or y >= self.cache[tile].shape[1]:
                print "Corrupted tile", tile, "in cache or coordinate error!"
                return None

            return self.cache[tile][y][x]

        # If not in cache, try to read local file
        if self.__read_local(tile):
            return self.cache[tile][y][x]

        # Try to read remote file (i.e. load from net to disk, then read that)
        # Only if api key is provided we try to download anything
        # TODO: Tries to re-download the file also if it was erroneous
        if self.api_key and self.__read_remote(tile):
            return self.cache[tile][y][x]

        # Mark the tile as None so we don't try to re-download it anymore
        self.cache[tile] = None
            
        return None


    def __read_local(self, tile):
        """Read a locally cached GeoTIFF altitude map"""
        
        local_file = self.root_path + tile + '.tif'
        if self.verbose > 0:
            print "Reading local tile", tile
        if self.verbose > 1:
            print " from", local_file
    
        try:
            tif = tiff.imread(local_file)
            #print tif.shape

        except ValueError as e:
            print 'Local file error {0}'.format(e.message)
            return False

        except:
            # File was not found!
            print 'Unexpected error while reading local file!'
            return False

        # File loaded succesfully, add to cache
        # Y-axis needs to be inverted so that values increase to north
        self.cache[tile] = numpy.flip(tif, axis=0)
        
        return True
        
        
    def __read_remote(self, tile):
        """Load a remote GeoTIFF altitude map file and cache it locally."""
        remote_file = self.http_path + tile[:2] + '/' + tile[:3] + '/' + tile + '.tif'
        if self.api_key:
            remote_file += '?api_key=' + self.api_key

        local_file = self.root_path + tile + '.tif'

        if self.verbose > 0:
            print "Loading remote tile", tile
        if self.verbose > 1:
            print " from", remote_file
        
        try:
            urllib.urlretrieve(remote_file, filename=local_file)
        except:
            print 'Error while retrieving remote tile'
            return False
            
        # If succesfully downloaded remote file to local cache, try to read it
        return self.__read_local(tile)

