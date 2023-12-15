![INESC TEC](docs/figures/inesctec.png)
***

# EWH Optimization and Flexibility

This tool focuses on optimizing the functioning calendar of thermoelectric water heaters (EWH) through the 
analysis of a limited dataset. The primary goal is to identify and estimate periods during which flexibility can be 
introduced by enhancing the operation of the EWH. By utilizing only the electrical consumption data of the appliance
as input, the tool calculates optimal periods for initiating EWH operation. This ensures the delivery of 
consumer-defined comfort levels, subject to certain constraints, while simultaneously minimizing operational costs or
total energy consumption. The tool offers a practical solution for enhancing the efficiency and cost-effectiveness of
thermoelectric water heaters based on consumption data analysis.
***

## Documentation

Preliminary documentation available at the project ``docs/`` directory.
It includes the optimization documentation including mathematical formulation.

For a preview of an example REST API for this service, check:

[ewh-flex-rest-api](https://github.com/CPES-Power-and-Energy-Systems/ewh-flex-rest-api)

[ewh-flex-rest-api Swagger](https://cpes-power-and-energy-systems.github.io/ewh-flex-rest-api/)

***

## Initial setup

> **Note**:  The commands below assume that you are running them from the root directory of the project.

### With Local Python Interpreter:

With a local python interpreter, you'll need to manually install dependencies:

1. Install the python dependencies
    > pip install -r requirements.txt

2. Install the `ewh-flex` Python library
    > pip install .
   
3. **HiGHS Solver Integration**

    When opting for the HiGHS solver in the optimization settings, please note that external binary files are required for 
seamless functionality. To utilize this solver, download the necessary files from the [HiGHS project and releases repository](https://github.com/JuliaBinaryWrappers/HiGHSstatic_jll.jl/releases)  and specify their location in the designated path for optimal performance.

***

## How to run

The tool is designed to effortlessly process two primary inputs: the EWH load diagram and a set
of specified parameters. Upon providing these inputs, the tool seamlessly channels them through a dedicated optimization
pipeline. The results, refined through the optimization process, can then be plotted and exported.

* Find comprehensive guidance in the ``/examples`` folder, which not only contains sample input data but also showcases 
exemplar run code (via ``/examples/ewh_opt_example.py``) for a seamless start to the project.
* Navigate to the ``/ewh_flex`` folder within the project directory, where all essential functions for execution are centralized.


***

## Inputs

This tool is prepared to work with a single input containing the EWH consumption diagram with 1 min. resolution. However,
there is a set of optional but recommended inputs that should be addressed in the ``input_parameters.json`` data file.

### Mandatory inputs

To utilize this tool effectively, users are required to provide an Electric Water Heater (EWH) dataset in JSON format,
comprising only timestamps and electrical consumption data (in watts) with minute resolution. An illustrative example 
file can be found in the 'data' folder for reference (``data_example_7_days.json``).

### Optional (but recommended) inputs

For enhanced customization and precision, the tool allows users to provide optional inputs such as:
* ``ewh_capacity``: EWH capacity (l)
* ``ewh_power``: EWH heating power (W)
* ``ewh_max_temp``: EWH maximum allowed water temperature (°C)
* ``user_comf_temp``: Hot-Water Usage Comfort Temperature (minimum user-defined temperature - °C)
* ``tariff``: Tariff selection between simple (1) or dual (2)
* ``price_simple``: Simple pricing value per kWh (Euro)
* ``price_dual_day``: Dual day pricing value per kWh (Euro)
* ``price_dual_night``: Dual night pricing value per kWh (Euro)
* ``tariff_simple``:  Fixed daily simple tariff pricing (Euro)
* ``tariff_dual``: Fixed daily dual tariff pricing (Euro)

If the requester does not provide optional inputs, the default values, as shown in the example JSON below, will be used.

```
{
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
```




Note: The inputs ``user``, ``datetime_start``, and ``datetime_end`` should be ignored if the data is provided directly.



***


## Outputs

The EWH Optimization Tool outputs a comprehensive set of variables in JSON format, including key information. This
structured output provides users with a detailed overview of the optimized Electric Water Heater operation,
facilitating easy analysis and further utilization of the results. This tool provides the following outputs:

* ``simulation_period``: Simulated/Optimized Period including start and end datetimes (minute resolution)
* ``original_energy``: Total accumulated energy for the real measurement profile (kWh)
* ``optimized_energy``: Total accumulated energy for the optimized measurement profile (kWh)
* ``original_price``: Total cost for the real measurement profile (€)
* ``optimized_price``: Total cost for the optimized measurement profile (€)
* ``avg_daily_energy``: Average daily energy Consumption for the optimized scenario (kWh)
* ``total_flexibility``: Flexibility availability for the optimized period (minutes)
* ``perc_flexibility``:  Percentage of the total simulated period that can provide flexibility (%)
* ``avg_daily_flexibility``: Average flexibility availability for the optimized scenario (minutes)
* ``savings_cost``: Pricing savings between real and optimized scenarios (€)
* ``savings_energy``: Energy savings between real and optimized scenarios (kWh)
* ``original_usage_profile``:  Estimated hot-water usage profile based on EWH's real load diagram
* ``optimized_calendar``: Optimized EWH functioning calendarization

Please find and example of the output JSON below:

```
{
  "user": "sample_user",
  "simulation_period": {
    "start": "2022-07-12 00:00:00+00:00",
    "end": "2022-12-13 23:59:00+00:00",
    "days_in_simulation": 7.0
  },
  "original_energy": {
    "value": 24.3384,
    "unit": "kWh"
  },
  "optimized_energy": {
    "value": 20.196,
    "unit": "kWh"
  },
  "original_price": {
    "value": 5.43,
    "unit": "Euro"
  },
  "optimized_price": {
    "value": 4.94,
    "unit": "Euro"
  },
  "avg_daily_energy": {
    "value": 2.8851,
    "unit": "kWh"
  },
  "total_flexibility": {
    "value": 9332.0,
    "unit": "minutes"
  },
  "perc_flexibility": {
    "value": 92.58,
    "unit": "Percent"
  },
  "avg_daily_flexibility": {
    "value": 1333.0,
    "unit": "minutes"
  },
  "savings_cost": {
    "value": 0.5,
    "unit": "Euro"
  },
  "savings_energy": {
    "value": 4.1424,
    "unit": "kWh"
  },
  "original_usage_profile": [
    {"timestamp": "2022-07-12 00:00:00+00:00", "hot_water_usage": 0},
    {"timestamp": "2022-07-12 00:01:00+00:00", "hot_water_usage": 0}
    /* ... more entries ... */
  ],
  "optimized_calendar": [
    {"timestamp": "2022-07-12 00:00:00+00:00", "ewh_on": 0.0},
    {"timestamp": "2022-07-12 00:01:00+00:00", "ewh_on": 0.0}
    /* ... more entries ... */
  ]
}

```

***


## EWH Optimization Modelling, Methodology, and Mathematical Foundation

* Explore the ``/docs`` folder for a detailed exposition of the tool's methodology and underlying mathematical principles.
The modeling approach is anchored in fundamental principles, ensuring transparency and clarity in the application of 
mathematical concepts for robust optimization:

1. **Input Handling:**
   - Provide the EWH load diagram as the initial input to the service.

2. **Conversion to Hot Water Usage:**
   - Utilize the built-in converter to transform the load diagram into nuanced patterns of hot water usage, laying the foundation for subsequent optimization.

3. **Optimization Model:**
   - **Temperature Assurance:**
     - Guarantee that the water temperature within the EWH never falls below the user-defined comfort threshold during and after hot water usage intervals.
   - **Energy Estimates:**
     - Calculate the minimum accumulated energy required for comfort and the total equivalent energy accumulated in the EWH after each hot water usage, considering fluid mixing dynamics.
   - **Comfort Guarantee:**
     - Ensure that the final energy accumulated after use is equal to or greater than the minimum equivalent comfort energy value.
   - **Penalty Mechanism:**
     - Incorporate a penalty variable to handle challenges in guaranteeing constant hot water availability, penalizing excessive temperature reductions.
   - **Energy Considerations:**
     - Account for energy losses by usage, gains by heating, and losses by convection through the EWH's surface area.
   - **Cost Minimization:**
     - Minimize the total operating cost by optimizing the proportion of EWH heating usage and the respective pricing.

4. **Non-linear Constraint Handling:**
   - The optimization model includes a non-linear constraint, skillfully linearized via linear regression. This constraint calculates the equivalent internal energy after hot water usage, ensuring precision and efficiency in diverse EWH operating conditions.

5. **Assumptions/Defaults**
   - The service assumes several default variables such as:
     - Specific heat capacity of water (4.186 J/g°C)
     - Ambient temperature (20°C)
     - Inlet water temperature (20°C)
     - EWH initial water temperature (60°C)
     - EWH overall heat transfer coefficient (0.00125 kW/(m2*K))
     - EWH height (100 cm)
     - Total flow rate (8.5 l/min)


***

## Contacts

If you have any questions regarding this project, please contact the following people:

**Developers (SW source code / methodology questions)**:
* José Paulos (jose.paulos@inesctec.pt)
