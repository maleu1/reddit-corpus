import os
import datetime
import pytz
import time
import re
import argparse
import logging

import praw
import ftfy
from lxml import etree
import pandas as pd

try:
    from config import *
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


def naive_to_eastern_datetime(dt):
    eastern = pytz.timezone('US/Eastern')
    return eastern.localize(dt)


def datetime_utc_to_unix(dt):
    #  # convert utc datetime to unix timestamp without milliseconds
    return int(dt.strftime("%s"))


def get_timestamps_for_date(d):
    start_str = "{} 00:00:00".format(d.date())
    end_str = "{} 23:59:59".format(d.date())
    start_date = naive_to_eastern_datetime(datetime.datetime.strptime(
        start_str, "%Y-%m-%d %H:%M:%S"))
    end_date = naive_to_eastern_datetime(datetime.datetime.strptime(
        end_str, "%Y-%m-%d %H:%M:%S"))
    start_date = start_date.astimezone(pytz.utc)
    end_date = end_date.astimezone(pytz.utc)
    ts1 = datetime_utc_to_unix(start_date)
    ts2 = datetime_utc_to_unix(end_date)
    return ts1, ts2


def strip_tags(s):
    s = re.sub(r"<[^>]*>", " ", s)
    s = re.sub(r"[ ]{2,}", " ", s)
    return s


def create_xml_doc(s):
    """
        Creates an xml doc for a submission on reddit.
    """

    root = etree.Element("reddit")
    tree = etree.ElementTree(root)
    s_node = etree.Element("submission")
    cs_node = etree.Element("comments")

    s_att_list = ["created_utc", "edited", "has_media",
                  "gilded", "score", "title", "id", "domain",
                  "url", "permalink", "locked",
                  "over_18", "stickied", "is_self", "num_reports"]

    c_att_list = ['created_utc', 'edited', 'gilded', 'id', 'num_reports',
                  'parent_id', 'controversiality']

    s_node.set("author_name", s.author.name)
    s_node.set("subreddit_name", s.subreddit.display_name)
    try:
        s_node.text = s.selftext
    except ValueError:
        s_node.text = strip_tags(ftfy.fix_text(s.selftext_html)).strip()
    for k in s_att_list:
        try:
            val = str(s.__dict__[k])
        except KeyError:
            val = ""
        if val == "None":
            val = ""
        try:
            s_node.set(k, val)
        except ValueError:
            s_node.set(k, ftfy.fix_text(val))
    if s.media:
        s_node.set("has_media", "True")
    else:
        s_node.set("has_media", "False")
    try:
        s.comments.replace_more(limit=0)
    except Exception as e:
        # TO DO: better solution (wait & retry)
        logging.warning(e)
        time.sleep(90)
        return False, 0
    num_comments = 0
    for c in s.comments.list():
        c_node = etree.Element("comment")
        for k in c_att_list:
            try:
                val = str(c.__dict__[k])
            except KeyError:
                val = ""
            if val == "None":
                val = ""
            c_node.set(k, val)
        try:
            c_node.text = c.body
        except ValueError:
            try:
                c_node.text = ftfy.fix_text(c.body)
            except ValueError as e:
                c_node.text = strip_tags(ftfy.fix_text(c.body_html)).strip()
        cs_node.append(c_node)
        num_comments += 1
    s_node.append(cs_node)
    s_node.set("num_com_found", str(num_comments))
    s_node.set("num_com_listed", str(s.num_comments))
    root.append(s_node)
    s_date = datetime.datetime.fromtimestamp(s.created_utc)
    year = str(s_date.year)
    fd = os.path.join(DIR["xml"], s.subreddit.display_name.lower(), year,
                      str(s_date.date()))
    fn = "{}_{}_{}.xml".format(s.subreddit.display_name.lower(),
                               str(s_date.date()), s.id)
    try:
        os.makedirs(fd)
    except FileExistsError:
        pass
    fp = os.path.join(fd, fn)
    try:
        tree.write(fp, pretty_print=True, encoding='utf-8',
                   xml_declaration=True)
    except Exception as e:
        logging.warning(e)
        return False, num_comments
    else:
        logging.info("{}\t{}\t{}".format(s_date.date(),
                                         s.subreddit.display_name, s.title))
        return True, num_comments


