from ewh_flex import ewh_optimization
from ewh_flex import plot_results_plotly
from ewh_flex import return_results
from ewh_flex import gui_data
from ewh_flex import is_valid_time_format
import streamlit as st
import datetime
import json
import pandas as pd
import os


##############################################
##          Streamlit Main Page             ##
##############################################

st.set_page_config(
    page_title="ewh-flex",
    page_icon='./docs/figures/inesctec_small.png')

st.image('./docs/figures/inesctec.png')
st.title('EWH Optimization and Flexibility')


st.write('This tool focuses on optimizing the functioning calendar of thermoelectric water heaters (EWH) through the '
         'analysis of a limited dataset. The primary goal is to identify and estimate periods during which flexibility '
         'can be introduced by enhancing the operation of the EWH. By utilizing only the electrical consumption data of '
         'the appliance as input, the tool calculates optimal periods for initiating EWH operation. This ensures the '
         'delivery of consumer-defined comfort levels, subject to certain constraints, while simultaneously minimizing '
         'operational costs or total energy consumption. The tool offers a practical solution for enhancing the '
         'efficiency and cost-effectiveness of thermoelectric water heaters based on consumption data analysis.')

st.divider()

st.header('EWH Specifications')


# Disable the submit button after it is clicked
def disable():
    st.session_state.disabled = True
# Initialize disabled for form_submit_button to False
if "disabled" not in st.session_state:
    st.session_state.disabled = False


# request EWH Specifications
ewh_capacity = st.number_input('EWH Capacity (liters)', value=100)
if ((ewh_capacity >= 30) & (ewh_capacity <= 300)) == False:
    st.error("Enter a value between 30 and 300")

ewh_power_choice = st.radio(
        "EWH Power",
        ["Auto-Detect","Specify the EWH Power (watt)"])

if ewh_power_choice == "Auto-Detect":
    ewh_power = 0
if ewh_power_choice == "Specify the EWH Power (watt)":
    ewh_power = st.number_input('EWH Power (watt)', value=1800)
    if ((ewh_power >= 500) & (ewh_power <= 3000)) == False:
        st.error("Enter a value between 500 and 3000")

ewh_max_temp = st.number_input('EWH maximum allowed temperature (°C)', value=80)
if ((ewh_max_temp >= 60) & (ewh_max_temp <= 100)) == False:
    st.error("Enter a value between 60 and 100")

ewh_stf_temp = st.number_input('EWH standard non-optimized functioning water temperature (°C)', value=60)
if ((ewh_stf_temp >= 40) & (ewh_stf_temp <= 80)) == False:
    st.error("Enter a value between 40 and 80")

user_comf_temp = st.number_input('Hot-Water Usage Comfort Temperature (°C)', value=40)
if ((user_comf_temp >= 20) & (user_comf_temp <= 60)) == False:
    st.error("Enter a value between 20 and 60")


pricing_choice = st.radio(
        "Pricing Source",
        ["None", "Price per kWh & Daily Tariff (€)", "Upload pricing diagram"],
        captions=("Run optimization based only on energy consumption.",
                  "Select between daily/dual tariff, and provide pricing per kWh and daily access tariff.",
                  "Upload a JSON/CSV file comprising only timestamp and price data. Must respect the EWH load period length and resolution."))


if pricing_choice == "None":
    tariff = 0
    price_simple = 0
    tariff_simple = 0
    price_dual_day = 0
    price_dual_night = 0
    tariff_dual = 0
if pricing_choice == "Price per kWh & Daily Tariff (€)":
    pricing_choice = 'fixed'
    tariff_selector = st.selectbox('Simple or Dual Daily Tariff', ('Simple', 'Dual'))
    if tariff_selector == 'Simple':
        tariff = 1
        price_simple = st.number_input('Price per kWh (€)', value=0.12)
        tariff_simple = st.number_input('Daily Tariff (€)', value=0.36)
        price_dual_day = 0
        price_dual_night = 0
        tariff_dual = 0
    else:
        tariff = 2
        price_dual_day = st.number_input('Price per kWh during the day period (€)', value=0.15)
        price_dual_night = st.number_input('Price per kWh during the night period (€)', value=0.08)
        tariff_dual = st.number_input('Daily Tariff', value=0.43)
        price_simple = 0
        tariff_simple = 0
