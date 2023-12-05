#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from .base_model import BaseModel


class WishlistGame(BaseModel):
    """
        Represents the recipient of funds for a given application.
    """

    def __init__(self, data):
        """
            Parameterized constructor for the WishlistGame object.

            :param data: The JSON data to define the object with.
        """
        super(WishlistGame, self).__init__(data)

        self.name = data.get("name", None)
        self.reviews_percent = data.get("reviews_percent", None)

        subs = data.get("subs", None)
        first_sub = next(iter(subs or []), None)
        self.price = None if first_sub is None else first_sub.get("price", None)

    def __repr__(self):
        """ Representation of the current WishlistGame object. """
        return "WishlistGame: <%s>" % self.name
