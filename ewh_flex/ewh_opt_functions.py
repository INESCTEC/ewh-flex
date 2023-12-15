##############################################
##        EWH Optimization Functions        ##
##############################################
import numpy as np
import pandas as pd
from pulp import *
import re
import math
from sklearn.linear_model import LinearRegression
import datetime

from .ewh_power_functions import ewh_power_detection
from .auxiliary_functions import fillDefaults



##############################################
##            Input Parameters              ##
##############################################
def build_varBackpack(paramsInput, dataset):

    # default paramters if any are missing
    paramsDefault ={
        "user": "sample_user",
        "datetime_start": "2022-12-07T00:00:00.000Z",
        "datetime_end": "2022-12-13T23:59:00.000Z",
        "ewh_specs": {
            "ewh_capacity": 100,
            "ewh_power": 1800,
            "ewh_max_temp": 80,
            "user_comf_temp": 40,
            "tariff": 1,
            "price_simple": 0.119585,
            "price_dual_day": 0.149118,
            "price_dual_night": 0.070511,
            "tariff_simple": 0.3604,
            "tariff_dual": 0.4285
        }
    }

    # check if paramsInput is filled, and fix with defaults
    paramsInput = fillDefaults(paramsInput, paramsDefault)

    # unpack some variables
    user = paramsInput['user']
    # Water Usage Temperature Setpoint (minimum user-defined temperature - °C)
    tempSet = paramsInput['ewh_specs']['user_comf_temp']
    # EWH capacity (l)
    ewh_capacity = paramsInput['ewh_specs']['ewh_capacity']
    # EWH maximum allowed temperature
    ewh_max_temp = paramsInput['ewh_specs']['ewh_max_temp']
    ewh_power_original = paramsInput['ewh_specs']['ewh_power']

    # Heating power of the EWH (kw) with 90% efficiency
    if (ewh_power_original > 250) & (ewh_power_original < 5000):
        ewh_power = 0.9 * ewh_power_original/1000
    else:
        # detect ewh power
        ewh_power_original = ewh_power_detection(dataset)
        ewh_power = 0.9 * ewh_power_original/1000

    ## sufficiently big number for if-else constraints
    bigNumber = 1E5
    ## EWH Dimensions (cm)
    ewh_height = 100
    ## calculate radius (m)
    ewh_radius = math.sqrt((ewh_capacity/1000)/((ewh_height/100)*np.pi))
    ## calculate area (m2)
    ewh_area = 2 * np.pi * ewh_radius * (ewh_radius + ewh_height/100)
    # Specific heat capacity of water (4.186 J/g°C)
    waterHeatCap = 4.186
    ### overall heat transfer coefficient (kW/(m2*K))
    heatTransferCoeff = 0.00125
    ## Ambient Temperature (ºC)
    ambTemp = 20
    ## Inlet/network water temperature
    temp_inlet = 20
    # EWH minimum allowed temperature
    ewh_min_temp = 0
    # EWH start-point temperature
    ewh_start_temp = 60
    # total flow rate
    flow_rate_min = 8.5  ## kg/min
    # Minimum allowable energy content of the prosumer’s EWH (kWh)
    wh_min = ewh_min_temp * ewh_capacity * waterHeatCap / 3600
    # Maximum allowable energy content of the prosumer’s EWH (kWh)
    wh_max = ewh_max_temp * ewh_capacity * waterHeatCap / 3600
    # Total energy balance of prosumer’s EWH at the beginning (kWh)
    wh_init = ewh_start_temp * ewh_capacity * waterHeatCap / 3600


    ## create variable backpack for export
    varBackpack = {}
    # user id
    varBackpack['user'] = user
    # EWH capacity (l)
    varBackpack['ewh_capacity'] = ewh_capacity
    # Heating power of the EWH (kw)
    varBackpack['ewh_power'] = ewh_power
    # original power without efficiency
    varBackpack['ewh_power_original'] = ewh_power_original
    # EWH maximum allowed temperature
    varBackpack['ewh_max_temp'] = ewh_max_temp
    # Hot-Water Usage Comfort Temperature (minimum user-defined temperature - °C)
    varBackpack['tempSet'] = tempSet
    ## sufficiently big number for if-else constraints
    varBackpack['bigNumber'] = bigNumber
    ## EWH Height (cm)
    varBackpack['ewh_height'] = ewh_height
    ## calculate radius (m)
    varBackpack['ewh_radius'] = ewh_radius
    ## calculate area (m2)
    varBackpack['ewh_area'] = ewh_area
    # Specific heat capacity of water (4.186 J/g°C)
    varBackpack['waterHeatCap'] = waterHeatCap
    ### overall heat transfer coefficient (kW/(m2*K))
    varBackpack['heatTransferCoeff'] = heatTransferCoeff
    ## Ambient Temperature (ºC)
    varBackpack['ambTemp'] = ambTemp
    ## Inlet/network water temperature
    varBackpack['temp_inlet'] = temp_inlet
    ## Outlet flow rate
    varBackpack['flow_rate_min'] = flow_rate_min
    # EWH minimum allowed temperature
    varBackpack['ewh_min_temp'] = ewh_min_temp
    # EWH start-point temperature
    varBackpack['ewh_start_temp'] = ewh_start_temp
    # Minimum allowable energy content of the prosumer’s EWH (kWh)
    varBackpack['wh_min'] = wh_min
    # Maximum allowable energy content of the prosumer’s EWH (kWh)
    varBackpack['wh_max'] = wh_max
    # Total energy balance of prosumer’s EWH at the beginning (kWh)
    varBackpack['wh_init'] = wh_init
    # Pricing Tariff (1-simple, 2-day/night)
    varBackpack['tariff'] = paramsInput['ewh_specs']['tariff']
    varBackpack['price_simple'] = paramsInput['ewh_specs']['price_simple']
    varBackpack['price_dual_day'] = paramsInput['ewh_specs']['price_dual_day']
    varBackpack['price_dual_night'] = paramsInput['ewh_specs']['price_dual_night']
    varBackpack['tariff_simple'] = paramsInput['ewh_specs']['tariff_simple']
    varBackpack['tariff_dual'] = paramsInput['ewh_specs']['tariff_dual']

    return varBackpack