if pricing_choice == "Upload pricing diagram":
    price_dynamic = st.file_uploader("Choose a file", key='price_dynamic')
    price_simple = 0
    price_dual_day = 0
    price_dual_night = 0
    tariff_dual = 0
    tariff_simple = 0
    tariff = 3


st.divider()

st.header('EWH Usage')

st.write('Select the source for EWH usage data:')
st.write('* EWH load diagram time-series dataset from Data Space or uploaded JSON/CSV, comprising only timestamps and electrical consumption data (in watts) with minute resolution. This alternative provides results with higher precision. Maximum of 30 days.')
st.write('* EWH daily usage example with periods and durations of hot-water usage. This alternative provides results with lower precision. Maximum of 24h.')

# load or calendar input
inputType = st.radio('What kind of input do you want to provide?',
                     ('Data Space',
                      'Upload JSON/CSV',
                      'Hot-Water Usage Example'),
                     captions = ("Source EWH Load Diagram data with 1-min resolution from the Data Space",
                                 "Upload a JSON or CSV with the EWH Load Diagram Time-Series with 1-min resolution",
                                 "I don't have a Load Diagram file. Fill in a daily basis typical calendar"))

st.divider()

if (inputType == 'Data Space'):
    load_diagram_exists = 1

    # data source
    data_source = st.radio(
        "What's your Data Space source?",
        ["In-Data", "SEL"],
        captions=["In-Data/Sentinel", "Smart Energy Lab"])

    if data_source == "In-Data":
        endpoint = 'indata'
    else:
        endpoint = 'sel'

    ## token input
    user_id = st.text_input("User Access Token", "Replace with user access token, e.g.: 123456abcdef")

    ## date input
    today = datetime.datetime.today()
    limit_start_date = datetime.date(today.year - 1, 1, 1)
    limit_end_date = datetime.date(today.year, today.month, today.day - 1)
    default_start_date = today - datetime.timedelta(days=7)
    default_end_date = today - datetime.timedelta(days=1)

    simulation_period = st.date_input(
        "Select the period to optimize (max. 30 Days)",
        (default_start_date, default_end_date),
        limit_start_date, limit_end_date,
        format="DD/MM/YYYY",
    )
    if len(simulation_period) > 1:
        datetime_start = simulation_period[0]
        datetime_end = simulation_period[1]
        if ((((datetime_end - datetime_start).days+1) < 1) | ((datetime_end - datetime_start).days > 30)):
            st.error("Select a date range within 1-30 days")
    else:
        st.error("Select a date range (missing end date)")


elif (inputType == 'Upload JSON/CSV'):
    dataset = st.file_uploader("Choose a file", key='dataset')
    load_diagram_exists = 1

elif (inputType == 'Hot-Water Usage Example'):
    # load or calendar input
    usageType = st.radio(' ',
                         ('Hot-Water Usage CSV',
                          'Hot-Water Usage 24-hour Example'),
                         captions=("Upload a CSV with the hot-water usage calendar with start and duration (minutes) variables",
                                   "Fill in a daily basis 24-hours hot water usage typical calendar"),
                         label_visibility="collapsed")

    if (usageType == 'Hot-Water Usage CSV'):
        dataset = st.file_uploader("Choose a file", key='dataset')
        load_diagram_exists = 3

    elif (usageType == 'Hot-Water Usage 24-hour Example'):
        load_diagram_exists = 0
        usage_data = st.columns(2)
        # a selection for the user to specify the number of rows
        num_rows = st.slider('Number of Hot-Water Usages', min_value=1, max_value=10)
        # columns to lay out the inputs
        grid = st.columns(2)

        # Function to create a row of widgets (with row number input to assure unique keys)
        def add_row(row):
            with grid[0]:
                st.text_input('Start Period (HH\:MM)', key=f'start_{row}', value='08:00')
                if is_valid_time_format(st.session_state[f'start_{row}']) == False:
                    st.error(f"Please insert a valid starting time value (HH\:MM).")
            with grid[1]:
                st.number_input('Duration (minutes)', step=1, key=f'duration_{row}', value=5)
                if not ((st.session_state[f'duration_{row}'] > 0) & (st.session_state[f'duration_{row}'] <= 20)):
                    st.error(f"Please insert a valid duration between 1 and 20 minutes.")

        # Loop to create rows of input widgets
        for r in range(num_rows):
            add_row(r)

