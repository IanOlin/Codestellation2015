#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
# Library to extract Exif information from digital camera image files.
# https://github.com/ianare/exif-py
#
#
# Copyright (c) 2002-2007 Gene Cash
# Copyright (c) 2007-2014 Ianaré Sévi and contributors
#
# See LICENSE.txt file for licensing information
# See CHANGES.txt file for all contributors and changes
#

"""
Runs Exif tag extraction in command line.
"""

import sys
import getopt
import logging
import timeit
from exifread.tags import DEFAULT_STOP_TAG, FIELD_TYPES
from exifread import process_file, exif_log, __version__, Ratio

logger = exif_log.get_logger()


def usage(exit_status):
    """Show command line usage."""
    msg = ('Usage: EXIF.py [OPTIONS] file1 [file2 ...]\n'
           'Extract EXIF information from digital camera image files.\n\nOptions:\n'
           '-h --help               Display usage information and exit.\n'
           '-v --version            Display version information and exit.\n'
           '-q --quick              Do not process MakerNotes.\n'
           '-t TAG --stop-tag TAG   Stop processing when this tag is retrieved.\n'
           '-s --strict             Run in strict mode (stop on errors).\n'
           '-d --debug              Run in debug mode (display extra info).\n'
           '-c --color              Output in color (only works with debug on POSIX).\n'
    )
    print(msg)
    sys.exit(exit_status)


def show_version():
    """Show the program version."""
    print('Version %s on Python%s' % (__version__, sys.version_info[0]))
    sys.exit(0)


