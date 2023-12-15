from ewh_flex import read_data
from ewh_flex import ewh_optimization
from ewh_flex import (plot_results, write_results)

##############################################
##            Read Input Data               ##
##############################################

# Input parameters JSON filepath
paramsInput_filePath = './data/input/input_parameters.json'
# EWH load diagram dataset JSON filepath
dataset_filePath = './data/input/data_example_7_days.json'

# Read data
dataset, paramsInput = read_data(paramsInput_filePath, dataset_filePath)



##############################################
##              Optimization                ##
##############################################

# Select Solver between 'HiGHS' (recommended) and 'CBC'. HiGHS solver requires 'solverPath' to respective binaries
opt_output = ewh_optimization(paramsInput, dataset, optSolver='HiGHS', solverPath='./highs/bin/highs.exe')



##############################################
##              Plot Results                ##
##############################################

## Select plot option between showing plot ('p') or writing ('w'). If writing, fill writePath
plot_results(opt_output, plotOption='w', writePath='./data/output/results.png')



##############################################
##           Write Results JSON             ##
##############################################

write_results(opt_output, writePath="./data/output/results.json")