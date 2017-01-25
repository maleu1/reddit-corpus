import os
import re
import argparse
import logging
import glob
from lxml import etree
import pandas as pd

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


def lines_from_elem(elem, search_re):
    lines = []
    if elem.text:
        text = " ".join(elem.itertext())
        text = text.replace("\n", " ")
        text = re.sub(r"[ ]{2,}", " ", text)
        for match in search_re.finditer(text):
            ln = kwic_from_match(text, match)
            lines.append(ln)

    return lines


def fast_conc_iter(context, search_re):
    """
    fast_iter is useful if you need to free memory while iterating through
    a very large XML file.
    http://lxml.de/parsing.html#modifying-the-tree
    Based on Liza Daly's fast_iter
    http://www.ibm.com/developerworks/xml/library/x-hiperfparse/
    See also http://effbot.org/zone/element-iterparse.htm
    Slightly customized for concordance used
    """
    lines = []
    for event, elem in context:
        lines += lines_from_elem(elem, search_re)
        elem.clear()
        # Also eliminate now-empty references from the root node to elem
        for ancestor in elem.xpath('ancestor-or-self::*'):
            while ancestor.getprevious() is not None:
                del ancestor.getparent()[0]
    del context
    return lines


def search_in_file(f, search_re, args):
    context = etree.iterparse(f, events=('end',),
                              tag=["comment", "submission"])
    lines = fast_conc_iter(context, search_re)
    if lines:
        fn = os.path.basename(f)
        for ln in lines:
            ln["FILENAME"] = fn
            if args.print is True:
                print(ln["LEFT"].rjust(CONC_LEFT), "\t", ln["KEY"],
                      "\t", ln["RIGHT"].ljust(CONC_RIGHT), "\t", fn, "\n")
    return lines


def configure_search_regex(args):
    flags = re.UNICODE
    b = r"\b"
    if args.regex:
        s = r'{0}{1}{0}'.format(b, args.regex)
        search_re = re.compile(s, flags=flags)
    else:
        s = r'{0}{1}{0}'.format(b, re.escape(args.string.strip()))
        search_re = re.compile(s, flags=flags)
    return search_re


def search_corpus(args):
    if args.pos:
        pattern = os.path.join(DIR["corpus_tag_xml"], "*.xml")
    else:
        pattern = os.path.join(DIR["corpus_xml"], "*.xml")
    all_files = glob.glob(pattern)
    lines = []
    search_re = configure_search_regex(args)
    for f in sorted(all_files):
        lines += search_in_file(f, search_re, args)
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
        print("Found {} hits", len(lines))


def main(args):
    search_corpus(args)


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
    parser.add_argument('-p', '--print', dest="print",
                        help="Print lines to console",
                        action="store_true")
    parser.add_argument('-c', '--csv', dest="csv",
                        help="Save lines to CSV file",
                        action="store", type=str, metavar="FILENAME")
    parser.add_argument('-t', '--tagged', dest="pos",
                        help="Search part-of-speech tagged corpus",
                        action="store_true")

    args = parser.parse_args()
    main(args)
