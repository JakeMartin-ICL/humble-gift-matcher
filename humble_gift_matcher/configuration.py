#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import yaml
from humble_gift_matcher.config_data import ConfigData


class Configuration(object):
    @staticmethod
    def validate_configuration():
        """
            Does a basic validation of the configuration to ensure we're not
            missing anything critical.

            :return:  None
        """

        return True, ""

    @staticmethod
    def load_configuration(config_file):
        """
            Loads configuration data from a yaml file.

            :param config_file:  The yaml file to load configuration data from.
            :return:  None
        """
        with open(config_file, "r") as f:
            saved_config = yaml.safe_load(f)

        ConfigData.debug = saved_config.get("debug", ConfigData.debug)
        ConfigData.auth_sess_cookie = saved_config.get("session-cookie", ConfigData.auth_sess_cookie)
        ConfigData.steam_api_key = saved_config.get("steam-api-key", ConfigData.steam_api_key)
        ConfigData.steam_user_id = saved_config.get("steam-user-id", ConfigData.steam_user_id)
        ConfigData.steam_username = saved_config.get("steam-username", ConfigData.steam_username)
        ConfigData.steam_password = saved_config.get("steam-password-optional", ConfigData.steam_password)

    @staticmethod
    def parse_command_line():
        """
            Parses configuration options from the command line arguments to the
            script.

            :return:  None
        """
        parser = argparse.ArgumentParser()

        parser.add_argument("-d", "--debug", action="store_true",
                            default=ConfigData.debug,
                            help="Activates debug mode.")
        parser.add_argument(
                "-c", "--auth_cookie",
                default=ConfigData.auth_sess_cookie, type=str,
                help="The _simple_auth cookie value from a web browser")

        sub = parser.add_subparsers(
                title="action", dest="action",
                help=("Action to perform, optionally restricted to a few "
                      "specifiers. If no action is specified, the tool "
                      "defaults to downloading according to the configuration "
                      "file. Please note that specifying an action WILL"
                      "override the configuration file."))

        a_list = sub.add_parser("match", help=(
                "Match unredeemed games with friend's wishlists."))

        args = parser.parse_args()

        Configuration.configure_action(args)

        ConfigData.debug = args.debug
        ConfigData.auth_sess_cookie = args.auth_cookie

    @staticmethod
    def configure_action(args):
        if args.action is not None:
            pass
        else:
            args.action = "download"
        ConfigData.action = args.action