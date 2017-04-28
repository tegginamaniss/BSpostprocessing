'''A collection of functions to plot the data'''

import matplotlib.pyplot as plt

from tools import m2nm, nm2m, ms2kts, rad2deg

def plot_histogram(data,title,xlabel,nbins,ylim=10,range=None):

    if not range:
        range = (data.min(),data.max())

    plt.figure()
    (n,bins,patches) = plt.hist(data,
                                bins=nbins,
                                range=range,
                                rwidth=0.7)

    plt.ylim([0,ylim])
    plt.xticks(bins)
    plt.grid()
    plt.title(title)
    plt.xlabel(xlabel)

def plot_path_deviation(path_deviation):

    max_path_deviation = [ m2nm(deviation.max()) for deviation in path_deviation]

    max_path_deviation = [ deviation for deviation in max_path_deviation if deviation>0.01]

    if max_path_deviation:
        plot_histogram(max_path_deviation,
                       title  = 'Path deviation',
                       xlabel = 'Path deviation [NM]',
                       nbins  = 20,
                       range  = (0,20.0))

def plot_largest_cmd_change(cmd_change):
    
    spd_changes = [ms2kts(spd)  for (spd,hdg) in cmd_change if spd>0.01]
    hdg_changes = [rad2deg(hdg) for (spd,hdg) in cmd_change if hdg>0.01]

    if spd_changes:
        plot_histogram(spd_changes,
                       title  = 'Largest speed change commands',
                       xlabel = 'Speed change command [kts]',
                       nbins  = 10,
                       range  = (0,100.0) )

    if hdg_changes:
        plot_histogram(hdg_changes,
                       title  = 'Largest heading change commands',
                       xlabel = 'Heading change command [deg]',
                       nbins  = 18,
                       range  = (0,180.0) )

def plot_largest_cmd_state_change(state_change):

    state_change = [ms2kts(state) for state in state_change if state>0.01]

    if state_change:
        plot_histogram(state_change,
                       title  = 'Largest state change commands',
                       xlabel = 'State change command [kts]',
                        nbins  = 15,
                       range  = (0,300.0) )
    

def plot_los(los_data):
    '''Make a histogram of the LOS data'''
    
    los_cpas = [ m2nm(pair['cpa']) for pair in los_data ]

    if los_cpas:
        plot_histogram(los_cpas,
                       title  = 'Number of LOS',
                       xlabel = 'CPA Distance [NM]',
                        nbins  = 5,
                       range=(0.0,5.0))

    

def plot_los_time(los_data):
    '''Make a histogram of the LOS times'''

    los_time = [ pair['time'][-1] - pair['time'][0] for pair in los_data ]

    if los_time:
        plot_histogram(los_time,
                       title  = 'Time in LOS',
                       xlabel = 'Time [s]',
                        nbins  = 10,
                       range=(0.0, 200.0))


def plot_conflicts(conflict_data):
    '''Make a histogram of the conflict data'''
    
    conflict_cpas = [ m2nm(pair['cpa']) for pair in conflict_data ]

    if conflict_cpas:
        plot_histogram(conflict_cpas,
                       title  = 'Number of conflicts',
                       xlabel = 'CPA Distance [NM]',
                        nbins  = 5,
                       range=(0.0,5.0))
    

def plot_conflicts_time(conflict_data):
    '''Make a histogram of the LOS times'''

    conflicts_time = [ pair['time'][-1] - pair['time'][0] for pair in conflict_data ]

    if conflicts_time:
        plot_histogram(conflicts_time,
                       title  = 'Time in conflict',
                       xlabel = 'Time [s]',
                       nbins  = 15,
                       range  = (0.0,300.0))

        
def show():
    '''Show all plots'''
    plt.show()
