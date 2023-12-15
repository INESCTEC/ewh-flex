from .ewh_power_functions import convert_load_usage
from .ewh_opt_functions import (build_varBackpack, update_dataset_backpack, linear_regressors, ewh_solver)

##############################################
##      Optimization Pipeline Function      ##
##############################################

def ewh_optimization(params_input, dataset, optSolver = 'HiGHS', solverPath=None):
    varBackpack = build_varBackpack(params_input, dataset)
    dataset['delta_use'] = convert_load_usage(dataset, varBackpack)
    dataset, varBackpack = update_dataset_backpack(dataset, varBackpack)
    varBackpack = linear_regressors(dataset, varBackpack)
    opt_output = ewh_solver(dataset, varBackpack, optSolver=optSolver, solverPath=solverPath)

    return opt_output