##############################################
##            Additional Data               ##
##############################################
def update_dataset_backpack(dataset, varBackpack):

    # unpack some variables
    ewh_capacity = varBackpack['ewh_capacity']
    tempSet = varBackpack['tempSet']
    temp_inlet = varBackpack['temp_inlet']
    waterHeatCap = varBackpack['waterHeatCap']
    flow_rate_min = varBackpack['flow_rate_min']
    price_simple = varBackpack['price_simple']
    price_dual_day = varBackpack['price_dual_day']
    price_dual_night = varBackpack['price_dual_night']
    tariff = varBackpack['tariff']

    # check time resolution in minutes
    resolution = dataset.loc[1, 'timestamp'] - dataset.loc[0, 'timestamp']
    resolution = (resolution.seconds % 3600) // 60
    delta_t = resolution / 60  # hours > 1m
    T = range(len(dataset))
    # fix mass value
    dataset['mass'] = ewh_capacity
    # add w_confort
    dataset['w_confort'] = tempSet * ewh_capacity * waterHeatCap / 3600
    # flow rate
    flow_rate_value = flow_rate_min * 60 * delta_t
    # fix flow rate value
    dataset['flow_rate'] = flow_rate_value
    # fix mass value
    dataset['mass'] = ewh_capacity
    # add w_confort
    dataset['w_confort'] = tempSet * ewh_capacity * waterHeatCap / 3600
    # add inlet temperature
    dataset['temp_inlet'] = temp_inlet
    # total simulated days
    daySim = len(dataset) / 1440

    ## add price
    dataset['price1'] = price_simple
    dataset.loc[(dataset['timestamp'].dt.hour >= 0) & (dataset['timestamp'].dt.hour < 8), 'price2'] = price_dual_night
    dataset.loc[(dataset['timestamp'].dt.hour >= 22) & (dataset['timestamp'].dt.hour <= 23), 'price2'] = price_dual_night
    dataset.loc[(dataset['timestamp'].dt.hour >= 8) & (dataset['timestamp'].dt.hour < 22), 'price2'] = price_dual_day

    # create variables from dataset
    flow_rate = list(dataset.flow_rate)
    delta_use = list(dataset.delta_use)
    temp_inlet = list(dataset.temp_inlet)

    if tariff == 1:
        networkTariff = varBackpack['tariff_simple']
        networkPrice = list(dataset.price1)
    else:
        networkTariff = varBackpack['tariff_dual']
        networkPrice = list(dataset.price2)

    # update and add some backpack variables

    # T range for optimization
    varBackpack['T'] = T
    # resolution for each T Step
    varBackpack['delta_t'] = delta_t
    # Flow Rate Value on T
    varBackpack['flow_rate_value'] = flow_rate_value
    # total simulated days
    varBackpack['daySim'] = daySim
    # EWH capacity (l)
    varBackpack['flow_rate'] = flow_rate
    # Flow Rate Value on T
    varBackpack['delta_use'] = delta_use
    # total simulated days
    varBackpack['temp_inlet'] = temp_inlet
    # network tariff and price
    varBackpack['networkPrice'] = networkPrice
    varBackpack['networkTariff'] = networkTariff

    return dataset, varBackpack

