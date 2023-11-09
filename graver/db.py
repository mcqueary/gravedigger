# import sys
import logging as log
import sqlite3 as sql


def add_row_to_database(filename, grave):
    row = (grave["id"],)
    keys = ["graveid"]
    for key in grave.keys():
        if key == "id":
            continue
        row += (grave[key],)
        keys.append(key)

    col_names = "(" + ", ".join(keys) + ")"
    value_hold = "(" + "?," * (len(keys) - 1) + "?)"
    # trunk-ignore(bandit/B608)
    insert = "INSERT INTO findAGrave " + col_names + " VALUES " + value_hold

    try:
        conn = sql.connect(filename)
        c = conn.cursor()
        c.executemany(insert, [row])
        conn.commit()
        conn.close()
    except sql.IntegrityError:
        log.warn("Memorial #" + grave["id"] + " is already in database.")
    except Exception as e:
        log.exception(e)
