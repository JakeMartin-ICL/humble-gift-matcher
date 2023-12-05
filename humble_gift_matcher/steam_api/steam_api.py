import requests
import json
from typing import List, Dict, Any
import urllib3
from .model.friend import Friend
from .model.WishlistGame import WishlistGame

def get_friends(api_key: str, user_id: int):
    url = "http://api.steampowered.com/ISteamUser/GetFriendList/v0001"
    payload = {'key': api_key, 'steamid': user_id}

    api_response = requests.get(url, params=payload)
    try:
        friends = api_response.json()["friendslist"]["friends"]
    except json.decoder.JSONDecodeError:
        print(
            f"[Error] Steam API response invalid. Expected data, recieved:\n{api_response.text}. \nCheck your config.")
    return friends

def get_friends_with_details(api_key: str, user_id: int, friend_ids: List[str] = None) -> Dict[str, Friend]:
    friend_ids = [friend["steamid"] for friend in get_friends(api_key, user_id)] if friend_ids is None else friend_ids
    url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002"
    payload = {'key': api_key, 'steamids':  ','.join(friend_ids)}

    api_response = requests.get(url, params=payload)
    try:
        json = api_response.json()["response"]["players"]
    except json.decoder.JSONDecodeError:
        print(
            f"[Error] Steam API response invalid. Expected data, recieved:\n{api_response.text}. \nCheck your config.")
    friends = dict([(friend["steamid"], Friend(friend)) for friend in json])
    return friends

def get_wishlist(user_id: int, session: requests.Session = None) -> Dict[int, WishlistGame]:
    url = f"https://store.steampowered.com/wishlist/profiles/{user_id}/wishlistdata/?p=0"

    if session is None:
        api_response = requests.get(url)
    else:
        api_response = session.get(url)
    try:
        json = api_response.json()
    except json.decoder.JSONDecodeError:
        print(
            f"[Error] Steam API response invalid. Expected data, recieved:\n{api_response.text}. \nCheck your config.")
        
    if type(json) is not dict or 'success' in json:
        return {}
    wishlist = dict([(int(id), WishlistGame(game)) for id, game in json.items()])
    return wishlist

def get_appids() -> List[Dict[str, Any]]:
    url = "https://api.steampowered.com/ISteamApps/GetAppList/v2"

    # requests doesn't return the full list for some reason
    urlresp = urllib3.request("GET", url)
    try:
        json = urlresp.json()
    except json.decoder.JSONDecodeError:
        print(
            f"[Error] Steam API response invalid. Expected data, recieved:\n{urlresp}. \nCheck your config.")

    return json["applist"]["apps"]