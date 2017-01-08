import os
import glob
import logging

import pandas as pd

try:
    from config import DIR, PATH
except ImportError as e:
    print(e)
    print("Please make sure to (copy &) rename 'sample_config.py' to "
          "'config.py'.")


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
    pattern = os.path.join(DIR["meta"], "*_[0-9]*.csv")
    return glob.glob(pattern)


def combine_metadata(meta_files):
    meta_frames = [pd.read_csv(f, index_col=0) for f in meta_files]
    dfr = pd.concat(meta_frames, ignore_index=True)
    dfr.sort_values(by=["DATE", "SUBREDDIT"], inplace=True)
    return dfr.reset_index(drop=True)


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
            size_df = meta_df.groupby(["YEAR", "MONTH"]).size()
            size_df = size_df.rename("NUM_SUBMISSIONS").to_frame()
            size_df.to_csv(os.path.join(DIR["stats"],
                                        "num_subs_by_year_month.csv"))
            size_df = meta_df.groupby(["SUBREDDIT", "YEAR"]).size()
            size_df = size_df.rename("NUM_SUBMISSIONS").to_frame()
            size_df.to_csv(os.path.join(DIR["stats"],
                                        "num_subs_by_subreddit_year.csv"))


if __name__ == "__main__":
    main()
