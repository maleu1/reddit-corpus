import os
import glob
import collections

import pandas as pd
from lxml import etree

from config import DIR

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


def freq_df_from_token_list(tokens):
    freq = collections.Counter(tokens)
    freq_df = pd.DataFrame.from_dict(freq, orient='index').reset_index()
    freq_df.columns = ["TOKEN", "FREQUENCY"]
    freq_df = freq_df.sort_values(by="FREQUENCY", ascending=False)
    freq_df = freq_df.reset_index(drop=True)
    freq_df["POS"] = freq_df["TOKEN"].apply(lambda t:
                                            t.split("_")[1].split("/")[0])
    freq_df["TOKEN"] = freq_df["TOKEN"].apply(lambda t:
                                              t.split("_")[0])
    freq_df["TOKEN"] = freq_df["TOKEN"].apply(lambda t:
                                              t.replace("\n", ""))
    freq_df["PCT_RANK"] = freq_df["FREQUENCY"].rank(pct=True)
    total_wc = freq_df["FREQUENCY"].sum()
    print(total_wc)
    return freq_df


def tokenize(s):
    tokens = ["{}_{}".format(t.split("_")[0].lower(), t.split("_")[1])
              for t in s.split() if len(t) > 3 and "_" in t and
              any([c.isalnum() for c in t.split("_")[0]])]
    return tokens


def token_list_from_files(files, fn):
    tokens = []
    for f in files:
        tree = etree.parse(f)
        sentences = tree.findall(".//s")
        for s in sentences:
            tokens += tokenize(s.text)
    if tokens:
        freq_df = freq_df_from_token_list(tokens)
        freq_df.to_csv(os.path.join(DIR["tokens"], fn))
        print(fn)
        print(freq_df[freq_df["POS"].isin({"NNP", "NNPS"})].head(10))
    else:
        print("No tokens for", fn)


def create_lists(year=True, subreddit=True, month=True):
    if year:  # By year
        for y in YEARS:
            pattern = os.path.join(DIR["corpus_tag_xml"],
                                   "*_{}-*.xml".format(y))
            fn = "tokens_by_year_{}.csv".format(y)
            token_list_from_files(glob.glob(pattern), fn)
    if subreddit:
        for s in SUBREDDITS:
            pattern = os.path.join(DIR["corpus_tag_xml"],
                                   "*_{}_*.xml".format(s))
            fn = "tokens_by_subreddit_{}.csv".format(s)
            token_list_from_files(glob.glob(pattern), fn)
    if month:
        for m in range(1, 13):
            m = str(m).zfill(2)
            pattern = os.path.join(DIR["corpus_tag_xml"],
                                   "*-{}.xml".format(m))
            fn = "tokens_by_month_{}.csv".format(m)
            token_list_from_files(glob.glob(pattern), fn)
    if year and month:
        for y in YEARS:
            for m in range(1, 13):
                m = str(m).zfill(2)
                pattern = os.path.join(DIR["corpus_tag_xml"],
                                       "*_{}-{}.xml".format(y, m))
                fn = "tokens_by_year_month_{}_{}.csv".format(y, m)
                token_list_from_files(glob.glob(pattern), fn)
    if subreddit and year:
        for s in SUBREDDITS:
            for y in YEARS:
                pattern = os.path.join(DIR["corpus_tag_xml"],
                                       "*_{}_{}-*.xml".format(s, y))
                fn = "tokens_by_subreddit_year_{}_{}.csv".format(s, y)
                token_list_from_files(glob.glob(pattern), fn)
    if subreddit and year and month:
        for s in SUBREDDITS:
            for y in YEARS:
                for m in range(1, 13):
                    m = str(m).zfill(2)
                    pattern = os.path.join(DIR["corpus_tag_xml"],
                                           "*_{}_{}-{}.xml".format(s, y, m))
                    fn = "tokens_by_subreddit_year_month_{}_{}_{}.csv"\
                         .format(s, y, m)
                    token_list_from_files(glob.glob(pattern), fn)


def main():
    try:
        os.makedirs(DIR["tokens"])
    except FileExistsError:
        pass
    create_lists()


if __name__ == "__main__":
    main()
