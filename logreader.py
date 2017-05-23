'''Read the logdata from a csv file into an aircraft structure'''

import csv
import numpy as np
from acfttrace import AircraftTrace
import math


def _strip_header(logfile):
    '''Remove the preamble from the file'''
    # Skip the first line, it is generic comment
    logfile.next()

    # The next line has the headings
    heading_string = logfile.next().strip('#')
    headings = heading_string.split()
    return headings


def wgs84_to_ecef(lla, unit="rad"):
    """Converts coordinates (altitude, latitude, longitude) in WGS84 to 
    coordinates (x,y,z) in the ECEF reference frame.
    """

    # Data from the WGS84 model
    a = 6378137.0
    finv = 298.257223563

    # Data from array
    lat = lla[0]
    lon = lla[1]
    h = lla[2]

    # Unit conversion
    unit = unit.lower()
    if unit == "deg":
        lat = math.radians(lat)
        lon = math.radians(lon)

    # Intermediate stuff
    b = a * (1 - 1 / finv)
    psi = math.atan(math.tan(lat) * b / a)  # Magically works at the singularities!
    r = a * math.cos(psi) + h * math.cos(lat)

    x = r * math.cos(lon)
    y = r * math.sin(lon)
    z = b * math.sin(psi) + h * math.sin(lat)

    return np.array([[x], [y], [z]])


def _parse_aircraft_data(logfile, headings, fname):
    '''Convert the data into an aircraft structure'''

    # Loop through all the lines in the csv file and append the states
    # to the correct aircraft
    csvreader = csv.reader(logfile)

    hlen = len(headings)
    callsigns = []
    data = []
    for row in csvreader:
        if not hlen == len(row):
            break
        callsigns.append(row[1])
        data.append(row)
    callsigns = sorted(list(set(callsigns)))  # remove duplicates and sort alpha-numerically
    acids = {key: value for (value, key) in enumerate(callsigns)}

    # Create a new list of aircraft based on the callsigns
    aircraft = [AircraftTrace(callsign) for callsign in callsigns]

    for r in data:
        pos = wgs84_to_ecef((float(r[3]), float(r[4]), float(r[5])), unit="deg")

        posx, posy, posz = pos[0][0], pos[1][0], pos[2][0]
        callsign, time, psi, tas, cas, sel_hdg, sel_spd = r[1], float(r[0]), float(r[7]), float(r[9]), float(r[13]),\
                                                         float(r[8]), float(r[9])

        acft_id = acids[callsign]
        # Unwanted stuff
        scenario, nd_range, nd_mode = fname, int(40), int(3)
        state = [float(posx), float(posy), float(posz), psi, tas, cas, sel_hdg, sel_spd, nd_range, nd_mode]

        aircraft[acft_id].addDataPoint(time, state)

    for acft in aircraft:
        acft.finalize()

    return aircraft


def parse_logfile(fname):
    '''Parse the file and return a list of aircraft'''
    filename = 'logs/' + fname
    logfile = open(filename, 'r')

    headings = _strip_header(logfile)
    aircraft = _parse_aircraft_data(logfile, headings, fname)

    return aircraft


def main():
    '''Entry point when running as a script'''

    # Check if we started with the correct arguments (either none or one)
    n_args = len(sys.argv)

    if n_args == 1:
        filename = 'input.txt'
    elif n_args == 2:
        filename = sys.argv[1]
    else:
        print('Too many arguments provided!')
        return 1
    aircraft = parse_logfile(filename)

    for acft in aircraft:
        print(acft.callsign)
        # print(acft.column('posx').shape)
    # print(acft.column('posx').shape)

if __name__ == '__main__':
    import sys
    sys.exit(main())