##############################################
##        Regressors (Linearization)        ##
##############################################
def linear_regressors(dataset, varBackpack):

    # unpack some variables
    tempSet = varBackpack['tempSet']
    temp_inlet = varBackpack['temp_inlet']
    ewh_max_temp = varBackpack['ewh_max_temp']
    flow_rate_value = varBackpack['flow_rate_value']
    waterHeatCap = varBackpack['waterHeatCap']
    ewh_capacity = varBackpack['ewh_capacity']

    ### Regressor 1 with temp_ewh ranging from setpoint to max
    # range of temp_heat values: from inlet to max ewh
    temp_aux = range(tempSet,ewh_max_temp+1)
    ## create df with inlet temp from real data
    regressor_aboveSet = dataset[['temp_inlet']].copy()
    ## remove duplicate temperatures
    regressor_aboveSet = regressor_aboveSet.drop_duplicates(subset='temp_inlet', keep="first")
    ## how many different temp_inlets there are available
    counter = len(regressor_aboveSet)
    ## repeat temp_inlet values for joining with temp_heat values
    regressor_aboveSet = regressor_aboveSet.loc[regressor_aboveSet.index.repeat(len(temp_aux))].reset_index(drop=True)
    ## add the temp_heat values
    regressor_aboveSet['temp_heat'] = list(temp_aux) * counter
    ## add remaining variables
    regressor_aboveSet['temp_set'] = tempSet
    regressor_aboveSet['flow_rate'] = flow_rate_value
    ## calculate ewh_flow via fluid mix formula
    regressor_aboveSet['ewh_flow'] = regressor_aboveSet['flow_rate'] * (regressor_aboveSet['temp_set']-regressor_aboveSet['temp_inlet']) / (regressor_aboveSet['temp_heat']-regressor_aboveSet['temp_inlet'])
    ## calculate ewh output energy
    regressor_aboveSet['w_out'] = regressor_aboveSet['ewh_flow'] * waterHeatCap * (regressor_aboveSet['temp_heat']) / 3600
    ## calculate internal water energy
    regressor_aboveSet['w_water'] = ((regressor_aboveSet['temp_heat']*(ewh_capacity-regressor_aboveSet['ewh_flow']) + regressor_aboveSet['temp_inlet']*regressor_aboveSet['ewh_flow']) / ewh_capacity) * ewh_capacity * waterHeatCap/3600


    ### Regressor 2 with temp_ewh ranging from minimum of inlet to setpoint
    #range of temp_heat values: from inlet to max ewh
    temp_aux = range(np.floor(min(temp_inlet)).astype(int),tempSet+1)
    ## create df with inlet temp from real data
    regressor_belowSet = dataset[['temp_inlet']].copy()
    ## remove duplicate temperatures
    regressor_belowSet = regressor_belowSet.drop_duplicates(subset='temp_inlet', keep="first")
    ## how many different temp_inlets there are available
    counter = len(regressor_belowSet)
    ## repeat temp_inlet values for joining with temp_heat values
    regressor_belowSet = regressor_belowSet.loc[regressor_belowSet.index.repeat(len(temp_aux))].reset_index(drop=True)
    ## add the temp_heat values
    regressor_belowSet['temp_heat'] = list(temp_aux) * counter
    ## add remaining variables
    regressor_belowSet['temp_set'] = tempSet
    regressor_belowSet['flow_rate'] = flow_rate_value
    ## since internal temperature is below setpoint, the flow rate is a direct link from the EWH
    regressor_belowSet['ewh_flow'] = flow_rate_value
    ## calculate ewh output energy
    regressor_belowSet['w_out'] = regressor_belowSet['ewh_flow'] * waterHeatCap * (regressor_belowSet['temp_heat']) / 3600
    ## calculate internal water energy
    regressor_belowSet['w_water'] = ((regressor_belowSet['temp_heat']*(ewh_capacity-regressor_belowSet['ewh_flow']) + regressor_belowSet['temp_inlet']*regressor_belowSet['ewh_flow']) / ewh_capacity) * ewh_capacity * waterHeatCap/3600
    ## remove lines where temp_heat < temp_inlet (impossible)
    regressor_belowSet = regressor_belowSet[regressor_belowSet['temp_heat']>=regressor_belowSet['temp_inlet']]

    ## Eq.(8)
    ## above setpoint (regressor_aboveSet)
    ## create the regression
    reg = LinearRegression().fit(regressor_aboveSet[['temp_heat']],regressor_aboveSet['w_water'].values)
    ## regression R score
    regressor_aboveSet_score = reg.score(regressor_aboveSet[['temp_heat']],regressor_aboveSet['w_water'].values)
    ## Extract coeffiecients
    regressor_aboveSet_m = reg.coef_[0]
    regressor_aboveSet_b = reg.intercept_
    ## below setpoint (regressor_belowSet)
    ## create the regression
    reg = LinearRegression().fit(regressor_belowSet[['temp_heat']],regressor_belowSet['w_water'].values)
    ## regression R score
    regressor_belowSet_score = reg.score(regressor_belowSet[['temp_heat']],regressor_belowSet['w_water'].values)
    ## Extract coeffiecients
    regressor_belowSet_m = reg.coef_[0]
    regressor_belowSet_b = reg.intercept_

    varBackpack['regressor_aboveSet_m'] = regressor_aboveSet_m
    varBackpack['regressor_aboveSet_b'] = regressor_aboveSet_b
    varBackpack['regressor_belowSet_m'] = regressor_belowSet_m
    varBackpack['regressor_belowSet_b'] = regressor_belowSet_b

    return varBackpack


