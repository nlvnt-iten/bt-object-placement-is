from math import pi, tan, log, sinh, atan

import presentation.config.constants as pconstants

def latlon_to_pixel(lat, lon, z):
    w = pconstants.TILE_SIZE * 2**z
    x = (lon + 180) / 360 * w
    y = (1 - (log(tan(pi/4 + (lat*pi/180)/2)) / pi)) / 2 * w
    return x, y

def pixel_to_latlon(px, py, z):
    w = pconstants.TILE_SIZE * 2**z
    lon = 360 * px / w - 180
    n   = pi - 2*pi*py / w
    lat = atan(sinh(n)) * 180 / pi
    return lat, lon