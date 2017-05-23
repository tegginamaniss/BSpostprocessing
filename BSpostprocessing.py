#!/usr/bin/env python2
'''A script to calculate a bunch of statistics and make nice graphs'''

import itertools
import numpy
import plot_functions

from data_reducer import DataReducer
from logreader import parse_logfile
from tools import m2nm, nm2m, rad2deg, deg2rad, normalized


def create_position_vector(acft):
    '''Create an array of x,y coordinates'''
    return numpy.column_stack((acft.column('posx'),
                               acft.column('posy')))


def create_velocity_vector(acft):
    '''Create an array of Vx,Vy coordinates'''

    tas = acft.column('tas')
    psi = acft.column('psi')

    Vx = tas * numpy.cos(psi)
    Vy = tas * numpy.sin(psi)

    return numpy.column_stack((Vx, Vy))


def create_sel_velocity_vector(acft):
    '''Create an array of commanded Vx,Vy coordinates'''

    sel_spd = acft.column('sel_spd')
    sel_hdg = acft.column('sel_hdg')

    Vx_sel = sel_spd * numpy.cos(sel_hdg)
    Vy_sel = sel_spd * numpy.sin(sel_hdg)

    return numpy.column_stack((Vx_sel, Vy_sel))


def calculate_relative_position(acft1, acft2):
    '''Calculate the relative position of acft2 wrt acft1'''
    pos_acft1 = create_position_vector(acft1)
    pos_acft2 = create_position_vector(acft2)

    rel_pos = pos_acft2 - pos_acft1

    return rel_pos


def calculate_relative_velocity(acft1, acft2):
    '''Calculate the relative velocity of acft2 wrt acft1'''
    vel_acft1 = create_velocity_vector(acft1)
    vel_acft2 = create_velocity_vector(acft2)

    rel_vel = vel_acft1 - vel_acft2

    return rel_vel


def calculate_distance(acft1, acft2):
    '''Calculate the distance between both aircraft'''

    rel_pos = calculate_relative_position(acft1, acft2)

    # Calculate the distance at each step by taking the norm of the
    # relative position
    distance = numpy.array([numpy.linalg.norm(position)
                            for position in rel_pos])

    return distance


def calculate_future_cpa(acft1, acft2):
    rel_pos = calculate_relative_position(acft1, acft2)
    rel_vel = calculate_relative_velocity(acft1, acft2)

    norm_vel = normalized(rel_vel)

    # Calculate the CPA vector
    future_cpa = numpy.array([numpy.linalg.norm(relpos - numpy.dot(relpos, normvel) * normvel)
                              for relpos, normvel in zip(rel_pos, norm_vel)])
    # for p in future_cpa:
    #     print m2nm(p)
    return future_cpa


def calculate_path_deviation(acft):
    '''Calculate the perpendicular offset from the original trajectory'''
    pos = create_position_vector(acft)

    x0 = pos[0, :]

    n_vel = normalized(create_velocity_vector(acft))[0, :]

    path_deviation = numpy.array([numpy.linalg.norm((x0 - x) - numpy.dot((x0 - x), n_vel) * n_vel)
                                  for x in pos])

    return path_deviation


def collect_stats(aircraft):
    '''Get the basic set of data required for further calculations'''
    statistics = []

    for (acft1, acft2) in itertools.combinations(aircraft, 2):
        print('Calculating stats for {} and {}'
              .format(acft1.callsign, acft2.callsign))

        pair_stats = {}

        pair_stats['acft1'] = acft1
        pair_stats['acft2'] = acft2

        pair_stats['distance'] = calculate_distance(acft1, acft2)
        pair_stats['cpa'] = calculate_future_cpa(acft1, acft2)

        statistics.append(pair_stats)

    print 'I have {} pairs'.format(len(statistics))

    return statistics


def check_actual_los(statistics, pz_radius):
    '''Check which pairs get into a LOS'''

    los_collection = [{'acft1': pair['acft1'].callsign,
                       'acft2': pair['acft2'].callsign,
                       'time': pair['acft1'].column('t')[pair['distance'] < pz_radius],
                       'cpa': pair['distance'].min()}
                      for pair in statistics
                      if (pair['distance'] < pz_radius).any()]

    print

    for los in los_collection:
        print '{ac1} and {ac2} in LOS from {t0} s \tto {t1} s\t, minimum distance: {cpa}'.format(
            ac1=los['acft1'], ac2=los['acft2'],
            t0=los['time'][0], t1=los['time'][-1],
            cpa=m2nm(los['cpa']))

    return los_collection


def check_conflicts(statistics, pz_radius):
    '''Check for conflicts between aircraft pairs'''

    conflict_collection = [{'acft1': pair['acft1'].callsign,
                            'acft2': pair['acft2'].callsign,
                            'time': pair['acft1'].column('t')[pair['cpa'] < pz_radius],
                            'cpa': pair['cpa'].min()}
                           for pair in statistics
                           if (pair['cpa'] < pz_radius).any()]

    print
    for conflict in conflict_collection:
        print '{ac1} and {ac2} in conflict from {t0} s \tto {t1} s\t, minimum distance: {cpa}'.format(
            ac1=conflict['acft1'], ac2=conflict['acft2'],
            t0=conflict['time'][0], t1=conflict['time'][-1],
            cpa=m2nm(conflict['cpa']))

    return conflict_collection


def check_relevant_pairs(statistics, cutoff):
    '''Check which pairs are close enough to each other to be relevant'''

    relevant_pairs = [pair for pair in statistics if (pair['distance'].min() < cutoff)]

    print 'I have {} relevant pairs'.format(len(relevant_pairs))

    return relevant_pairs