def main1():
    """Parse command line options/arguments and execute."""
    try:
        arg_names = ["help", "version", "quick", "strict", "debug", "stop-tag="]
        opts, args = getopt.getopt(sys.argv[1:], "hvqsdct:v", arg_names)
    except getopt.GetoptError:
        usage(2)

    detailed = True
    stop_tag = DEFAULT_STOP_TAG
    debug = False
    strict = False
    color = False

    for option, arg in opts:
        if option in ("-h", "--help"):
            usage(0)
        if option in ("-v", "--version"):
            show_version()
        if option in ("-q", "--quick"):
            detailed = False
        if option in ("-t", "--stop-tag"):
            stop_tag = arg
        if option in ("-s", "--strict"):
            strict = True
        if option in ("-d", "--debug"):
            debug = True
        if option in ("-c", "--color"):
            color = True

    if not args:
        usage(2)

    exif_log.setup_logger(debug, color)

    coords = []

    # output info for each file
    for filename in args:
        file_start = timeit.default_timer()
        try:
            img_file = open(str(filename), 'rb')
        except IOError:
            logger.error("'%s' is unreadable", filename)
            continue
        #logger.info("Opening: %s", filename)

        tag_start = timeit.default_timer()

        # get the tags
        data = process_file(img_file, stop_tag=stop_tag, details=detailed, strict=strict, debug=debug)

        tag_stop = timeit.default_timer()

        #for x in data:
        #    print x
        #    print data[x]
        #    print '\n'
        if not data:
            logger.warning("No EXIF information found\n")
            continue

        if 'JPEGThumbnail' in data:
            #logger.info('File has JPEG thumbnail')
            del data['JPEGThumbnail']
        if 'TIFFThumbnail' in data:
            logger.info('File has TIFF thumbnail')
            del data['TIFFThumbnail']

        tag_keys = (data.keys())
        tag_keys.sort()

        #for i in tag_keys:
        #    try:
        #        logger.info('%s (%s): %s', i, FIELD_TYPES[data[i].field_type][2], data[i].printable)
        #    except:
        #        logger.error("%s : %s", i, str(data[i]))

        file_stop = timeit.default_timer()

        logger.debug("Tags processed in %s seconds", tag_stop - tag_start)
        logger.debug("File processed in %s seconds", file_stop - file_start)
        #print("")

        coords.append((data['GPS GPSLatitude'], data['GPS GPSLongitude']))


    #The minimum and maximum coordinates
    xdist = []
    ydist = []
    xcenter = []
    ycenter = []
    xcoords = []
    ycoords = []

    #each element of coords is separated into separate s of longitude and latitudes
    for elements in coords:
        tempcoords = elements
        print tempcoords
        #print type(elements[0])
        xcoords.append(tempcoords[0])
        ycoords.append(tempcoords[1])

    def ratioVal(x):
        return float(x.num)/x.den

    def convertSecs(latOrLong):
        return latOrLong[0]*3600 + latOrLong[1]*60 + latOrLong[2]
    def convertSecsInstance(latOrLong):
        return ratioVal(latOrLong[0])*3600 + ratioVal(latOrLong[1])*60 + ratioVal(latOrLong[2])

    def renormalizeVals(latOrLong):
        val = latOrLong
        if (val[2].num<0) != (val[2].den<0):
            newNum = abs(val[2].den) - abs(val[2].num) #1+(-numerator)
            newNumPrev = val[1].num - val[1].den #numerator - 1
            val[2] = Ratio(newNum, abs(val[2].den))
            val[1] = Ratio(newNumPrev, val[1].den)
        elif (ratioVal(val[2])>=60):
            num1 = val[2].num
            den1 = val[2].den
            val[2] = Ratio(num1%(60*den1), den1)
            val[1] = Ratio((num1/(60*den1))*val[1].den + val[1].num*den1, den1*val[1].den)
        if (val[1].num<0) != (val[1].den<0):
            newNum = abs(val[1].den) - abs(val[1].num) #1+(-numerator)
            newNumPrev = val[0].num - val[0].den #numerator - 1
            val[1] = Ratio(newNum, abs(val[1].den))
            val[0] = Ratio(newNumPrev, val[0].den)
        elif (ratioVal(val[1])>=60):
            num1 = val[1].num
            den1 = val[1].den
            val[1] = Ratio(num1%(60*den1), den1)
            val[0] = Ratio((num1/(60*den1))*val[0].den + val[0].num*den1, den1*val[0].den)
        return val

    def minima(coordArr):
        ymin = coordArr[0].values
        for min_y_element in coordArr:
            min_y_elements = min_y_element.values
            if ratioVal(min_y_elements[0]) < ratioVal(ymin[0]):
                ymin = min_y_elements
            elif ratioVal(min_y_elements[0]) == ratioVal(ymin[0]):
                if ratioVal(min_y_elements[1]) < ratioVal(ymin[1]):
                    ymin = min_y_elements
                elif ratioVal(min_y_elements[1]) == ratioVal(ymin[1]):
                    if ratioVal(min_y_elements[2]) < ratioVal(ymin[2]):
                        ymin = min_y_elements
        return ymin


    def maxima(coordArr):
        xmax = coordArr[0].values
        for max_x_element in coordArr:
            max_x_elements = max_x_element.values
            if ratioVal(max_x_elements[0]) > ratioVal(xmax[0]):
                xmax = max_x_elements
            elif ratioVal(max_x_elements[0]) == ratioVal(xmax[0]):
                if ratioVal(max_x_elements[1]) > ratioVal(xmax[1]):
                    xmax = max_x_elements
                elif ratioVal(max_x_elements[1]) == ratioVal(xmax[1]):
                    if ratioVal(max_x_elements[2]) > ratioVal(xmax[2]):
                        xmax =  max_x_elements
        return xmax

    #arbitrary assignments for for loop sorting
    xmin = minima(xcoords)
    xmax = maxima(xcoords)
    ymin = minima(ycoords)
    ymax = maxima(ycoords)



    # print type(xmin)
    # print xmin
    # print xmin[0].__class__
    # print xmin[0].num
    print ''
    #DOING TEH MAD MATHZ FOR T3H DISTANCE...DAWG
    for x in range(3):
        xdist.append(ratioVal(xmax[x]) - ratioVal(xmin[x]))
    for y in range(3):
        ydist.append(ratioVal(ymax[y]) - ratioVal(ymin[y]))

    #DOING MORE OF DE MAD MATHZ...HOMEDAWG
    for x2 in range(3):
        xcenter.append(ratioVal(xmin[x2]) + xdist[x2]/2)
    for y2 in range (3):
        ycenter.append(ratioVal(ymin[y2]) + ydist[y2]/2)

    # normalize axes for coordinates
    print 'Top left corner of the square to print out'
    #calculate the seconds in the distances, for comparison
    xdist1 = convertSecs(xdist)
    ydist1 = convertSecs(ydist)
    length = xdist1 if xdist1 > ydist1 else ydist1
    border = length/10
    tlLat = [xmin[0], xmin[1], Ratio(xmin[2].num - xmin[2].den*border, xmin[2].den)]
    tlLat = renormalizeVals(tlLat)

    tlLong = [ymin[0], ymin[1], Ratio(ymin[2].num - ymin[2].den*border, ymin[2].den)]
    tlLong = renormalizeVals(tlLong)

    print 'latitude: ', tlLat
    print 'longitude: ', tlLong

    print ''
    print 'Bottom right corner of the square to print out'

    brLat = [xmin[0], xmin[1], Ratio(xmin[2].num + xmin[2].den*border*2 + length*xmin[2].den, xmin[2].den)]
    brLat = renormalizeVals(brLat)

    brLong = [ymin[0], ymin[1], Ratio(ymin[2].num + ymin[2].den*border*2 + length*ymin[2].den, ymin[2].den)]
    brLong = renormalizeVals(brLong)

    print 'latitude: ', brLat
    print 'longitude: ', brLong

    print ''

    print 'Edge len in secs', length+border*2

    print ''

    xminsec = convertSecsInstance(tlLat)
    yminsec = convertSecsInstance(tlLong)
    for elements in coords:
        print 'Normalized Coordinate: x, y'
        print (convertSecsInstance(elements[0].values)-xminsec)/(length+border*2)
        print (convertSecsInstance(elements[1].values)-yminsec)/(length+border*2)
        print ''




    #not yet returning the list of coordinates
    masta = [xdist, ydist, xcenter, ycenter]

    return masta

if __name__ == '__main__':
    masta = main1()
    #print masta
