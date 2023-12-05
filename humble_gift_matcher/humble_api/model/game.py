#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from .base_model import BaseModel


class Game(BaseModel):
    """
        Represents a single Game (Weekly Bundle, Monthly Bundle, etc.) which itself contains a list of
        products which were a part of the Game.
    """

    def __init__(self, data, parent: str = None):
        """
            Parameterized constructor for the Game object.

            :param data: The JSON data to define the object with.
        """
        super(Game, self).__init__(data)

        self.name = data.get("human_name", None)
        self.steam_app_id = data.get("steam_app_id", None)
        self.parent = parent
        self.claimed = "redeemed_key_val" in data


    def __repr__(self):
        """ Representation of an Game object. """
        return "Game: <%s>" % self.name
