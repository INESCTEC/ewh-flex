##############################################
##              TSG-Client                  ##
##############################################

from dotenv import dotenv_values, find_dotenv
from tsg_client.controllers import TSGController
import os

def dataspace_connection(guiBackpack):

    # unpack data from GUI
    endpoint = guiBackpack['endpoint']
    user_id = guiBackpack['user_id']
    datetime_start = guiBackpack['datetime_start']
    datetime_end = guiBackpack['datetime_end']

    # Find dotenv
    found_dotenv = find_dotenv('.env')
    # Load environment variables:
    config = dotenv_values(found_dotenv)

    if endpoint == 'sentinel':
        # Sentinel Endpoint
        EXTERNAL_CONNECTOR = {
            "CONNECTOR_ID": 'urn:ids:enershare:connectors:connector-sentinel',
            "ACCESS_URL": 'https://connector-sentinel.enershare.inesctec.pt',
            "AGENT_ID": 'urn:ids:enershare:participants:INESCTEC-CPES'
        }
    else:
        # SEL Endpoint
        EXTERNAL_CONNECTOR = {
            "CONNECTOR_ID": 'urn:ids:enershare:connectors:connector-sentinel',
            "ACCESS_URL": 'https://connector-sentinel.enershare.inesctec.pt',
            "AGENT_ID": 'urn:ids:enershare:participants:INESCTEC-CPES'
        }

    # Connect to our TSG connector:
    conn = TSGController(
        api_key=config['API_KEY'],
        connector_id=config['CONNECTOR_ID'],
        access_url=config['ACCESS_URL'],
        agent_id=config['AGENT_ID'],
        metadata_broker_url=config['METADATA_BROKER_URL']
    )

    # Get external connector info (self-descriptions):
    self_description = conn.get_connector_selfdescription(
        access_url=EXTERNAL_CONNECTOR['ACCESS_URL'],
        connector_id=EXTERNAL_CONNECTOR['CONNECTOR_ID'],
        agent_id=EXTERNAL_CONNECTOR['AGENT_ID']
    )

    # parameters
    params = {
        'shelly_id': user_id,
        'phase': 'total',
        'parameter': 'instant_active_power',
        'start_date': datetime_start.strftime('%Y-%m-%d 00:00'),
        'end_date': datetime_end.strftime('%Y-%m-%d 23:59'),
    }

    # Get external connector OpenAPI specs:
    api_version = "1.0.0"
    open_api_specs = conn.get_openapi_specs(self_description, api_version)
    endpoint = '/dataspace/inesctec/observed/ceve_living-lab/metering/energy'
    data_app_agent_id = open_api_specs[0]["agent"]

    print(f"""
    Performing a request to:
    - Agent ID: {data_app_agent_id}
    - API Version: {api_version}
    - Endpoint: {endpoint}
    """)

    AUTH = {'Authorization': 'Token {}'.format(config['TOKEN'])}

    # Execute external OpenAPI request:
    response = conn.openapi_request(
        headers=AUTH,
        external_access_url=EXTERNAL_CONNECTOR['ACCESS_URL'],
        data_app_agent_id=data_app_agent_id,
        api_version=api_version,
        endpoint=endpoint,
        params=params,
        method="get"
    )

    print("-" * 79)
    print(f"> Connector {EXTERNAL_CONNECTOR['CONNECTOR_ID']} RESPONSE:")
    print("Status Code:", response.status_code)
    # print("Response Text:", response.text)
    print("-" * 79)

    return response