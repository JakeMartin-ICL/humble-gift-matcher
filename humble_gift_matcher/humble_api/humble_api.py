#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from alive_progress import alive_bar
import http.cookiejar
import itertools
from typing import Dict, List
from rapidfuzz import process, fuzz
from .model.game import Game
from .model.product import Product
import json
import requests
from .exceptions.humble_response_exception import HumbleResponseException
from .exceptions.humble_parse_exception import HumbleParseException
from .exceptions.humble_authentication_exception import HumbleAuthenticationException


class HumbleApi(object):
    """
        This class represents common actions for the Humble API.

        The Humble Bundle API is not stateless, it stores an authentication token as a cookie named _simpleauth_sess

        The Requests.Session handles storing the auth token. To load some persisted cookies simply set session.cookies
        after initialization.
    """

    # URLs.
    LOGIN_URL = "https://www.humblebundle.com/processlogin"
    ORDER_LIST_URL = "https://www.humblebundle.com/api/v1/user/order"
    ORDER_URL = "https://www.humblebundle.com/api/v1/order/{order_id}"
    ORDERS_URL = "https://www.humblebundle.com/api/v1/orders"

    # default_headers specifies the default HTTP headers added to each request sent to the humblebundle.com servers.
    default_headers = {
        "Accept": "application/json",
        "Accept-Charset": "utf-8",
        "Keep-Alive": "true",
        "X-Requested-By": "hb_android_app",
        "User-Agent": "Apache-HttpClient/UNAVAILABLE (java 1.4)"
    }

    # default_params specifies the default querystring parameters added to each
    # request sent to humblebundle.com.
    default_params = {"ajax": "true"}

    def __init__(self, auth_sess_cookie):
        """
            Base constructor.  Responsible for setting up the requests object
            and cookie jar. All configuration values should be set prior to
            constructing an object of this type; changes to configuration will
            not take effect on variables which already exist.
        """
        self.session = requests.Session()

        auth_sess_cookie = bytes(
                auth_sess_cookie, "utf-8").decode("unicode_escape")
        cookie = http.cookiejar.Cookie(
                0, "_simpleauth_sess", auth_sess_cookie, None, None,
                "www.humblebundle.com", None, None, "/", None, True,
                None, False, None, None, None)
        self.session.cookies.set_cookie(cookie)

        self.session.headers.update(self.default_headers)
        self.session.params.update(self.default_params)

    def check_login(self):
        """
            Checks to see if we have a valid session cookie by attempting to retrieve the orders page.
            If we get a HumbleAuthenticationException then we need to log in to the system again.
            Otherwise we're good to go.

            We can't just check for the cookie existence.  The session ID might've been
            invalidated server side.

            :return: True if the _simpleauth_sess cookie has been set, False if not.
        """
        try:
            gamekeys = self.get_orders()
            if len(gamekeys) > 0:
                return True
            else:
                return False
        except HumbleAuthenticationException:
            return False

    def get_orders(self, *args, **kwargs):
        """
            Fetch all the gamekeys owned by an account.

            A gamekey is a string that uniquely identifies an order from the Humble store.

            :param list args: (optional) Extra positional args to pass to the request
            :param dict kwargs: (optional) Extra keyword args to pass to the request
            :return: A list of gamekeys
            :rtype: list
            :raises RequestException: if the connection failed
            :raises HumbleAuthenticationException: if not logged in
            :raises HumbleResponseException: if the response was invalid
        """
        response = self._request("GET", HumbleApi.ORDER_LIST_URL, *args, **kwargs)

        """ get_gamekeys response always returns JSON """
        data = self.__parse_data(response)

        if isinstance(data, list):
            return [v["gamekey"] for v in data]

        # Let the helper function raise any common exceptions
        self.__authenticated_response_helper(response, data)

        # We didn't get a list, or an error message
        raise HumbleResponseException("Unexpected response body", request=response.request, response=response)
        
    def get_orders_with_details(self, appid_lookup: Dict[str, str], *args, **kwargs):
        """
            Fetch all the gamekeys owned by an account.

            A gamekey is a string that uniquely identifies an order from the Humble store.

            :param list args: (optional) Extra positional args to pass to the request
            :param dict kwargs: (optional) Extra keyword args to pass to the request
            :return: A list of gamekeys
            :rtype: list
            :raises RequestException: if the connection failed
            :raises HumbleAuthenticationException: if not logged in
            :raises HumbleResponseException: if the response was invalid
        """
        print("[Info] Fetching order list.")
        response = self._request("GET", HumbleApi.ORDER_LIST_URL, *args, **kwargs)

        """ get_gamekeys response always returns JSON """
        data = self.__parse_data(response)

        if not isinstance(data, list):
            # Let the helper function raise any common exceptions
            self.__authenticated_response_helper(response, data)

            # We didn't get a list, or an error message
            raise HumbleResponseException("Unexpected response body", request=response.request, response=response)

        keys = [v["gamekey"] for v in data]
        print(f"[Info] {len(keys)} orders found.")
        paginated_keys = [keys[i:i+25] for i in range(0, len(keys), 25)]

        orders_json = {}
        with alive_bar(len(keys)) as bar:
            bar.title("[Info] Fetching order details")
            for keys_chunk in paginated_keys:
                payload = {"all_tpkds": "true", "gamekeys": keys_chunk}
                response_with_details = self._request("GET", HumbleApi.ORDERS_URL, params=payload)
                data_chunk = self.__parse_data(response_with_details)
                orders_json.update(data_chunk)
                bar(len(keys_chunk))
        
        games: List[Game] = []
        with alive_bar(len(keys)) as bar:
            bar.title("[Info] Parsing games from orders")
            for order in orders_json.values():
                product = Product(order["product"])
                tpks = order["tpkd_dict"]["all_tpks"]
                bar.text(f"{product.human_name}: {len(tpks)} keys")
                for game in tpks:
                    games.append(Game(game, product.human_name))
        print(f"[INFO] Found {len(games)}")
        
        try:
            with open('humble_steam_matches.json', 'r') as f:
                previous_run_matches = json.load(f)
            print(f"[INFO] Found {len(previous_run_matches)} matches from previous runs.")
        except:
            print("[WARN] No record of matches from previous runs found.")
            previous_run_matches = {}

        unmatched_games = []
        with alive_bar(len(games)) as bar:
            bar.title("[Info] Matching Humble games with Steam appids.")
            for game in games:
                bar.text(game.name)
                if game.steam_app_id is None:
                    appid = appid_lookup.get(game.name, None)
                    if appid is None:
                        appid = previous_run_matches.get(game.name, None)
                        if appid is None:
                            unmatched_games.append(game)
                    game.steam_app_id = appid
                bar()

        if unmatched_games:
            print(f"[Info] {len(unmatched_games)} games still have no appid. Attempting fuzzy match")
            name_list = appid_lookup.keys()
            for game in unmatched_games:
                match_options = [title for (title, _, _) in process.extract(game.name, name_list, scorer=fuzz.WRatio, limit=10)]
                print(f"\nWhich number is the correct match for: {game.name}")
                for i, option in enumerate(match_options):
                    print(f"({i+1}) {option}")
                print("(0) Skip for this run")
                print("(-) Skip always")
                response = input()
                if response == "":
                    steam_name = match_options[0]
                elif response == "0":
                    previous_run_matches[game.name] = -1
                    continue
                elif response == "-":
                    continue

                try:
                    steam_name = match_options[int(response) - 1]
                    game.steam_app_id = appid_lookup.get(steam_name) 
                    previous_run_matches[game.name] = game.steam_app_id
                except:
                    print(f"[WARN] {game.name} remains unmatched")

            print("[INFO] Saving matches for future use.")
            with open('humble_steam_matches.json', 'w') as f:
                json.dump(previous_run_matches, f)

        return games


    def _request(self, *args, **kwargs):
        """
            Set sane defaults that aren't session wide. Otherwise maintains the API of Session.request.

            :param list args: (optional) Extra positional args to pass to the request.
            :param dict kwargs: (optional) Extra keyword args to pass to the request.
        """
        kwargs.setdefault("timeout", 30)
        return self.session.request(*args, **kwargs)

    def __authenticated_response_helper(self, response, data):
        """
            Checks a response for the common authentication errors.  Sometimes a successful API call won't have a
             success property.  We do a check for this property and return true if found, otherwise we parse for
s             errors.

            :param response:  The response received from humblebundle.com. A pass through variable used to initialize
             the exceptions.
            :param data:  The interpreted JSON data from the response.
            :return:  True if the API call was successful.  Otherwise an exception is thrown.
            :raises HumbleAuthenticationException: If not logged in.
            :raises HumbleResponseException: If the response was invalid.
        """
        success = data.get("success", None)
        if success:
            return True

        error_id = data.get("error_id", None)
        errors, error_msg = self.__get_errors(data)

        # API calls that require login and have a missing or invalid token.
        if error_id == "login_required":
            raise HumbleAuthenticationException(error_msg, request=response.request, response=response)

        # Something happened, we're not sure what but we hope the error_msg is useful.
        if success is False or errors is not None or error_id is not None:
            raise HumbleResponseException(error_msg, request=response.request, response=response)

        # Response had no success or errors fields, it's probably data
        return True

    def __parse_data(self, response):
        """
            Try and parse the response data as JSON.  If parsing fails, throw a HumbleParseException.

            :param response:  The response received from humblebundle.com.
             A pass through variable used to initialize the exceptions.
            :return:  The response as a JSON object.
            :raises HumbleParseException:  When the response cannot be parsed as a JSON object.
        """
        try:
            return response.json()
        except ValueError as e:
            raise HumbleParseException("Invalid JSON: %s", str(e), request=response.request, response=response)

    def __get_errors(self, data):
        """
            Retrieves any errors defined within the JSON and returns them as a string.

            :param data: The JSON data to be searched for errors.
            :return:  A tuple containing the errors and error message.
        """
        errors = data.get("errors", None)
        error_msg = ", ".join(itertools.chain.from_iterable(v for k, v in list(errors.items()))) \
            if errors else "Unspecified error"
        return errors, error_msg
