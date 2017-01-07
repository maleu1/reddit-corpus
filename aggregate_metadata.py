import os
import glob
import logging

import pandas as pd
from lxml import etree

from config import DIR, PATH

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


def get_meta_files():
    pattern = os.path.join(DIR["meta"], "[0-9]*-[0-9]*-[0-9]**.csv")
    return glob.glob(pattern)


def combine_metadata(meta_files):
    meta_frames = [pd.read_csv(f, index_col=0) for f in meta_files]
    dfr = pd.concat(meta_frames, ignore_index=True)
    dfr["DATE"] = dfr["DATE"].fillna("0000-00-00")
    dfr.sort_values(by=["DATE", "SUBREDDIT"], inplace=True)
    dfr["YEAR"] = dfr["DATE"].apply(lambda d: d.split("-")[0])
    dfr["MONTH"] = dfr["DATE"].apply(lambda d: d.split("-")[1])
    dfr["YEAR_MONTH"] = dfr["DATE"].apply(lambda d: "-".join(d.split("-")[:2]))
    dfr.SUCCESS = dfr.SUCCESS.astype(bool)
    return dfr.reset_index(drop=True)


def add_post_information(r):
    r["XML_PATH"] = os.path.join(DIR["xml"], r.SUBREDDIT, r.YEAR,
                                 r.DATE, "{}_{}_{}.xml"
                                 .format(r.SUBREDDIT, r.DATE, r.ID))
    try:
        tree = etree.parse(r["XML_PATH"])
    except IOError:
        r["SUCCESS"] = False
    else:
        sub = tree.find(".//submission")
        r["SCORE"] = int(sub.get("score"))
        r["GILDED"] = bool(int(sub.get("gilded")))
        r["EDITED"] = sub.get("edited")
        r["STICKIED"] = sub.get("stickied")
        r["OVER_18"] = sub.get("over_18")
        r["TITLE"] = sub.get("title")
        r["AUTHOR_NAME"] = sub.get("author_name")
        r["URL"] = sub.get("url")
        r["HAS_MEDIA"] = sub.get("has_media")
        r["NUM_COM"] = sub.get("num_comments")
        r["NUM_COM_FOUND"] = len(list(sub.findall(".//commment")))
        r["IS_SELF"] = sub.get("is_self")
    return r


def main(generate=True, analyze=True):
    logging.basicConfig(filename="metadata.log", level=logging.INFO,
                        filemode="w")
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    if generate:
        # Create a single metadata file from all the date+subreddit csv files
        meta_files = get_meta_files()
        logging.info("Combining metadata from {} files"
                     .format(len(meta_files)))
        meta_df = combine_metadata(meta_files)
        logging.info("Adding information to {} rows"
                     .format(len(meta_df.index)))
        meta_df = meta_df.apply(add_post_information, axis="columns")
        meta_df.to_csv(PATH["metadata"])
    if analyze:
        try:
            meta_df = pd.read_csv(PATH["metadata"], index_col=0)
        except IOError as e:
            logging.warning(e)
        else:
            try:
                os.makedirs(DIR["stats"])
            except FileExistsError:
                pass
            # Tabulate the number of submissions
            size_df = meta_df.groupby(["SUBREDDIT"]).size()
            size_df = size_df.rename("NUM_SUBMISSIONS").to_frame()
            size_df.to_csv(os.path.join(DIR["stats"],
                                        "num_subs_by_subreddit.csv"))
            size_df = meta_df.groupby(["DATE"]).size()
            size_df = size_df.rename("NUM_SUBMISSIONS").to_frame()
            size_df.to_csv(os.path.join(DIR["stats"],
                                        "num_subs_by_date.csv"))
            size_df = meta_df.groupby(["YEAR"]).size()
            size_df = size_df.rename("NUM_SUBMISSIONS").to_frame()
            size_df.to_csv(os.path.join(DIR["stats"],
                                        "num_subs_by_year.csv"))
            size_df = meta_df.groupby(["MONTH"]).size()
            size_df = size_df.rename("NUM_SUBMISSIONS").to_frame()
            size_df.to_csv(os.path.join(DIR["stats"],
                                        "num_subs_by_month.csv"))
            size_df = meta_df.groupby(["YEAR_MONTH"]).size()
            size_df = size_df.rename("NUM_SUBMISSIONS").to_frame()
            size_df.to_csv(os.path.join(DIR["stats"],
                                        "num_subs_by_year_month.csv"))
            size_df = meta_df.groupby(["SUBREDDIT", "YEAR"]).size()
            size_df = size_df.rename("NUM_SUBMISSIONS").to_frame()
            size_df.to_csv(os.path.join(DIR["stats"],
                                        "num_subs_by_subreddit_year.csv"))


if __name__ == "__main__":
    main()
