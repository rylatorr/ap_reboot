#!/usr/bin/python3

READ_ME = '''
=== PREREQUISITES ===
Run in Python 3

Assign network tag "ap_reboot" to all networks that you want APs rebooted.

Install both requests & Meraki Dashboard API Python modules:
pip[3] install --upgrade requests
pip[3] install --upgrade meraki

=== DESCRIPTION ===
This script iterates through the org's networks that are tagged with the label
"ap_reboot". For each of these networks'
Remove the network tag/label "ap_reboot" afterwards.

=== USAGE ===
python[3] ap_reboot.py -k <api_key> -o <org_id> [-m <mode>]
** mode arg not implemented - running this will reboot all APs in networks with the tag. Immediately.
The optional -m parameter is either "simulate" (default) to only print changes,
or "commit" to also apply those changes to Dashboard.
'''

from datetime import datetime
import getopt
import logging
import sys
import time
from meraki import meraki
import requests

# Prints READ_ME help message for user to read
def print_help():
    lines = READ_ME.split('\n')
    for line in lines:
        print('# {0}'.format(line))

logger = logging.getLogger(__name__)

def configure_logging():
    logging.basicConfig(
        filename='{}_log_{:%Y%m%d_%H%M%S}.txt'.format(sys.argv[0].split('.')[0], datetime.now()),
        level=logging.DEBUG,
        format='%(asctime)s: %(levelname)7s: [%(name)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# Reboot a single device
# https://api.meraki.com/api_docs#reboot-a-device
def rebootdevice(apikey, networkid, serial, suppressprint=False):
    base_url = 'https://api.meraki.com/api/v0'
    calltype = 'Device'
    posturl = '{0}/networks/{1}/devices/{2}/reboot'.format(
        str(base_url), str(networkid), str(serial))
    headers = {
        'x-cisco-meraki-api-key': format(str(apikey)),
        'Content-Type': 'application/json'
    }
    dashboard = requests.post(posturl, headers=headers)
    #
    # Call return handler function to parse Dashboard response
    #
    result = meraki.__returnhandler(
        dashboard.status_code, dashboard.text, calltype, suppressprint)
    return result

def main(argv):
    # Set default values for command line arguments
    api_key = org_id = arg_mode = None

    # Get command line arguments
    try:
        opts, args = getopt.getopt(argv, 'hk:o:m:')
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt == '-k':
            api_key = arg
        elif opt == '-o':
            org_id = arg
        elif opt == '-m':
            arg_mode = arg

    # Check if all required parameters have been input
    if api_key == None or org_id == None:
        print_help()
        sys.exit(2)

    # Assign default mode to "simulate" unless "commit" specified
    if arg_mode != 'commit':
        arg_mode = 'simulate'

    # Get list of current networks in org
    networks = meraki.getnetworklist(api_key, org_id)

    # Iterate through all networks
    for network in networks:
        # Skip if network does not have the tag "ap_reboot"
        if network['tags'] is None or 'ap_reboot' not in network['tags']:
            continue

        # Iterate through a "ap_reboot" network's devices
        devices = meraki.getnetworkdevices(api_key, network['id'])

        # Reboot APs
        for device in devices:
            if "MR" in device['model']:
                logger.info('Rebooting ' + device['serial'])
                rebootdevice(api_key, network['id'], device['serial'])
                time.sleep(0.2)

if __name__ == '__main__':
    # Configure logging to stdout
    configure_logging()
    # Define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # Set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # Tell the handler to use this format
    console.setFormatter(formatter)
    # Add the handler to the root logger
    logging.getLogger('').addHandler(console)

    # Output to logfile/console starting inputs
    start_time = datetime.now()
    logger.info('Started script at {0}'.format(start_time))
    inputs = sys.argv[1:]
    try:
        key_index = inputs.index('-k')
    except ValueError:
        print_help()
        sys.exit(2)
    inputs.pop(key_index+1)
    inputs.pop(key_index)
    logger.info('Input parameters: {0}'.format(inputs))

    main(sys.argv[1:])

    # Finish output to logfile/console
    end_time = datetime.now()
    logger.info('Ended script at {0}'.format(end_time))
    logger.info(f'Total run time = {end_time - start_time}')
