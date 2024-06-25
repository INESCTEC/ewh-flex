from ewh_flex import read_data
from ewh_flex import ewh_optimization
from ewh_flex import return_results
import json

with open(r'./tests/data/results_test.json') as json_data:
    results_test = json.load(json_data)

##############################################
##            Read Input Data               ##
##############################################

def test_ewh_flex():
    # Input parameters JSON filepath
    paramsInput_filePath = r'./tests/data/input_parameters.json'
    # User usage input JSON filepath (no load diagram)
    dataset_filePath = r'./tests/data/input_data.json'

    # read data
    dataset, paramsInput = read_data(paramsInput_filePath, dataset_filePath)
    # run optimization
    opt_output = ewh_optimization(paramsInput, dataset, resample='no', optSolver='HiGHS', solverPath=r'./HiGHS/bin/highs.exe')
    # get results
    results = return_results(opt_output)
    for _key, _value in results.items():
        assert _value == results_test.get(_key), f'{_key}'

test_ewh_flex()