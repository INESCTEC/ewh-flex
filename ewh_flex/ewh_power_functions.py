##############################################
##       EWH Power Profile Functions        ##
##############################################

import pandas as pd
import numpy as np
import math
import datetime

from .auxiliary_functions import round_up_hundred

##############################################
##        EWH Spec Power Detection          ##
##############################################

def ewh_power_detection(dataset):
    _temp_load = pd.DataFrame(dataset.copy())
    _temp_load.columns = ['timestamp','load']
    _temp_load['timestamp'] = pd.to_datetime(_temp_load['timestamp'], utc=True)

    # delete observations where load is low
    _temp_load = _temp_load.loc[_temp_load['load'] > (0.15 * max(_temp_load['load'])/.95)]
    # filter out bottom and top 10% values
    _quantile = _temp_load['load'].quantile([0.1, 0.9])
    _temp_load = _temp_load[_temp_load['load'].between(_quantile[.1], _quantile[0.9])]
    # estimated load is the average of the selected observations
    _ewh_estimated_power = round_up_hundred(_temp_load['load'].mean()/.9)
    return _ewh_estimated_power

##############################################
##         Convert Load to Usage            ##
##############################################

def convert_load_usage(dataset, varBackpack):

    # unpack some variables
    ewh_power = varBackpack['ewh_power_original']
    ewh_max_temp = varBackpack['ewh_max_temp']
    temp_set = varBackpack['tempSet']

    # dataset copy
    _temp_load = pd.DataFrame(dataset.copy())
    _temp_load.columns = ['timestamp','load']
    _temp_load['timestamp'] = pd.to_datetime(_temp_load['timestamp'], utc=True)

    # required data
    ewh_power = 0.9 * ewh_power/1000  # kilowatts with 90% efficiency
    ewh_max_temp = 0.9 * ewh_max_temp # assumes 80% of max temperature
    temp_set = temp_set  # comfort temperature (usage)
    temp_inlet = 20  # network water temperature
    flow_out = 8.5  # liters per minute
    delta_t = 1 / 60  # minute resolution
    waterHeatCap = 4.186  # Specific heat capacity of water (4.186 J/g°C)

    # Total energy balance of prosumer’s EWH at the beginning (kWh)
    # w_init = ewh_max_temp * ewh_capacity * waterHeatCap / 3600
    # calculates approximate ewh flow with mixture with inlet water (assumes 90% of max temperature)
    # for tempSet=45 and for
    flow_ewh = flow_out * (temp_set - temp_inlet) / (ewh_max_temp - temp_inlet)
    # calculates losses
    # w_out = ewh_max_temp * (flow_ewh * TEMPO_USO) * waterHeatCap / 3600
    # calculates heating per minute
    w_in = ewh_power * delta_t

    # variable that flags EWH heating
    _temp_load['heating'] = 0
    _temp_load.loc[(_temp_load['load'] / 100) > (ewh_power / 5), 'heating'] = 1


    # 1st step: detect average duration of periods between automatic re-heating
    # objective, disregard periods where the EWH activates without water usage
    # auxiliary variable for flagging blanks blocks
    blank = 0
    # list of blank blocks duration
    blanks_list = list()
    for i in range(0, len(_temp_load)):
        if (_temp_load.loc[i, 'heating'] == 0) & (blank == 0):
            _start = _temp_load.loc[i, 'timestamp']
            blank = 1
            # flag instance as heating
            continue

        if (_temp_load.loc[i, 'heating'] == 1) & (blank == 1):
            _end = _temp_load.loc[i - 1, 'timestamp']
            blank = 0
            # calculate total minutes of blank
            blank_time = int((_end - _start).total_seconds() / 60)
            # only saves blocks if larger than 90min
            if blank_time > 90:
                blanks_list.append(blank_time)

    blanks_list = np.array(blanks_list)

    blank = 0
    heating = 0
    # variable that flags water usage
    _temp_load['usage'] = 0
    for i in range(0, len(_temp_load)):

        if (_temp_load.loc[i, 'heating'] == 0) & (blank == 0):
            _start_blank = _temp_load.loc[i, 'timestamp']
            blank = 1
            # flag instance as heating

        if (_temp_load.loc[i, 'heating'] == 1) & (blank == 1):
            _end_blank = _temp_load.loc[i - 1, 'timestamp']
            blank = 0
            # calculate total minutes of blank
            blank_time = int((_end_blank - _start_blank).total_seconds() / 60)


        if (_temp_load.loc[i, 'heating'] == 1) & (heating == 0):
            _start = _temp_load.loc[i, 'timestamp']
            heating = 1
            # flag instance as heating
            continue

        if (_temp_load.loc[i, 'heating'] == 0) & (heating == 1):
            _end = _temp_load.loc[i - 1, 'timestamp']
            heating = 0
            # calculate total minutes of heating
            heating_time = int((_end - _start).total_seconds() / 60)
            # calculate total minutes of usage via formula
            usage_time = heating_time / (1 + ((ewh_max_temp * flow_ewh * waterHeatCap) / (3600 * w_in)))
            usage_time = math.ceil(usage_time)
            # extract end of usage (subtract one, since start date already included)
            _end = _start + datetime.timedelta(minutes=(usage_time - 1))
            # only flags if long enough and using blank filters
            if (blank_time < blanks_list.mean()*.9) | (usage_time>2):
                # flag as using water
                _temp_load.loc[(_temp_load['timestamp'] >= _start) & (_temp_load['timestamp'] <= _end), 'usage'] = 1
            continue

    return _temp_load['usage']
