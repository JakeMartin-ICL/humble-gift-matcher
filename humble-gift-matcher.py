#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from humble_gift_matcher.config_data import ConfigData
from humble_gift_matcher.configuration import Configuration
from humble_gift_matcher.humble_api.humble_api import HumbleApi
from humble_gift_matcher.actions import Action
from steam import webauth


print("Humble Bundle Gift Matcher v%s" % ConfigData.VERSION)
print("This program is not affiliated nor endorsed by Humble Bundle, Inc.")
print("For any suggestion or bug report, please create an issue at:\n%s\n" %
      ConfigData.BUG_REPORT_URL)

# Determine which configuration file we want to use.
user_config_filename = os.path.expanduser("~/.config/%s" % ConfigData.config_filename)
system_config_filename = "/etc/%s" % ConfigData.config_filename
local_config_filename = "%s/%s" % (os.getcwd(), ConfigData.config_filename)
final_config_filename = None

# Assignment is in reverse order of priority.  Last file to exist is the one used.
if os.path.isfile(local_config_filename):
    final_config_filename = local_config_filename
if os.path.isfile(system_config_filename):
    final_config_filename = system_config_filename
if os.path.isfile(user_config_filename):
    final_config_filename = user_config_filename

if final_config_filename is None:
    exit("No configuration file found.\nLocations searched:\nUser: %s\nSystem: %s\nLocal: %s\n" %
        (user_config_filename, system_config_filename, local_config_filename))

# Load the configuration from the YAML file...
try:
    print("Loading configuration from %s" % final_config_filename)
    Configuration.load_configuration(final_config_filename)
    print("Configuration successfully loaded from %s" % final_config_filename)
except FileNotFoundError:
    exit("Configuration file was identified but could not be read.")

Configuration.parse_command_line()

validation_status, message = Configuration.validate_configuration()
if not validation_status:
    print(message)
    exit("Invalid configuration.  Please check your command line arguments and "
         "hb-downloader-settings.yaml.")
    
hapi = HumbleApi(ConfigData.auth_sess_cookie)

if not hapi.check_login():
        exit("Login to humblebundle.com failed."
             "  Please verify your authentication cookie")

password = input("Enter Steam password: ") if ConfigData.steam_password == "" else ConfigData.steam_password
user = webauth.WebAuth2()
steam_session = user.login(ConfigData.steam_username, password)

Action.match_games_with_friends(hapi, steam_session)

exit()
