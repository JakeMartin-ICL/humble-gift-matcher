#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from .base_model import BaseModel


class Friend(BaseModel):
    """
        Represents the recipient of funds for a given application.
    """

    def __init__(self, data):
        """
            Parameterized constructor for the Friend object.

            :param data: The JSON data to define the object with.
        """
        super(Friend, self).__init__(data)

        self.steamid = data.get("steamid", None)
        self.name = data.get("personaname", None)
        self.real_name = data.get("realname", None)

    def __repr__(self):
        """ Representation of the current Friend object. """
        return "Friend: <%s>" % self.name