def process_date(d, subreddit, reddit):
    ts1, ts2 = get_timestamps_for_date(d)
    csv_fn = "{}_{}.csv".format(subreddit.lower(), d.year)
    csv_fp = os.path.join(DIR["meta"], csv_fn)
    try:
        df = pd.read_csv(csv_fp, index_col=0)
    except (OSError, pd.io.common.EmptyDataError):
        df = pd.DataFrame()
        df["ID"] = ""
        try:
            os.makedirs(DIR["meta"])
        except FileExistsError:
            pass
    for s in reddit.subreddit(subreddit).submissions(start=ts1, end=ts2):
        if str(s.id) not in set(str(df["ID"])):
            success, num_com = create_xml_doc(s)
            s_date = datetime.datetime.fromtimestamp(s.created_utc)
            dn = os.path.join(s.subreddit.display_name.lower(),
                              str(s_date.year), str(s_date.date()))
            fn = "{}_{}_{}.xml".format(s.subreddit.display_name.lower(),
                                       str(s_date.date()), s.id)
            meta = {"DATE": s_date.date(), "SUBREDDIT": subreddit,
                    "FETCHED": datetime.datetime.now().date(),
                    "ID": s.id, "SUCCESS": success, "PERMALINK": s.permalink,
                    "SCORE": s.score, "IS_SELF": s.is_self, "DOMAIN": s.domain,
                    "HAS_MEDIA": s.media, "YEAR": s_date.year,
                    "MONTH": s_date.month, "AUTHOR_NAME": s.author.name,
                    "GILDED": s.gilded, "EDITED": s.edited, "TITLE": s.title,
                    "OVER_18": s.over_18, "STICKIED": s.stickied,
                    "NUM_COM_FOUND": num_com, "NUM_COM_LISTED": s.num_comments,
                    "XML_PATH": os.path.join(dn, fn)
                    }
            try:
                df = df.append(meta, ignore_index=True)
            except pd.indexes.base.InvalidIndexError:
                pass
            else:
                df.to_csv(csv_fp)


def get_dates():
    dates = [FIRST_DAY + datetime.timedelta(days=n) for n in
             range((LAST_DAY - FIRST_DAY).days + 1)]
    return dates


def process_r_nba_by_date(dates, reddit):
    """For each date get all submissions from r/nba"""
    reddit = praw.Reddit(user_agent=USER_AGENT,
                         client_id=CLIENT_ID,
                         client_secret=CLIENT_SECRET)
    for d in dates:
        process_date(d, "nba", reddit)


def process_team_subs_by_date(dates, reddit):
    """For each date, get all submissions from all team subreddits """
    for d in dates:
        for v in sorted(TEAM_SUBREDDITS.values()):
            process_date(d, v, reddit)


def process_date_first(dates, reddit):
    """ For each date, get all submissions for each subreddit"""
    for d in dates:
        for s in sorted(SUBREDDITS):
            process_date(d, s, reddit)


def process_sub_first(dates, reddit):
    """ For each subreddit, get all submissions for each date"""
    for s in sorted(SUBREDDITS):
        for d in dates:
            process_date(d, s, reddit)


def main(args):
    logging.basicConfig(filename="download.log", level=logging.INFO,
                        filemode="w")
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    dates = get_dates()
    reddit = praw.Reddit(user_agent=USER_AGENT,
                         client_id=CLIENT_ID,
                         client_secret=CLIENT_SECRET)

    if args.nba_only:
        process_r_nba_by_date(dates, reddit)
    elif args.team_only:
        process_team_subs_by_date(dates, reddit)
    elif args.subreddit_first:
        process_sub_first(dates, reddit)
    else:
        process_date_first(dates, reddit)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download reddit posts. "
                                     "Defaults to --date-first.")
    method_group = parser.add_mutually_exclusive_group()
    method_group.add_argument('-d', '--date-first', dest="date_first",
                              help="Download date by date (all subreddits)",
                              action="store_true")
    method_group.add_argument('-s', '--sub-first',
                              dest="subreddit_first",
                              help="Download subreddit by subreddit "
                              "(all dates)",
                              action="store_true")
    method_group.add_argument('-n', '--nba-only', dest="nba_only",
                              help="Only download from r/nba",
                              action="store_true")
    method_group.add_argument('-t', '--team-only', dest="team_only",
                              help="Only download from team subreddits",
                              action="store_true")
    args = parser.parse_args()
    main(args)
