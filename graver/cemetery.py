# import os
import sqlite3
from dataclasses import dataclass


class CemeteryException(Exception):
    pass


@dataclass
class Cemetery:
    """Class for keeping track of a Find A Grave cemetery."""

    id: int
    url: str
    name: str
    location: str
    coords: str
    
    @classmethod
    def create_table(cls, database_name="graves.db"):
        conn = sqlite3.connect(database_name)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS cemeteries
            (id INTEGER PRIMARY KEY, url TEXT,
            name TEXT, location TEXT, coords TEXT, more_info BOOL)"""
        )
        conn.close()