##############################################
##       Solving Optimization Problem       ##
##############################################
def ewh_solver(dataset, varBackpack, optSolver='HiGHS', solverPath=None):

    # unpack some variables
    T = varBackpack['T']
    wh_init = varBackpack['wh_init']
    ewh_power = varBackpack['ewh_power']
    delta_t = varBackpack['delta_t']
    daySim = varBackpack['daySim']
    user = varBackpack['user']
    networkPrice = varBackpack['networkPrice']
    networkTariff = varBackpack['networkTariff']
    ewh_start_temp = varBackpack['ewh_start_temp']
    ewh_capacity = varBackpack['ewh_capacity']
    waterHeatCap = varBackpack['waterHeatCap']
    heatTransferCoeff = varBackpack['heatTransferCoeff']
    ewh_area = varBackpack['ewh_area']
    ambTemp = varBackpack['ambTemp']
    wh_min = varBackpack['wh_min']
    wh_max = varBackpack['wh_max']
    ewh_min_temp = varBackpack['ewh_min_temp']
    ewh_max_temp = varBackpack['ewh_max_temp']
    delta_use = varBackpack['delta_use']
    tempSet = varBackpack['tempSet']
    bigNumber = varBackpack['bigNumber']
    regressor_aboveSet_m = varBackpack['regressor_aboveSet_m']
    regressor_aboveSet_b = varBackpack['regressor_aboveSet_b']
    regressor_belowSet_m = varBackpack['regressor_belowSet_m']
    regressor_belowSet_b = varBackpack['regressor_belowSet_b']

    ##############################################
    ##           DECISION VARIABLES             ##
    ##############################################

    # Temperature of water at EWH outlet at the beginning of time interval t (°C)
    temp = [LpVariable(f'temp_{t:03d}', lowBound=0) for t in T]
    # Total energy balance of prosumer’s EWH at time interval t (kWh)
    w_tot = [LpVariable(f'w_tot_{t:03d}', lowBound=0) for t in T]
    # Energy into the prosumer’s EWH at time interval t (kWh)
    w_in = [LpVariable(f'w_in_{t:03d}', lowBound=0) for t in T]
    # Thermal energy losses at time interval t (kWh)
    w_loss = [LpVariable(f'w_loss_{t:03d}') for t in T]
    # Binary variable for EWH operation status (1 = ON, 0 = OFF)
    delta_in = [LpVariable(f'delta_in_{t:03d}', cat=LpBinary) for t in T]
    # Amount of energy stored in the EWH after usage and mixing with inlet
    w_water = [LpVariable(f'w_water_{t:03d}', lowBound=0) for t in T]
    # Extra cost associated with water temperature reaching below comfort
    costComfort = [LpVariable(f'costComfort_{t:03d}', lowBound=0) for t in T]
    # Binary Variable for if-else expression 15
    binAux = [LpVariable(f'binAux_{t:03d}', cat=LpBinary) for t in T]
    # Pricing of that specific energy usage
    energyCost = [LpVariable(f'price_{t:03d}', lowBound=0) for t in T]


    ##############################################
    ##           DEFINING THE MILP              ##
    ##############################################

    # Create MIlP Instance
    milp = LpProblem('Thermo_MILP', LpMinimize)
    # Define the objective function
    milp += lpSum(energyCost[t] * 100 + costComfort[t] * 1000 for t in T), 'Objective_Function'


    ##############################################
    ##              CONSTRAINTS                 ##
    ##############################################

    for t in T:
        # Eq. (1)
        if t == 0:
           milp += w_tot[t] == wh_init, f'Constraint_1_{t:03d}'
        else:
           milp += w_tot[t] == w_water[t-1] + w_in[t-1] - w_loss[t-1], f'Constraint_1_{t:03d}'
        # Eq. (2)
        milp += w_in[t] == ewh_power * delta_t * delta_in[t], f'Constraint_2_{t:03d}'
        # Eq. (3) Pricing
        milp += energyCost[t] == delta_in[t] * ewh_power * delta_t * networkPrice[t] + networkTariff * (delta_t/24), f'Constraint_3_{t:03d}'
        # Eq. (4)
        if t == 0:
            milp += temp[t] == ewh_start_temp, f'Constraint_4_{t:03d}'
        else:
            milp += temp[t] == (w_tot[t] * 3600) / (ewh_capacity * waterHeatCap), f'Constraint_4_{t:03d}'
        # Eq. (5)
        milp += w_loss[t] == heatTransferCoeff * ewh_area * ((temp[t] - ambTemp)) * delta_t, f'Constraint_5_{t:03d}'
        # Eq. (6)
        milp += wh_min <= w_tot[t], f'Constraint_6.1_{t:03d}'
        milp += w_tot[t] <= wh_max, f'Constraint_6.2_{t:03d}'
        milp += ewh_min_temp <= temp[t], f'Constraint_6.3_{t:03d}'
        milp += temp[t] <= ewh_max_temp, f'Constraint_6.4_{t:03d}'

        ## Eq.(7) assure that in the (t) period after the end of hot water usage (t-1), the EWH has, at least, 80L @ 45ºC [t]
        if delta_use[t]-delta_use[t-1] < 0:
            milp += w_tot[t] >= (tempSet*1.005 * ewh_capacity * waterHeatCap / 3600) - costComfort[t], f'Constraint_7_{t:03d}'
            # milp += w_tot[t] >= (tempSet * ewh_capacity * waterHeatCap / 3600), f'Constraint_14_{t:03d}'

        ## Eq.(8) Internal water energy after usage
        if delta_use[t] > 0:
            # binary definition with temp[t]
            milp += temp[t] >= tempSet - bigNumber * (1-binAux[t]), f'Constraint_8.1_{t:03d}'
            milp += temp[t] <= tempSet + bigNumber * binAux[t], f'Constraint_8.2_{t:03d}'
            # if temp[t] > tempSet
            milp += w_water[t] >= (regressor_aboveSet_m * temp[t] + regressor_aboveSet_b) - bigNumber * (1-binAux[t]), f'Constraint_8.3_{t:03d}'
            milp += w_water[t] <= (regressor_aboveSet_m * temp[t] + regressor_aboveSet_b) + bigNumber * (1-binAux[t]), f'Constraint_8.4_{t:03d}'
            # else
            milp += w_water[t] >= (regressor_belowSet_m * temp[t] + regressor_belowSet_b) - bigNumber * binAux[t], f'Constraint_8.5_{t:03d}'
            milp += w_water[t] <= (regressor_belowSet_m * temp[t] + regressor_belowSet_b) + bigNumber * binAux[t], f'Constraint_8.6_{t:03d}'
        else:
            milp += w_water[t] == temp[t] * ewh_capacity * waterHeatCap / 3600, f'Constraint_8.7_{t:03d}'




    ##############################################
    ##           SAVING AND SOLVING             ##
    ##############################################

    # Write the milp to a .lp file
    milp.writeLP('thermo_milp.lp')

    #time limit depends on simulated days plus 1 minute
    timeLimit = (daySim * 10) + 60


    if (optSolver == 'HiGHS'):
        solver = getSolver('HiGHS_CMD', msg=True, timeLimit=timeLimit, path=solverPath, gapRel=0.005, threads=1)
    if (optSolver == 'CBC'):
        solver = getSolver('PULP_CBC_CMD', msg=True, timeLimit=timeLimit, gapRel=0.005)

    milp.solve(solver)
    # -- LpStatus is a dictionary with the status of solution:
    # -- {0: 'Not Solved', 1: 'Optimal', -1: 'Infeasible', -2: 'Unbounded', -3: 'Undefined'}
    stat = LpStatus[milp.status]
    opt_val = value(milp.objective)  # objective function value



    ##############################################
    ##             Export Results               ##
    ##############################################
    # Outputs stored in sheet "general"
    general_outputs = {'MILP status': stat, 'Objective Function Value': opt_val}
    # variable list
    vars = ['temp','w_tot','w_in','w_out','w_loss','delta_in','delta_flex','w_flex']
    # create empty df
    opt_diagrams = pd.DataFrame(index=T,columns=vars)
    opt_diagrams = dataset[['timestamp','temp_inlet','delta_use']].copy()


    for v in milp.variables():

        temp_idx = int(''.join(filter(str.isdigit, str(v))))

        ## find variables and store data
        if re.search(f'temp_', v.name):
            opt_diagrams.loc[temp_idx,'temp'] = v.varValue
        if re.search(f'w_tot_', v.name):
            opt_diagrams.loc[temp_idx,'w_tot'] = v.varValue
        if re.search(f'w_water_', v.name):
            opt_diagrams.loc[temp_idx, 'w_water'] = v.varValue
        if re.search(f'w_in_', v.name):
            opt_diagrams.loc[temp_idx,'w_in'] = v.varValue
        if re.search(f'w_out_', v.name):
            opt_diagrams.loc[temp_idx,'w_out'] = v.varValue
        if re.search(f'w_loss_', v.name):
            opt_diagrams.loc[temp_idx,'w_loss'] = v.varValue
        if re.search(f'delta_in_', v.name):
            opt_diagrams.loc[temp_idx,'delta_in'] = v.varValue
        if re.search(f'binAux_', v.name):
            opt_diagrams.loc[temp_idx,'binAux'] = v.varValue
        if re.search(f'price_', v.name):
            opt_diagrams.loc[temp_idx,'price'] = v.varValue

    # fix delta_in very low and close to 1 values
    opt_diagrams.loc[opt_diagrams['delta_in']<0.001,'delta_in'] = 0
    opt_diagrams.loc[opt_diagrams['delta_in']>0.999,'delta_in'] = 1
    ## add variable of flexibility (1-delta_in):
    opt_diagrams['flex'] = 1-opt_diagrams['delta_in']
    ## total flexibility (min)
    total_flex = sum(opt_diagrams['flex'])*60*delta_t
    # percentage flexibility
    perc_flex = 100*total_flex/(len(opt_diagrams)*60*delta_t)
    ## average daily flexiblity
    avgDailyFlex = total_flex/daySim
    avgDailyFlex_srt = str(datetime.timedelta(minutes=avgDailyFlex) - datetime.timedelta(microseconds=datetime.timedelta(minutes=avgDailyFlex).microseconds))
    ## optimized load
    optimized_load = sum(opt_diagrams['delta_in']) * ewh_power * delta_t
    ## average daily load
    avgDailyLoad = optimized_load/daySim
    ## (deleted microseconds)
    # avgDailyLoad_str = str(datetime.timedelta(minutes=avgDailyLoad) - datetime.timedelta(microseconds=datetime.timedelta(minutes=avgDailyLoad).microseconds))
    ## calculate total optimized load diagram
    opt_diagrams['optimized_load'] = opt_diagrams['delta_in']*1000*ewh_power
    ## add original load
    opt_diagrams['original_load'] = dataset['load']
    ## optimized price
    optimized_price = sum(opt_diagrams['price'])
    ## original load
    original_load = dataset['load'].sum()/1000 * delta_t
    ## original price
    ## network price per minute
    networkTariff_minute = networkTariff * (delta_t/24)
    networkTariff_used = networkTariff_minute * len(dataset)
    original_price = original_load * dataset.price1[0] + networkTariff_used


    print("Simulated Period:", str(datetime.timedelta(minutes=len(dataset))))
    print("Time Resolution:", int(60*delta_t), 'min')
    print("Optimized Price:", "{:.2f}".format(optimized_price), '€')
    print("Optimized Load:", "{:.2f}".format(optimized_load), 'kWh')
    print("Original Price:", "{:.2f}".format(original_price), '€')
    print("Original Load:", "{:.2f}".format(original_load), 'kWh')
    print("Avg. Consumption per day:", "{:.2f}".format(avgDailyLoad), 'kWh')
    print("Total Flexibility:", str(datetime.timedelta(minutes=total_flex)))
    print("Perc. Flexibility:", "{:.2f}".format(perc_flex), '%')
    print("Avg. Flexibililty per day:", avgDailyFlex_srt)

    opt_output = {}
    opt_output['user'] = user
    opt_output['tempSet'] = tempSet
    opt_output['simulated_period'] = daySim
    opt_output['time_resolution'] = int(60 * delta_t)
    opt_output['optimized_price'] = optimized_price
    opt_output['optimized_load'] = optimized_load
    opt_output['original_price'] = original_price
    opt_output['original_load'] = original_load
    opt_output['avg_daily_consumption'] = avgDailyLoad
    opt_output['total_flexibility'] = total_flex
    opt_output['perc_flexibility'] = perc_flex
    opt_output['avg_daily_flexibility'] = avgDailyFlex
    opt_output['savings_cost'] = original_price - optimized_price
    opt_output['savings_energy'] = original_load - optimized_load
    opt_output['opt_diagrams'] = opt_diagrams

    return opt_output
