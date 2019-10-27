import os
import datetime
import pytz
import time
import re
import argparse
import logging
import glob
#import ftfy
from psaw import PushshiftAPI
from tendo.singleton import SingleInstance
from lxml import etree
import pandas as pd

try:
    from config import *
except ImportError as e:
    print(e)
    print("Please make sure to (copy &) rename 'sample_config.py' to "
          "'config.py' and insert valid Reddit API credentials.")

def get_year_for_date(ts):
    return ts.strftime('%Y')

def open_file(filename, year):
    fn = "reddit_{}_{}.txt".format(filename.lower(), year)
    fp = os.path.join("txt", fn)
    try:
        return open(fp, "a+")
    except IOError:
        print("unable to open or create file")

def process_subreddit(subreddit, api, d):
    year = get_year_for_date(d)
    txt = open_file(subreddit, year)

    latest = d

    num_comments = 0
    while True:
        try:
            comments = api.search_comments(subreddit=subreddit,sort="asc",size=500,after=latest)
            if comments == None:
                break;

            for comment in comments:
                created = datetime.datetime.utcfromtimestamp(comment.created)
                new_year = get_year_for_date(created)
                if new_year != year:
                    year = new_year
                    txt = open_file(subreddit, year)
                txt.write(comment.body + "\n")
                num_comments += 1
                if num_comments % 50 == 0:
                    latest = comment.created
                    logging.info("{}\t{}".format(num_comments, latest))

        except Exception as e:  # limit to expected exception types later
            # Wait 5min and try again, to deal with e.g. wifi issues
            logging.warn(e)
            time.sleep(300)
            process_subreddit(subreddit, api, latest)
    txt.close()

def get_dates(from_last=True):
    if from_last:
        last = get_last_indexed_date()
        dates = [last + datetime.timedelta(days=n) for n in range((LAST_DAY - FIRST_DAY).days + 1)]
    else:
        dates = [FIRST_DAY + datetime.timedelta(days=n) for n in range((LAST_DAY - FIRST_DAY).days+ 1)]
    return dates

def for_user(api, date, user):
    txt = open_file(user, "any")

    latest = date
    num_comment = 0
    try:
        #viable alternative:
        #subreddits = api.search_comments(author=user, aggs='subreddit')
        subreddit_activity = api.redditor_subreddit_activity(user)
        if subreddit_activity != None:

            for comment in subreddit_activity["comment"]:
                num_comment +=1
                txt.write("{}\t{}".format(num_comment, comment))

                logging.info("{}\t{}".format(num_comment, comment))

    except Exception as e:
            logging.warn(e)
    txt.close()

def each_subreddit(api, date):
    for s in sorted(SUBREDDITS):
        process_subreddit(s, api, date)

def main(args):

    me = SingleInstance()
    logfile = os.path.join("download.log")
    logging.basicConfig(filename=logfile, level=logging.INFO,
                        filemode="w")
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    api = PushshiftAPI()

    if (args.first_date):
        date = args.first_date
    else:
        date = FIRST_DAY

    if (args.user):
        for_user(api, date, args.user)
    else:
        each_subreddit(api, date)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download reddit posts. "
                                     "arguments are -d or --date-first for start date, or -u for user posts")
    method_group = parser.add_mutually_exclusive_group()
    method_group.add_argument('-d', '--start-date', dest="first_date",
                              help="Download from this date (all subreddits)",
                              action="store_true")

    method_group = parser.add_mutually_exclusive_group()
    method_group.add_argument('-u', '--user', help="Get all posts of a user", action="store")

    args = parser.parse_args()
    main(args)
