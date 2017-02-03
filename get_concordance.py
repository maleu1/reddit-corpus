import os
import re
import argparse
import logging
import glob
import pprint

from lxml import etree
import pandas as pd
import pymongo as pm


try:
    from config import DIR, CONC_LEFT, CONC_RIGHT
except ImportError as e:
    print(e)
    print("Please make sure to (copy &) rename 'sample_config.py' to "
          "'config.py' and insert valid Reddit API credentials.")

"""
    This file is part of reddit-nba-corpus.

    reddit-nba-corpus is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    reddit-nba-corpus is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with reddit-nba-corpus.  If not, see <http://www.gnu.org/licenses/>.
"""


def kwic_from_match(text, m):
    kwic = {}
    kwic['KEY'] = m.group(0).strip()
    if len(text[:m.start()]) > CONC_LEFT:
        kwic['LEFT'] = text[m.start() - CONC_LEFT:m.start()].strip()
    else:
        kwic["LEFT"] = text[:m.start()].strip()
    kwic['RIGHT'] = text[m.end():m.end() + CONC_RIGHT].strip()
    return kwic


def lines_from_string(text, search_re):
    lines = []
    text = text.replace("\n", " ")
    text = re.sub(r"[ ]{2,}", " ", text)
    for match in search_re.finditer(text):
        ln = kwic_from_match(text, match)
        lines.append(ln)
    return lines


def save(lines, args):
    if lines and args.csv:
        try:
            os.makedirs(DIR["conc"])
        except FileExistsError:
            pass
        conc_df = pd.DataFrame().from_dict(lines)
        fp = os.path.join(DIR["conc"], "{}.csv".format(args.csv))
        conc_df.to_csv(fp)
        print("Concordance ({} hits) saved to {}".format(len(lines), fp))
    else:
        print("Found {} hits".format(len(lines)))


def configure_mongo_search_regex(args):
    flags = re.UNICODE
    b = r"\b"
    if args.regex:
        s = r'{0}{1}{0}'.format(b, args.regex)
    else:
        s = r'{0}{1}{0}'.format(b, re.escape(args.string.strip()))
    r = {"mongo": "/.*?{}.*?/".format(s), "python": re.compile(s, flags=flags)}
    return r


def search_database(args):
    lines = []
    regex = configure_mongo_search_regex(args)
    client = pm.MongoClient()
    db = client.nbareddit
    if args.pos:
        text_field = "pos"
    else:
        text_field = "text"
    search_args = {text_field: {"$regex": "{}".format(regex["mongo"])}}
    for r in db.posts.find(search_args):
        lns = lines_from_string(r[text_field], regex["python"])
        if args.display:
            for ln in lns:
                print(ln["LEFT"].rjust(CONC_LEFT),
                      "\t", ln["KEY"], "\t", ln["RIGHT"].ljust(CONC_RIGHT),
                      "\t", r["date"], r["subreddit"], "\n")
        lines += lns
    save(lines, args)


def main(args):
    search_database(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract concordance lines")
    method_group = parser.add_mutually_exclusive_group()
    method_group.add_argument('-r', '--regex', dest="regex",
                              help="Regular expression search",
                              action="store", type=str, metavar="REGEX")
    method_group.add_argument('-s', '--string',
                              dest="string",
                              help="String search", action="store", type=str,
                              metavar="STRING")
    parser.add_argument('-d', '--display', dest="display",
                        help="Display lines in console",
                        action="store_true")
    parser.add_argument('-c', '--csv', dest="csv",
                        help="Save lines to CSV file",
                        action="store", type=str, metavar="FILENAME")
    parser.add_argument('-p', '--pos', dest="pos",
                        help="Search part-of-speech tagged corpus",
                        action="store_true")

    args = parser.parse_args()
    main(args)
