""" UID Generator

This module contains functionality for producing unique IDs, doing checks
on a set of existing IDs and allowing the user to be sure that they can
generate a unique ID with their choices in a quick runtime
"""

import random


def generate_uid(existing_uids, length, safe=True,
                 choices="abcdefghijklmnopqrstuvwxyz0123456789"):
    # Remove duplicates from the choices string
    choices = ''.join(set(choices))

    # If safe mode is activated, raise an error if it is possible
    # that this search for a uid could run infintitely because
    # there are no unique IDs left to generate
    if safe and len(existing_uids) == len(choices)**length:
        raise IDsExhausted("""Safe mode active and it is
            possible that all UIDs have been exhausted""")

    while True:
        suggested_uid = ''.join(
                random.choice(choices) for i in range(length))
        if suggested_uid not in existing_uids:
            return suggested_uid


class IDsExhausted(Exception):
    pass
