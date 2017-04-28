'''Tools to write aircraft data into an xml format for MVIEW '''

import time
import xml.etree.ElementTree as et

from tools import m2nm, nm2m, ms2kts, m2ft, rad2deg, BoundingBox

exit_waypoint = { 'name':'dummy', 'xcoord':0.0, 'ycoord':0.0 }

def _write_date_time(parent_node):
    '''Write time and date'''
    timestring = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    et.SubElement(parent_node, 'date_time').text = timestring

def _write_subject(parent_node):
    ''' Write a dummy subject name'''
    et.SubElement(parent_node, 'subject').text = 'John Doe'

def _write_file(parent_node):
    '''Write a dummy file name'''
    et.SubElement(parent_node, 'file').text = 'Fubar'


def _write_settings(parent_node):
    '''Write some generic settnings'''
    settings_node = et.SubElement(parent_node,'settings')
    et.SubElement(settings_node, 'rotation').text = '0.0'

def _add_point(parent_node, xcoord, ycoord, name=None):
    '''Add an individual point to a parent node'''

    point_node = et.SubElement(parent_node,'point')

    et.SubElement(point_node, 'x_nm').text = str(xcoord)
    et.SubElement(point_node, 'y_nm').text = str(ycoord)

    # Check if a name was provided, keep in mind that '' is also a valid name
    if not name == None:
        et.SubElement(point_node, 'name').text = name


def _write_sectors(parent_node, aircraft):
    '''Calculate the sector and write the data'''

    sectors_node = et.SubElement(parent_node,  'sectors')
    sector_node  = et.SubElement(sectors_node, 'sector')
    border_node  = et.SubElement(sector_node,  'border_points')

    # Calculate the area used by all planes
    boundingbox = BoundingBox(aircraft)

    # Add 5NM of padding
    boundingbox.pad(nm2m(40.0))
    (xmin, xmax, ymin, ymax) = boundingbox.extent()

    # Add the four corners of the bounding box (clockwise) as a sector
    # Convert from ned to xyz
    _add_point(border_node, m2nm(ymin), m2nm(xmin))
    _add_point(border_node, m2nm(ymin), m2nm(xmax))
    _add_point(border_node, m2nm(ymax), m2nm(xmax))
    _add_point(border_node, m2nm(ymax), m2nm(xmin))

def _add_source_sink(parent_node, name, xcoord, ycoord):
    '''Add an individual source_sink to the document'''

    source_sink_node = et.SubElement(parent_node, 'source_sink')

    _add_point(source_sink_node, xcoord, ycoord, name)

def _write_sources_sinks(parent_node, aircraft):
    '''Calculate the source and sink poits and write them to the document'''
    sources_sinks_node = et.SubElement(parent_node, 'sources_sinks')

    # Calculate the area used by all planes
    boundingbox = BoundingBox(aircraft)

    # Add 5NM of padding
    boundingbox.pad(nm2m(40.0))
    (xmin, xmax, ymin, ymax) = boundingbox.extent()

    # Put a source top right and sink bottom left
    # Convert from ned to xyz
    _add_source_sink(sources_sinks_node, 'DUMMY', m2nm(ymax), m2nm(xmax))
    _add_source_sink(sources_sinks_node, 'YMMUD', m2nm(ymin), m2nm(xmin))

    # Keep sink info for later use (keep in xyz)
    exit_waypoint['name']   = 'YMMUD'
    exit_waypoint['xcoord'] = ymin
    exit_waypoint['ycoord'] = xmin


def _write_airspace(parent_node, aircraft):
    '''Calculate bounding box and write airspace bounds'''
    airspace_node = et.SubElement(parent_node, 'airspace')

    _write_sectors(airspace_node, aircraft)
    _write_sources_sinks(airspace_node, aircraft)

def _add_initial_aircraft(parent_node, callsign, state):
    '''Add an initial aircraft block'''

    exit_name   = exit_waypoint['name']
    exit_xcoord = exit_waypoint['xcoord']
    exit_ycoord = exit_waypoint['ycoord']

    acft_node = et.SubElement(parent_node, 'aircraft')

    et.SubElement(acft_node, 'ACID').text        = callsign
    et.SubElement(acft_node, 'x_nm').text        = str(m2nm(state.posx))
    et.SubElement(acft_node, 'y_nm').text        = str(m2nm(state.posy))
    et.SubElement(acft_node, 'alt_ft').text      = str(m2ft(state.posz))
    et.SubElement(acft_node, 'hdg_deg').text     = str(rad2deg(state.psi))
    et.SubElement(acft_node, 'gam_deg').text     = '0.0'
    et.SubElement(acft_node, 'spd_kts').text     = str(ms2kts(state.tas))
    et.SubElement(acft_node, 'min_spd_kts').text = str(230.0)
    et.SubElement(acft_node, 'max_spd_kts').text = str( 425.0)
    et.SubElement(acft_node, 'COPX').text        = exit_name
    et.SubElement(acft_node, 'COPX_x_nm').text   = str(m2nm(exit_xcoord))
    et.SubElement(acft_node, 'COPX_y_nm').text   = str(m2nm(exit_ycoord))


