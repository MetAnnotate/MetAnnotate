#!/usr/bin/env python

"""
Created by: MetAnnotate Team 2017

Description: Contains general utility functions for metannotate.
"""

from os import path


def sanitize_cli_path(cli_path):
    """
    Performs expansion of '~' and shell variables such as "$HOME" into absolute paths.
    :param cli_path: The path to expand
    :return: An expanded path.
    """
    return path.expanduser(path.expandvars(cli_path))
