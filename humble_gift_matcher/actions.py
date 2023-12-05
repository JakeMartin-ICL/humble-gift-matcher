#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from humble_gift_matcher.config_data import ConfigData
from alive_progress import alive_bar
from .steam_api.steam_api import get_appids, get_friends_with_details, get_wishlist


class Action:
    @staticmethod
    def match_games_with_friends(hapi, steam_session):
        print("[Info] Fetching all Steam appids.")
        appid_list = get_appids()
        print(f"[Info] Found {len(appid_list)} apps")
        appid_lookup = dict([(app["name"], app["appid"]) for app in appid_list])

        games = hapi.get_orders_with_details(appid_lookup)
        unredeemed_wishlisted = dict([(game.steam_app_id, 0) for game in games if not game.claimed])
        game_lookup = {game.steam_app_id: game for game in games}
        print(f"[INFO] {len(unredeemed_wishlisted)} of {len(games)} unredeemed.")

        friends_api_response = get_friends_with_details(ConfigData.steam_api_key, ConfigData.steam_user_id)
        keys_by_friend = {steamid: [] for steamid in friends_api_response}
        with alive_bar(len(friends_api_response)) as bar:
            bar.title("[Info] Matching friends with games.")
            for steamid in friends_api_response:
                wishlist = get_wishlist(steamid, steam_session)
                for appid in wishlist.keys():
                    if appid in unredeemed_wishlisted:
                        keys_by_friend[steamid].append(appid)
                        unredeemed_wishlisted[appid] += 1
                bar()


        print("\nResults:")
        for steamid, friend in friends_api_response.items():
            matches = keys_by_friend[steamid]
            print(f"\n{friend.name} ({friend.real_name}) would like {len(matches)} of your available games:")
            for appid in matches:
                game = game_lookup[appid]
                print(f"{game.name} from {game.parent}. Wanted by {unredeemed_wishlisted[appid] - 1} others.")

        print(f"\nYou!")
        wishlist = get_wishlist(ConfigData.steam_user_id, steam_session)
        for appid in wishlist.keys():
            if appid in unredeemed_wishlisted:
                print(f"{game_lookup[appid].name}")