def _add_aircraft(parent_node, callsign, state):
    '''Add one aircraft'''
    acft_node = et.SubElement(parent_node, 'aircraft')

    et.SubElement(acft_node, 'ACID').text           = callsign
    et.SubElement(acft_node, 'x_nm').text           = str(m2nm(state.posx))
    et.SubElement(acft_node, 'y_nm').text           = str(m2nm(state.posy))
    et.SubElement(acft_node, 'hdg_deg').text        = str(rad2deg(state.psi))
    et.SubElement(acft_node, 'spd_kts').text        = str(ms2kts(state.tas))
    et.SubElement(acft_node, 'selected').text       = 'false'
    et.SubElement(acft_node, 'speed_cmd').text      = str(ms2kts(state.sel_spd))
    et.SubElement(acft_node, 'track_cmd').text      =str(rad2deg(state.sel_hdg))
    et.SubElement(acft_node, 'conflict').text       = 'false'
    et.SubElement(acft_node, 'PZ_intrusion').text   =  'false'
    et.SubElement(acft_node, 'PZ_intrusion_nm').text= '-1.0'
    et.SubElement(acft_node, 'controlled').text     =  'true'


def _add_traffic(parent_node, aircraft_states, initial=False):
    '''Add the traffic data to a log point'''

    traffic_node = et.SubElement(parent_node, 'traffic')

    for (callsign, state) in aircraft_states:
        if initial:
            _add_initial_aircraft(traffic_node, callsign, state)
        else:
            _add_aircraft(traffic_node, callsign, state)

def _write_initial_traffic(parent_node, aircraft):
    '''Write the initial traffic node'''
    
    # Create a list of (callsign,state) tuples
    aircraft_states = [ (acft.callsign, acft.state(0)) for acft in aircraft ]

    # Use this list to create the traffic element
    _add_traffic(parent_node, aircraft_states, initial=True)

def _write_scenario(parent_node, aircraft):
    '''Create a scenario node'''

    scenario_node = et.SubElement(parent_node, 'scenario')

    _write_file(scenario_node)
    _write_settings(scenario_node)
    _write_airspace(scenario_node, aircraft)
    _write_initial_traffic(scenario_node, aircraft)


def _add_log_point(parent_node, timestamp, aircraft_states):
    '''Add an individual logpoint to the xml structure'''
    logpoint_node = et.SubElement(parent_node, 'logpoint')

    et.SubElement(logpoint_node, 'timestamp').text = str(timestamp)
    et.SubElement(logpoint_node, 'score').text     = '100.0'

    _add_traffic(logpoint_node, aircraft_states)

def _write_log_points(parent_node, aircraft):
    '''Loop through all the data points and add them to the xml structure'''
    n_logpoints = aircraft[0].n_points()

    for idx in range(n_logpoints):

        timestamp       = str( aircraft[0].t(idx) )
        aircraft_states = [(acft.callsign, acft.state(idx))
                           for acft in aircraft]

        _add_log_point(parent_node, timestamp, aircraft_states)

def _write_performance(node):
    '''Add a node with performance data to a node'''

    performance_node = et.SubElement(node, 'performance')

    et.SubElement(performance_node, 'average_score').text     = '100.0'
    et.SubElement(performance_node, 'SSD_inspections').text   = '0'
    et.SubElement(performance_node, 'speed_cmds').text        = '0'
    et.SubElement(performance_node, 'track_cmds').text        = '0'
    et.SubElement(performance_node, 'combined_cmds').text     = '0'
    et.SubElement(performance_node, 'veto').text              = 'false'
    et.SubElement(performance_node, 'conformal').text         = 'false'
    et.SubElement(performance_node, 'advisory_expired').text  = 'false'
    et.SubElement(performance_node, 'response_time_sec').text = '0'
    et.SubElement(performance_node, 'workload').text          = '50'
    et.SubElement(performance_node, 'CARS').text              = '0'
    et.SubElement(performance_node, 'midair_collision').text  = 'false'


def write_xml(aircraft, filename):
    '''Build the xml structure and write it to a file'''

    # Create the document root
    root = et.Element('record')

    # Add the nodes
    print('Creating Preamble')
    _write_date_time(root)
    _write_subject(root)
    _write_scenario(root, aircraft)
    print('Creating Logpoints')
    _write_log_points(root, aircraft)
    print('Creating Performance')
    _write_performance(root)

    print('Writing to: ' + filename)
    # Write to disk
    with open(filename, 'w') as xml_file:
        xml_file.write(et.tostring(root))


def main():
    '''Entry point when we run as a script'''

    import logreader

    # Check if we started with the correct arguemnts (either none or one)
    n_args = len(sys.argv)

    if n_args == 1:
        filename = 'input.txt'
    elif n_args == 2:
        filename = sys.argv[1]
    else:
        print 'Too many arguments provided!'
        return 1

    print 'Parsing: ' + filename

    # Grab the aircraft traces, and write to xml
    aircraft = logreader.parse_logfile(filename)

    write_xml(aircraft, 'test.xml')

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