if 'dataset' in locals():
    if dataset is not None:
        if ((dataset.type == 'application/json') | (dataset.type == 'text/csv') | (dataset.type == 'application/vnd.ms-excel')) == False:
            st.error(f"Please upload the dataset in JSON or CSV format!")

if 'price_dynamic' in locals():
    if price_dynamic is not None:
        if ((price_dynamic.type == 'application/json') | (price_dynamic.type == 'text/csv') | (dataset.type == 'application/vnd.ms-excel')) == False:
            st.error(f"Please upload the dataset in JSON or CSV format!")


with st.form(key='form'):
    if (inputType == 'Upload JSON/CSV'):
        if dataset is None:
            submit_button = st.form_submit_button("Run", disabled=True)
        else:
            if ((dataset.type == 'application/json') | (dataset.type == 'text/csv') | (dataset.type == 'application/vnd.ms-excel')) == False:
                submit_button = st.form_submit_button("Run", disabled=True)
            else:
                submit_button = st.form_submit_button("Run", on_click=disable, disabled=st.session_state.disabled)
    else:
        submit_button = st.form_submit_button("Run", on_click=disable, disabled=st.session_state.disabled)


guiBackpack = {}
guiBackpack['load_diagram_exists'] = load_diagram_exists
guiBackpack['ewh_capacity'] = ewh_capacity
guiBackpack['ewh_power'] = ewh_power
guiBackpack['ewh_max_temp'] = ewh_max_temp
guiBackpack['ewh_stf_temp'] = ewh_stf_temp
guiBackpack['user_comf_temp'] = user_comf_temp
guiBackpack['tariff'] = tariff
guiBackpack['price_simple'] = price_simple
guiBackpack['tariff_simple'] = tariff_simple
guiBackpack['price_dual_day'] = price_dual_day
guiBackpack['price_dual_night'] = price_dual_night
guiBackpack['tariff_dual'] = tariff_dual
guiBackpack['pricing_choice'] = pricing_choice
if pricing_choice == "Upload pricing diagram":
    guiBackpack['price_dynamic'] = price_dynamic
if inputType == 'Data Space':
    guiBackpack['endpoint'] = endpoint
    guiBackpack['inputType'] = 'Data Space'
    guiBackpack['user_id'] = user_id
if 'datetime_start' in locals():
    guiBackpack['datetime_start'] = datetime_start
if 'datetime_end' in locals():
    guiBackpack['datetime_end'] = datetime_end
if inputType == 'Upload JSON/CSV':
    guiBackpack['inputType'] = 'Upload JSON/CSV'
if inputType == 'Hot-Water Usage Example':
    guiBackpack['inputType'] = 'Hot-Water Usage Example'
if 'dataset' in locals():
    guiBackpack['dataset'] = dataset
    if dataset is not None:
        if dataset.type == 'application/json':
            guiBackpack['file_type'] = 'json'
        elif (dataset.type == 'text/csv') | (dataset.type == 'application/vnd.ms-excel'):
            guiBackpack['file_type'] = 'csv'
guiBackpack['session_state'] = st.session_state
if 'num_rows' in locals():
    guiBackpack['num_rows'] = num_rows




