"""Utilities to aid satellite location prediction"""
import datetime
from dateutil import parser

import numpy as np


def convert_day_percentage(epoch):
    """Convert a datetime object to decimal TLE format"""

    total_mins = (epoch.hour * 60) + epoch.minute
    total_seconds = (total_mins * 60) + epoch.second
    total_mcs = total_seconds * 1_000_000 + epoch.microsecond

    return float(total_mcs/86_400_000_000)


def convert_bstar(bstar):
    """Abominable conversion to TLEs b_star format. Assumes bstar will never be > 1"""

    b_str = str('{:.12f}'.format(bstar))

    decimal_i = None
    sig_i = None
    i = 0
    sig_figs =[]
    for char in b_str:
        # Found decimal location
        if (b_str[i] == '.'):
            decimal_i = i
        # Found sig figure
        elif(decimal_i is not None):
            # If first sig fig, record location
            if (sig_i is None and char != '0'):
                sig_i = i
            if (char != '0' or (char=='0' and sig_i is not None)):
                sig_figs.append(char)
        i+=1

    sig_figs = sig_figs[0:5]
    tle_b_str = f"{'-' if bstar < 0 else ' '}{''.join(sig_figs) + str(decimal_i - (sig_i-1))}"

    return tle_b_str


def compute_checksum(tle_line):
    """Compute checksum per TLE spec"""

    c_sum = 0
    for char in tle_line:
        if char.isdigit():
            c_sum += int(char)
        elif char == '-':
            c_sum +=1

    return c_sum % 10

