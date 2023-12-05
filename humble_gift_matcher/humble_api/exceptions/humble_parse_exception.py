#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from .humble_response_exception import HumbleResponseException


class HumbleParseException(HumbleResponseException):
    """ An error occurred while parsing the response. """
    pass