def has_overlap(pair1, pair2, cutoff):
    '''Check if there is overlap in two pairs'''
    return ((pair1['distance'] < cutoff) & (pair2['distance'] < cutoff)).any()


def group_pairs(relevant_pairs, cutoff):
    '''Group pairs that belong together'''

    # Create a copy that we can play with
    the_pairs = list(relevant_pairs)

    print 'Grouping, starting with {} pairs'.format(len(the_pairs))

    groups = []

    while the_pairs:
        group = []

        first_pair = the_pairs.pop(0)
        group.append(first_pair)

        # Loop over a copy of the pairs
        for pair in the_pairs[:]:

            if first_pair['acft1'] == pair['acft1'] and has_overlap(first_pair, pair, cutoff):

                the_pairs.remove(pair)
                group.append(pair)

            elif first_pair['acft2'] == pair['acft1'] and has_overlap(first_pair, pair, cutoff):

                the_pairs.remove(pair)
                group.append(pair)

        groups.append(group)

    print
    print 'Found {} groups'.format(len(groups))
    print
    for idx, group in enumerate(groups):
        print 'Group {}'.format(idx + 1)
        for pair in group:
            print '{} and {}'.format(pair['acft1'].callsign, pair['acft2'].callsign)

    return groups


def write_groups(groups, aircraft):
    '''Write an xml file for each group'''

    data_reducer = DataReducer(aircraft)

    for idx, group in enumerate(groups):
        callsigns = []
        for pair in group:
            callsigns.append(pair['acft1'].callsign)
            callsigns.append(pair['acft2'].callsign)

        # Only keep unique callsigns
        callsigns = list(set(callsigns))

        t_begin = group[0]['acft1'].t(0)
        t_end = group[0]['acft1'].t(-1)
        stride = 10

        reduction_parameters = {
            'callsigns': callsigns,
            't_begin': t_begin,
            't_end': t_end,
            'stride': stride}

        print
        data_reducer.write_data(reduction_parameters, 'output/group' + str(idx + 1) + '.xml')


def clamp_heading(hdg):
    '''Return a heading between -180 and 180 degrees'''
    while hdg > deg2rad(180.):
        hdg -= deg2rad(360.)

    while hdg < deg2rad(-180.):
        hdg += deg2rad(360.)

    return hdg


def calculate_largest_cmd_change(acft):
    '''Find the largest change in heading and speed'''

    spd_cmd = acft.column('sel_spd')
    hdg_cmd = acft.column('sel_hdg')

    initial_spd_cmd = spd_cmd[0]
    initial_hdg_cmd = hdg_cmd[0]

    spd_cmd -= initial_spd_cmd
    hdg_cmd = [clamp_heading(hdg - initial_hdg_cmd) for hdg in hdg_cmd]

    spd_change = numpy.absolute(spd_cmd).max()
    hdg_change = numpy.absolute(hdg_cmd).max()

    return (spd_change, hdg_change)


def calculate_largest_cmd_state_change(acft):
    '''Find the largest change in commanded state'''

    spd_cmd = acft.column('sel_spd')
    hdg_cmd = acft.column('sel_hdg')

    sel_vel = create_sel_velocity_vector(acft)

    tmp = numpy.array(sel_vel)

    initial_sel_vel = sel_vel[0]

    sel_vel -= initial_sel_vel

    state_change = numpy.array([numpy.linalg.norm(vel) for vel in sel_vel]).max()

    return state_change


def per_aircraft_calculations(aircraft):
    '''Calculate stuff for each acft'''

    path_deviation = []
    cmd_change = []
    state_change = []

    for acft in aircraft:
        path = calculate_path_deviation(acft)
        cmd = calculate_largest_cmd_change(acft)
        state = calculate_largest_cmd_state_change(acft)

        print '{} : cmd={} state={}'.format(acft.callsign, cmd, state)

        path_deviation.append(path)
        cmd_change.append(cmd)
        state_change.append(state)

    do_plot = True

    if do_plot:
        plot_functions.plot_path_deviation(path_deviation)
        plot_functions.plot_largest_cmd_change(cmd_change)
        # plot_functions.plot_largest_cmd_state_change(state_change)


def calculate_stats(aircraft):
    '''Function that dispatches all stats calculations'''

    per_aircraft_calculations(aircraft)
    print

    statistics = collect_stats(aircraft)

    relevant_pairs = check_relevant_pairs(statistics, nm2m(20.0))

    # groups = group_pairs(relevant_pairs,nm2m(20.0))

    # write_groups(groups, aircraft)


    los_data = check_actual_los(relevant_pairs, nm2m(5.0))
    conflict_data = check_conflicts(relevant_pairs, nm2m(5.0))

    do_plot = True

    if do_plot:
        plot_functions.plot_los(los_data)
        plot_functions.plot_los_time(los_data)

        # plot_functions.plot_conflicts(conflict_data)
        plot_functions.plot_conflicts_time(conflict_data)
        plot_functions.show()


def main():
    '''Entry point for this application when it's run as a script'''

    # Check if we started with the correct arguemnts (either none or one)
    n_args = len(sys.argv)

    if n_args == 1:
        filename = 'input.txt'
    elif n_args == 2:
        filename = sys.argv[1]
    else:
        print('Too many arguments provided!')
        sys.exit(1)

    # Read the data and calculate the stats
    aircraft = parse_logfile(filename)

    calculate_stats(aircraft)


if __name__ == '__main__':
    import sys

    sys.exit(main())