def convert_to_tle(**kwargs):
    """
    Converts from Starlonk satellite data format (modified NORAD) to TLE format. 
    The code in its current state should never go into production :|
    """
    norad_cat_id = kwargs['norad_cat_id']
    classification_type = kwargs['classification_type']
    satellite_id = kwargs['satellite_id']
    epoch_str = kwargs['epoch']
    mean_motion_dot = kwargs['mean_motion_dot']
    bstar = kwargs['bstar']
    element_set_no = kwargs['element_set_no']
    inclination = kwargs['inclination']
    ra_of_asc_node = kwargs['ra_of_asc_node']
    eccentricity = kwargs['eccentricity']
    arg_of_pericenter = kwargs['arg_of_pericenter']
    mean_anomaly = kwargs['mean_anomaly']
    mean_motion = kwargs['mean_motion']
    rev_at_epoch = kwargs['rev_at_epoch']

    # Launch data from object id
    l_yr = satellite_id[2:4]
    l_num = satellite_id[5:]

    # Epoch data
    epoch = parser.parse(epoch_str)
    epoch_yr = str(epoch.year)[-2:]
    doy = epoch.timetuple().tm_yday
    day_pct = convert_day_percentage(epoch)

    # Constants
    mean_motion_ddot = "00000+0"
    ephemeris_type = '0'

    ''' Compute first string per TLE format '''

    # Calculate classification details and following spaces
    cat_class = f'1 {norad_cat_id}{classification_type}'
    cat_space = ''.join([' ' for i in range(9 - len(cat_class))])
    cat = f"{cat_class}{cat_space}"

    # Calculate launch details and following spaces
    launch_data = f'{cat}{l_yr}{l_num}'
    launch_space = ''.join([' ' for i in range(18 - len(launch_data))])
    launch =f"{launch_data}{launch_space}"

    # Calculate epoch details and following spaces
    day_data = float(doy + day_pct)
    day_data_f = format(day_data, '.8f')
    epoch_data = f'{launch}{epoch_yr}{day_data_f}'
    epoch_space = ''.join([' ' for i in range(33 - len(epoch_data))])
    epoch = f'{epoch_data}{epoch_space}'

    # Calculate mean motion details and following spaces
    if mean_motion_dot > 0:
        mean_motion_dot = ' ' + str(format(mean_motion_dot, '.8f')).replace('0.','.')
    else:
        mean_motion_dot = str(format(mean_motion_dot, '.8f')).replace('0.','.')
    
    #Calculate mean motion dot details and following spaces
    mean_motion_dot_data = f'{epoch}{mean_motion_dot}'
    mean_motion_dot_space = ''.join([' ' for i in range(45 - len(mean_motion_dot_data))])
    mean_motion_dot_all = f'{mean_motion_dot_data}{mean_motion_dot_space}'

    # Calculate mean motion ddot details and following spaces
    mean_motion_ddot_data = f'{mean_motion_dot_all}{mean_motion_ddot}'
    mean_motion_ddot_space = ''.join([' ' for i in range(53 - len(mean_motion_ddot_data))])
    mean_motion_ddot = f'{mean_motion_ddot_data}{mean_motion_ddot_space}'

    # Calculate bstar (drag) details and following spaces AND Ephemeris (always one space)
    bstar_data = f'{mean_motion_ddot}{convert_bstar(bstar)} {ephemeris_type}'
    bstar_space = ''.join([' ' for i in range(65 - len(bstar_data))])
    bstar_all = f'{bstar_data}{bstar_space}'

    ephemeris = f'{bstar_all}'
    s_unchecked = f'{ephemeris}{element_set_no}'
    checksum = compute_checksum(s_unchecked)

    s = f'{s_unchecked}{checksum}'

    ''' Compute second string per TLE format '''

    # Always assuming 2 spaces after catalog id
    catalog = f'2 {norad_cat_id}  '

    # Format inclination data
    inclination_formatted = format(inclination, '.4f')
    inclination_data = f'{catalog}{inclination_formatted}'
    inclination_spaces = ''.join([' ' for i in range(17 - len(inclination_data))])
    inclination_all = f'{inclination_data}{inclination_spaces}'

    # Format ra_of_asc_node (add starting space if < 100)
    if (ra_of_asc_node < 10):
        ra = '  ' + format(ra_of_asc_node, '.4f')
    elif (ra_of_asc_node < 100):
        ra = ' ' + format(ra_of_asc_node, '.4f')
    else:
        ra = format(ra_of_asc_node, '.4f')

    ra_data = f'{inclination_all}{ra}'
    ra_spaces = ''.join([' ' for i in range(26 - len(ra_data))])
    ra_all = f'{ra_data}{ra_spaces}'

    # Format eccentricity
    eccentricity_formatted = format(eccentricity, '.7f').replace('0.','')
    eccentricity_data = f'{ra_all}{eccentricity_formatted}'
    eccentricity_spaces = ''.join([' ' for i in range(34 - len(eccentricity_data))])
    eccentricity_all = f'{eccentricity_data}{eccentricity_spaces}'

    # Format arg_of_pericenter
    if arg_of_pericenter < 10:
        arg_of_pericenter = '  ' + format(arg_of_pericenter, '.4f')
    elif arg_of_pericenter < 100:
        arg_of_pericenter = ' ' + format(arg_of_pericenter, '.4f')
    else:
        arg_of_pericenter = format(arg_of_pericenter, '.4f')

    arg_of_pericenter_data = f'{eccentricity_all}{arg_of_pericenter}'
    arg_of_pericenter_spaces = ''.join([' ' for i in range(43 - len(arg_of_pericenter_data))])
    arg_of_pericenter_all = f'{arg_of_pericenter_data}{arg_of_pericenter_spaces}'

    # Format mean_anomaly
    if mean_anomaly < 10:
        mean_anomaly = '  ' + format(mean_anomaly, '.4f')
    elif mean_anomaly < 100:
        mean_anomaly = ' ' + format(mean_anomaly, '.4f')
    else:
        mean_anomaly = format(mean_anomaly, '.4f')

    mean_anomaly_data = f'{arg_of_pericenter_all}{mean_anomaly}'
    mean_anomaly_spaces = ''.join([' ' for i in range(52 - len(mean_anomaly_data))])
    mean_anomaly_all = f'{mean_anomaly_data}{mean_anomaly_spaces}'

    #format mean_motion (10 < mean_motion < 100)
    mean_motion = format(mean_motion, '.8f')
    mean_motion_data = f'{mean_anomaly_all}{mean_motion}'
    mean_motion_spaces = ''.join([' ' for i in range(63 - len(mean_motion_data))])
    mean_motion_all = f'{mean_motion_data}{mean_motion_spaces}'

    #format rev_at_epoch
    if rev_at_epoch < 10:
        rev_at_epoch = '    ' + str(rev_at_epoch)
    elif rev_at_epoch < 100:
        rev_at_epoch = '   ' + str(rev_at_epoch)
    elif rev_at_epoch < 1000:
        rev_at_epoch = '  ' + str(rev_at_epoch)
    elif rev_at_epoch < 10000:
        rev_at_epoch = ' ' + str(rev_at_epoch)
    else:
        rev_at_epoch = str(rev_at_epoch)

    t_unchecked = f'{mean_motion_all}{rev_at_epoch}'
    t = f'{t_unchecked}{compute_checksum(t_unchecked)}'

    return s, t


def round_time(dt=None, roundTo=60):
    """Round time to 'roundTo' seconds"""
    if dt is None:
        dt = datetime.datetime.utcnow()
    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = (seconds+roundTo/2) // roundTo * roundTo
    return dt + datetime.timedelta(0,rounding-seconds,-dt.microsecond)

def deNaN(loc):
    """Swap NaNs with Nones"""
    return None if np.isnan(loc) else loc