if submit_button:
    if (inputType == 'Upload JSON/CSV'):
        if dataset is None:
            st.error(f"Please upload the dataset!")
            st.stop()

    with st.spinner('Running Optimization... Please Wait!'):


        ##############################################
        ##             Prepare Data                 ##
        ##############################################

        dataset, paramsInput = gui_data(guiBackpack)

        # Abort if larger than 30-days
        if dataset is None:
            st.warning('The file contains data with more than 30 days. Please refresh and upload new data.')
            st.stop()
            sys.exit()

        ##############################################
        ##              Optimization                ##
        ##############################################

        # Select Solver between 'HiGHS' (recommended) and 'CBC'. HiGHS solver requires 'solverPath' to respective binaries
        # Select resample between 'no','15m','1h'
        opt_output = ewh_optimization(paramsInput, dataset, resample='no', optSolver='HiGHS', solverPath=r'./HiGHS/bin/highs.exe')

        ##############################################
        ##              Plot Results                ##
        ##############################################

        ## Select plot option between showing plot ('p') or writing ('w'). If writing, fill writePath
        fig = plot_results_plotly(opt_output, plotOption='p')

        ##############################################
        ##              Return Results              ##
        ##############################################

        results = return_results(opt_output)





        st.success('✅ Done! Check Results Below!')

        st.divider()
        st.header('📊 Results')

        relative_savings = 100 * (opt_output['optimized_load'] - opt_output['original_load']) / opt_output['original_load']
        col1, col2, col3 = st.columns(3)
        col1.metric("🔌 Original Load", (('%.2f' % opt_output['original_load']) + ' kWh'))
        col2.metric("🔌 Optimized Load", (('%.2f' % opt_output['optimized_load']) + ' kWh'),
                    delta=(('%.2f' % relative_savings) + '%'), delta_color='inverse')
        col3.metric("🗓️ Simulated Period", (str(opt_output['simulated_period']) + ' Days'))

        _hours = '%.0f' % (opt_output['total_flexibility'] // 60)
        _minutes = '%.0f' % (opt_output['total_flexibility'] % 60)
        pricing_diff = opt_output['optimized_price'] - opt_output['original_price']
        total_flex = "{}h {}m".format(_hours, _minutes)
        col4, col5, col6 = st.columns(3)
        col4.metric("💶 Original Pricing", (('%.2f' % opt_output['original_price']) + ' €'))
        col5.metric("💶 Optimized Pricing", (('%.2f' % opt_output['optimized_price']) + ' €'),
                    delta=(('%.2f' % pricing_diff) + '€'), delta_color='inverse')
        col6.metric("📈 Total Flexibility", total_flex)

        # Add plot via plotly
        st.plotly_chart(fig)

        json_string = json.dumps(results)
        st.download_button(
            label="📄 Download Results JSON",
            file_name="results.json",
            mime="application/json",
            data=json_string,
        )

        st.divider()
        st.header('🏆 Ranking')
        st.write("This section shows the top-10 results comparing several users' savings.")

        # open ranking log file
        # Get the absolute path to the CSV file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, '.', 'ewh_flex', 'ranking.csv')
        ranking = pd.read_csv(csv_path)
        # open ranking log file
        ranking = pd.read_csv(csv_path)
        # convert index to rank
        ranking.index = ranking.index + 1
        ranking.reset_index(drop=False, inplace=True)
        ranking = ranking.rename(columns={"index": "rank"})
        # find current ranking
        current_rank = ranking.loc[ranking['timestamp'] == opt_output['ranking']['timestamp'].values[0],'rank']

        col7, col8, col9 = st.columns(3)
        col7.metric("⏬ Competition Savings", (('%.2f' % opt_output['ranking']['savings']) + ' %'))
        col8.metric("⭐ Points", (('%.2f' % opt_output['ranking']['points'])))
        col9.metric("🏆 Rank", (('%d' % current_rank)))

        # apply color coding to lines, to highlight the current (if present)
        def color_coding(row):
            if row.timestamp == opt_output['ranking']['timestamp'].values[0]:
                return ['background-color:darkgreen'] * len(row)
            else:
                return [''] * len(row)

        # Custom formatting for the 'points' column with emojis for the top 3 rows
        def add_emoji_to_rank(val, row_index):
            if row_index == 0:  # First row
                return f"🥇 {val}"
            elif row_index == 1:  # Second row
                return f"🥈 {val}"
            elif row_index == 2:  # Third row
                return f"🥉 {val}"
            else:  # Other rows, no emoji
                return f"{val}"

        # show only the top10 (if available)
        ranking = ranking.head(10)
        # ranking = ranking.apply(color_coding, axis=1)

        st.dataframe(
            ranking.style.format({
                'savings': '{:.2f}',  # Keep savings column format
                'rank': lambda val: add_emoji_to_rank(val, ranking.index[ranking['rank'] == val][0])
            }).apply(color_coding, axis=1),
            column_config={
                "rank": st.column_config.NumberColumn(
                    "Rank",
                    help="Current Top-10 ranking position",
                ),
                "timestamp": st.column_config.DatetimeColumn(
                    "Simulation Date",
                    help="Date and time of simulation",
                ),
                "duration": st.column_config.TextColumn(
                    "Duration",
                    help="Optimized period length",
                ),
                "savings": st.column_config.NumberColumn(
                    "Savings (%)",
                    format="%f",
                    help="Relative savings, compared to original load",
                ),
                "points": st.column_config.ProgressColumn(
                    "Points",
                    help="Ranking points (up to 100). Requires more than 1-day of simulation",
                    format="  %f ⭐",
                    min_value=0,
                    max_value=100,
                ),
            },
            hide_index=True,
        )