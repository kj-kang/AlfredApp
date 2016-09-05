# -*- coding: utf-8 -*-
# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set tabstop=4 expandtab shiftwidth=4 softtabstop=4

from __future__ import unicode_literals

import codecs
import json
import sqlite3
import sys
import os

sys.stdin = codecs.getreader("utf-8")(sys.stdin)
sys.stdout = codecs.getwriter("utf-8")(sys.stdout)
sys.stderr = codecs.getwriter("utf-8")(sys.stderr)

def search_bookmarks(cursor, queries):
    search = "AND ".join([ "moz_bookmarks.title like '%%%s%%'" % q for q in queries ])
    sql = """
SELECT moz_places.id, moz_places.url, moz_bookmarks.title, moz_places.frecency
FROM moz_bookmarks
LEFT OUTER JOIN moz_places
ON moz_bookmarks.fk = moz_places.id
WHERE moz_bookmarks.type = 1
    AND (%s)
ORDER BY moz_places.frecency DESC
""" % (search)
    retval = map(bookmarks_to_alfred, cursor.execute(sql))
    return retval

def search_inputhistory(cursor, queries):
    search = "AND ".join([ "moz_inputhistory.input like '%%%s%%'" % q for q in queries ])
    sql = """
SELECT moz_places.id, moz_places.url, moz_places.title, moz_places.frecency
FROM moz_inputhistory
LEFT OUTER JOIN  moz_places
ON moz_places.id = moz_inputhistory.place_id
WHERE (%s)
ORDER BY moz_places.frecency DESC
""" % search
    retval = map(bookmarks_to_alfred, cursor.execute(sql))
    return retval

def bookmarks_to_alfred(row):
    retval = {
        "id": row[0],
        "title": row[2],
        "subtitle": row[1],
        "arg": row[1],
        "frecency": row[3],
    }
    if retval["title"] is None:
        retval["title"] = retval["subtitle"]
    return retval


def profile_path():
    path = "~/Library/Application Support/Firefox/Profiles/"
    path = os.path.expanduser(path)
    profile_path = [ subpath for subpath in os.listdir(path) if "default" in subpath ]
    if len(profile_path) == 0:
        raise RuntimeError("Can't find Firefox Profile")
    path = os.path.join(path, profile_path[0], "places.sqlite")
    return path


def remove_duplicate(items):
    new_items = []
    saved_keys = {}
    for item in items:
        if saved_keys.has_key(item["id"]):
            pass
        else:
            saved_keys[item["id"]] = 1
            new_items.append(item)
    return new_items

import unicodedata

def main():
    queries = [ unicodedata.normalize('NFC', q.decode('utf-8')) for q in sys.argv[1:] ]
    connection = sqlite3.connect(profile_path())
    cursor = connection.cursor()
    retval = search_bookmarks(cursor, queries)
    retval = retval + search_inputhistory(cursor, queries)
    retval = sorted(retval, key=lambda x: x["frecency"])
    retval = remove_duplicate(retval)
    retval = { "items": retval }
    print json.dumps(retval)

if __name__ == '__main__':
    main()
