import json, sys

software_directory = sys.path[1]
odyssey_config = open(software_directory + '\\config.json')

odyssey_config_json = json.load(odyssey_config)

# Load constants into software from configuration file
USER_AGENT = odyssey_config_json['USER_AGENT']
SEGMENT_BUFFER = odyssey_config_json['SEGMENT_BUFFER']
TRACKING_COOKIES = odyssey_config_json['TRACKING_COOKIES']
CLEAR_COOKIES = odyssey_config_json['CLEAR_COOKIES']