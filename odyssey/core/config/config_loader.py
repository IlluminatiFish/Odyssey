import json
import sys


working_directory = sys.path[1]
configuration_file_path = working_directory + '\\odyssey.json'

odyssey_config = open(configuration_file_path)
odyssey_config_json = dict(json.load(odyssey_config))

USER_AGENT = odyssey_config_json.get('USER_AGENT', 'Mozilla/5.0')
SEGMENT_BUFFER = odyssey_config_json.get('SEGMENT_BUFFER', 4096)
TRACKING_COOKIES = odyssey_config_json.get('TRACKING_COOKIES', [])
CLEAR_COOKIES = odyssey_config_json.get('CLEAR_COOKIES', [])
DISPLAY_TRACKERS = odyssey_config_json.get('DISPLAY_TRACKERS', True)
TRACEROUTE_MAP_FILENAME = odyssey_config_json.get('TRACEROUTE_MAP_FILENAME', 'traceroute.html')

if TRACEROUTE_MAP_FILENAME == "":
    TRACEROUTE_MAP_FILENAME = "traceroute.html"

IP_LOGGERS = odyssey_config_json.get('IP_LOGGERS', [])
