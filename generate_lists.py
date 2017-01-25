import os
import glob
import collections
import re
import argparse
import datetime

import numpy as np
import pandas as pd
from scipy.stats import chisqprob
from lxml import etree

try:
    from config import DIR, YEARS, SUBREDDITS
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


class KeywordFrame():
    """
    Calculates keywords between two corpora.
    Input may be texts, token lists, counters or TokenFrames
    """
    def __init__(self, ignore_pos=False):
        self.corpus = {}
        self.ignore_pos = ignore_pos

    def combine_corpora(self, corpus_names, combined_name=None):
        """ Takes a list of corpus names and a combined name str """
        if combined_name is None:
            combined_name = "C{}".format(len(self.corpus.keys()) + 1)
        df = pd.DataFrame()
        for name in corpus_names:
            try:
                c = self.corpus[name]
            except KeyError as e:
                print("Not found:", e)
            else:
                df = df.append(c["df"], ignore_index=True)
        df.loc[:, "TOK"] = df.apply(lambda r: "{}_{}".format(r["TOKEN"],
                                    r["POS"]), axis="columns")
        for tok, grp in df.groupby("TOK"):
            if len(grp.index) > 1:
                t = grp.sum()
                t.TOK = tok
                if "_" in tok:
                    t.TOKEN = tok.split("_")[0]
                    t.POS = tok.split("_")[1]
                else:
                    t.TOKEN = tok
                    t.POS = ""
                df.drop(grp.index, inplace=True)
                df.loc[tok] = t
        wc = df["FREQ"].sum()
        df.drop("TOK", axis="columns", inplace=True)
        df.sort_values("FREQ", ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)
        df.index = df.index + 1
        df.index.name = "RANK"
        df.loc[:, "PCT"] = round(df["FREQ"] / wc * 100, 3)
        df.loc[:, "PERCENTILE"] = df["FREQ"].rank(pct=True)
        df.loc[:, "ZSCORE"] = (df.FREQ - df.FREQ.mean()) / df.FREQ.std(ddof=0)
        self.corpus[combined_name] = {"wc": wc, "df": df}

    def get_keywords(self, c_name_1, c_name_2):
        self.df = pd.DataFrame()
        print("Comparing", c_name_1, "and", c_name_2)
        # to not mess with the originals, e.g. when removing POS
        c1 = self.corpus[c_name_1].copy()
        c2 = self.corpus[c_name_2].copy()
        self.c_wc = c1["wc"] + c2["wc"]
        self.wc_1 = c1["wc"]
        self.wc_2 = c2["wc"]
        """
        There's a bug when dropping POS occurs where the POS also vanish from
        the original causing crashes when combining it again in some way
        """
        if not self.ignore_pos:
            c1["df"].loc[:, "TOK"] = c1["df"].apply(lambda r: "{}_{}"
                                                    .format(r["TOKEN"],
                                                            r["POS"]),
                                                    axis="columns")
            c2["df"].loc[:, "TOK"] = c2["df"].apply(lambda r: "{}_{}"
                                                    .format(r["TOKEN"],
                                                            r["POS"]),
                                                    axis="columns")
        else:
            c1["df"].loc[:, "TOK"] = c1["df"]["TOKEN"]
            c2["df"].loc[:, "TOK"] = c2["df"]["TOKEN"]
            """
            Combine duplicate tokens (which had different POS) then
            recalculate the order and relevant columns
            """
            for tok, grp in c1["df"].groupby("TOK"):
                if len(grp.index) > 1:
                    t = grp.sum()
                    t.TOK = tok
                    t.TOKEN = tok
                    c1["df"].drop(grp.index, inplace=True)
                    c1["df"].loc[tok] = t
            for tok, grp in c2["df"].groupby("TOK"):
                if len(grp.index) > 1:
                    t = grp.sum()
                    t.TOK = tok
                    t.TOKEN = tok
                    c2["df"].drop(grp.index, inplace=True)
                    c2["df"].loc[tok] = t
            c1["df"].loc[:, "PCT"] = round(c1["df"]["FREQ"] /
                                           self.wc_1 * 100, 3)
            c2["df"].loc[:, "PCT"] = round(c2["df"]["FREQ"] /
                                           self.wc_2 * 100, 3)
            c1["df"].sort_values("FREQ", ascending=False, inplace=True)
            c1["df"].reset_index(drop=True, inplace=True)
            c1["df"].index = c1["df"].index + 1
            c1["df"].index.name = "RANK"
            c2["df"].sort_values("FREQ", ascending=False, inplace=True)
            c2["df"].reset_index(drop=True, inplace=True)
            c2["df"].index = c2["df"].index + 1
            c2["df"].index.name = "RANK"

        # Ensure c1 and c2 both contain the same tokens
        t1 = set(c1["df"].TOK)
        t2 = set(c2["df"].TOK)
        c1["df"].set_index("TOK", drop=True, inplace=True)
        c2["df"].set_index("TOK", drop=True, inplace=True)
        not_in_c1 = sorted(t2.difference(t1))
        not_in_c2 = sorted(t1.difference(t2))

        not_in_c1 = [{"TOKEN": tok.split("_")[0], "POS": tok.split("_")[1],
                      "FREQ": 0, "PCT": 0, "TOK": tok} for tok in not_in_c1]
        not_in_c2 = [{"TOKEN": tok.split("_")[0], "POS": tok.split("_")[1],
                      "FREQ": 0, "PCT": 0, "TOK": tok} for tok in not_in_c2]
        nc1_df = pd.DataFrame.from_dict(not_in_c1)
        nc2_df = pd.DataFrame.from_dict(not_in_c2)
        if len(nc1_df.index) > 0:
            nc1_df.set_index("TOK", drop=True, inplace=True)
            c1["df"] = c1["df"].append(nc1_df)
        if len(nc2_df.index) > 0:
            nc2_df.set_index("TOK", drop=True, inplace=True)
            c2["df"] = c2["df"].append(nc2_df)
        self.df = c1["df"].merge(c2["df"], left_index=True, right_index=True,
                                 how="outer", suffixes=("_1", "_2"))

        self.df.loc[:, "TOKEN"] = self.df.TOKEN_1
        self.df.drop(["TOKEN_1", "TOKEN_2"], axis="columns", inplace=True)
        self.df.loc[:, "PERCENTILE_1"] = self.df["FREQ_1"].rank(pct=True)
        self.df.loc[:, "PERCENTILE_2"] = self.df["FREQ_2"].rank(pct=True)
        self.df.loc[:, "ZSCORE_1"] = (self.df.FREQ_1 - self.df.FREQ_1
                                      .mean()) / self.df.FREQ_1.std(ddof=0)
        self.df.loc[:, "ZSCORE_2"] = (self.df.FREQ_2 - self.df.FREQ_2
                                      .mean()) / self.df.FREQ_2.std(ddof=0)
        self.df.loc[:, "C_FREQ"] = self.df.FREQ_1 + self.df.FREQ_2
        self.df.loc[:, "NORM_1"] = self.df.FREQ_1 / self.wc_1
        self.df.loc[:, "NORM_2"] = self.df.FREQ_2 / self.wc_2
        self.df.loc[:, "EXPECTED_1"] = c1["wc"] * self.df.C_FREQ / self.c_wc
        self.df.loc[:, "EXPECTED_2"] = c2["wc"] * self.df.C_FREQ / self.c_wc
        self.df.loc[:, "SIGN"] = "+"
        self.df.loc[:, "SIGN"] = self.df.apply(lambda r:
                                               "-" if r["FREQ_1"] < r["FREQ_2"]
                                               else "+", axis="columns")
        self.df = self.df.apply(self.apply_keyword_metrics, axis="columns")

    def apply_keyword_metrics(self, r):
        # a trillionth (long-scale), avoids zero in relative risk calculation
        AVOID_ZERO = 0.000000000000000001
        """
        different from LL to preserve scale better
        (log2(1) = 0, log2(0.5) = -1. log2(0.000000000000000001)
                                = -59.794705707972525
        """
        AVOID_ZERO_LR = 0.5
        DEG_FREE = 1  # degrees of freedom, 1 since pairwise
        if r["FREQ_1"] != 0:
            r["LIKE_1"] = r["FREQ_1"] * np.log(r["FREQ_1"] / r["EXPECTED_1"])
        else:
            r["LIKE_1"] = 0
        if r["FREQ_2"] != 0:
            r["LIKE_2"] = r["FREQ_2"] * np.log(r["FREQ_2"] / r["EXPECTED_2"])
        else:
            r["LIKE_2"] = 0
        r["LIKELIHOOD"] = r["LIKE_1"] + r["LIKE_2"]
        r["LL"] = 2 * r["LIKELIHOOD"]
        if r["LL"] < 0:
            r["LL"] = 0

        r["LL_P_VAL"] = chisqprob(r["LL"], 1)

        if r["NORM_2"] == 0:
            r["PCT_DIFF"] = (r["NORM_1"] - r["NORM_2"]) * 100 / AVOID_ZERO
        else:
            r["PCT_DIFF"] = (r["NORM_1"] - r["NORM_2"]) * 100 / r["NORM_2"]

        r["BIC"] = r["LL"] - (DEG_FREE * np.log(self.c_wc))

        r["ELL"] = r["LL"] / (self.c_wc * np.log(min(r["EXPECTED_1"],
                                                     r["EXPECTED_2"])))

        if r["NORM_2"] != 0:
            r["REL_RISK"] = r["NORM_1"] / r["NORM_2"]
        else:
            r["REL_RISK"] = r["NORM_1"] / AVOID_ZERO

        if r["NORM_1"] == 0:
            top = AVOID_ZERO_LR / self.wc_1
        else:
            top = r["NORM_1"]
        if r["NORM_2"] == 0:
            bottom = AVOID_ZERO_LR / self.wc_2
        else:
            bottom = r["NORM_2"]
        r["LOG_RATIO"] = np.log2(top / bottom)
        # r["LOG_RATION"] = np.log2(r["REL_RISK"])
        r["ODDS_RATIO"] = (r["FREQ_1"] / (self.wc_1 -
                           r["FREQ_1"])) / (r["FREQ_2"] / (self.wc_2 -
                                                           r["FREQ_2"]))
        return r

    def add_from_token_frame(self, tf, name=None):
        if not name:
            name = "C{}".format(len(self.corpus.keys()) + 1)
        tf.recalculate()
        self.corpus[name] = {"df": tf.df, "wc": tf.wc}


class TokenFrame():
    def __init__(self, min_freq=1, preserve_case=False, stopwords=[],
                 pos_tagged=False, drop_function_words=False):

        self.min_freq = min_freq
        self.preserve_case = preserve_case
        self.stopwords = stopwords
        self.pos_tagged = pos_tagged
        self.drop_function_words = drop_function_words
        self.wc = 0

        self.tokens = []
        self.counter = collections.Counter()
        self.df = pd.DataFrame()

        self.function_pos_tags = ["CC", "DT", "EX", "IN", "PDT", "POS", "PRP",
                                  "PRP$", "RP"]
        """
        CC,Coordinating conjunction
        DT,Determiner
        EX,Existential there
        IN,Preposition or subordinating conjunction
        PDT,Predeterminer
        POS,Possessive ending
        PRP,Personal pronoun
        PRP$,Possessive pronoun
        RP,Particle
        """

    def recalculate(self):
        # updates df , e.g. after filtering etc.
        if len(self.df.index > 0):
            self.wc = self.df["FREQ"].sum()
            self.df.reset_index(drop=True, inplace=True)
            self.df.index = self.df.index + 1
            self.df.index.name = "RANK"
            self.df.loc[:, "PCT"] = round(self.df["FREQ"] / self.wc * 100, 3)
            self.df.loc[:, "PERCENTILE"] = self.df["FREQ"].rank(pct=True)
            self.df.loc[:, "ZSCORE"] = (self.df.FREQ -
                                        self.df.FREQ
                                        .mean()) / self.df.FREQ.std(ddof=0)

    def create_dataframe(self):
        if self.wc > 0:
            self.df = pd.DataFrame.from_records(self.counter.most_common())
            self.df.columns = ["TOKEN", "FREQ"]
            if self.pos_tagged:
                self.df.loc[:, "POS"] = self.df["TOKEN"].apply(lambda t:
                                                               t.split("_")[1]
                                                               .upper())
                self.df.loc[:, "TOKEN"] = self.df["TOKEN"].apply(lambda t: t.
                                                                 split("_")[0])
            else:
                self.df.loc[:, "POS"] = ""
            if self.min_freq > 1:
                self.df = self.df[self.df["FREQ"] > self.min_freq]
            if self.stopwords:
                self.df = self.df[~self.df["TOKEN"].str.lower()
                                  .isin(self.stopwords)]
            self.df.loc[:, "PCT"] = round(self.df["FREQ"] / self.wc * 100, 3)
            self.df.loc[:, "PERCENTILE"] = self.df["FREQ"].rank(pct=True)
            self.df.loc[:, "ZSCORE"] = (self.df.FREQ -
                                        self.df.FREQ.
                                        mean()) / self.df.FREQ.std(ddof=0)
            self.df.index = self.df.index + 1
            self.df.index.name = "RANK"

    def filter_for_pos(self, pos):
        self.df_bak = self.df
        if type(pos) == str:
            self.df = self.df[self.df["POS"] == pos]
        elif type(pos) == list:
            self.df = self.df[self.df["POS"].isin(pos)]
        self.recalculate()

    def filter_out_for_pos(self, pos):
        self.df_bak = self.df
        if type(pos) == str:
            self.df = self.df[self.df["POS"] != pos]
        elif type(pos) == list:
            self.df = self.df[~self.df["POS"].isin(pos)]
        self.recalculate()

    def undo_filter(self):
        try:
            self.df = self.df_bak
        except (TypeError, AttributeError):
            pass
        else:
            self.recalculate()

    def drop_function_tokens(self):
        """Remove tokens with part-of-speech tags (Penn) indicating
        function words"""
        if self.pos_tagged:
            self.tokens = [t for t in self.tokens if t.split("_")[1].upper()
                           not in self.function_pos_tags]

    def count(self):
        if self.tokens:
            self.counter = collections.Counter(self.tokens)
        self.wc = len(self.tokens)

    def from_counter(self, counter):
        self.counter = counter
        self.tokens = sorted([e for e in self.counter.elements()])
        if not self.preserve_case:
            self.from_list(self.tokens)
        if self.drop_function_words and self.pos_tagged:
            self.drop_function_tokens()
        self.wc = len(self.tokens)
        self.create_dataframe()

    def from_list(self, tokens):
        self.tokens = tokens
        if not self.preserve_case:
            self.lowercase_tokens()
        if self.drop_function_words and self.pos_tagged:
            self.drop_function_tokens()
        self.count()
        self.create_dataframe()

    def lowercase_tokens(self):
        self.tokens = [t.lower() for t in self.tokens]

    def from_token_frame_file(self, filepath):
        self.df = pd.read_csv(filepath, index_col=0)
        self.wc = self.df["FREQ"].sum()

    def from_text(self, text, tokenizer_function=None):
        if not tokenizer_function:
            tokenizer = WordTokenizer()
            if self.pos_tagged:
                self.tokens = tokenizer.tokenize(text, which="pos")
            else:
                self.tokens = tokenizer.tokenize(text, which="regex")
        else:
            self.tokens = tokenizer_function(text)

        if not self.preserve_case:
            self.lowercase_tokens()
        if self.drop_function_words and self.pos_tagged:
            self.drop_function_tokens()
        self.count()
        self.create_dataframe()

    def __repr__(self):
        return self.df.to_string()


class WordTokenizer():

    def __init__(self, default="regex", word_chars=None):
        if not word_chars:
            self.word_chars = "A-Za-z0-9'-"
        else:
            self.word_chars = word_chars
        self.re_non_word_chars = re.compile(r"[^{}]".format(self.word_chars))
        self.default = default

    def tokenize(self, s, which=None):
        if type(s) == str:
            if not which:
                which = self.default
            if which == "whitespace":
                return self.whitespace_tokenizer(s)
            elif which == "regex":
                return self.regex_tokenizer(s)
            elif which == "pos":
                return self.pos_tokenizer(s)
            else:
                return None
        else:
            return None

    @staticmethod
    def pos_tokenizer(s):
        return ["{}_{}".format(t.split("_")[0].lower(), t.split("_")[1])
                for t in s.split() if len(t) > 3 and "_" in t and
                any([c.isalnum() for c in t.split("_")[0]]) and
                len(t.split("_")[1]) < 6]

    def regex_tokenizer(self, s):
        tokens = self.re_non_word_chars.split(s)
        tokens = [t for t in tokens if t]
        return tokens

    @staticmethod
    def whitespace_tokenizer(s):
        return s.split(" ")


def tokenize(s):
    tokens = ["{}_{}".format(t.split("_")[0].lower(), t.split("_")[1])
              for t in s.split() if len(t) > 3 and "_" in t and
              any([c.isalnum() for c in t.split("_")[0]])]
    return tokens


def keyword_list_from_files(tar_files, ref_files, fn="",
                            drop_function_words=True, min_freq=1):
    tar = token_list_from_files(tar_files, fn="", min_freq=min_freq)
    ref = token_list_from_files(ref_files, fn="", min_freq=min_freq)
    if tar and ref:
        kw = KeywordFrame(ignore_pos=False)
        if len(tar.df.index) > 0:
            kw.add_from_token_frame(tar, name="target")
            kw.add_from_token_frame(ref, name="reference")
            kw.get_keywords("target", "reference")
            kw.df.sort_values(["LOG_RATIO", "FREQ_1"], inplace=True,
                              ascending=False)
            kw_str = "\n".join(list(kw.df.head(20)["TOKEN"]))
            print(kw_str)
            if fn:
                kw.df.to_csv(os.path.join(DIR["keywords"], fn))
                print("Created keyword list: ", fn)
            return kw
        else:
            return None

    else:
        return None


def concat_text_from_xml_files(files):
    text = []
    for f in files:
        tree = etree.parse(f)
        sentences = tree.findall(".//s")
        for s in sentences:
            text.append(s.text)
    text = "\n".join(text)
    return text


def token_list_from_files(files, fn="", min_freq=1):
    text = concat_text_from_xml_files(files)
    if text:
        tok = TokenFrame(pos_tagged=True, drop_function_words=False,
                         min_freq=min_freq)
        tok.from_text(text)
        if fn:
            tok.df.to_csv(os.path.join(DIR["tokens"], fn))
            print("Created token list: ", fn)
        return tok
    else:
        print("No tokens for", fn)
        return None


def create_lists(frequency=True, keywords=True, year=True, subreddit=True,
                 month=True, min_freq=10):
    if frequency:
        if year:  # By year
            for y in YEARS:
                pattern = os.path.join(DIR["corpus_tag_xml"],
                                       "*_{}-*.xml".format(y))
                fn = "tokens_for_year_{}.csv".format(y)
                token_list_from_files(glob.glob(pattern), fn)
        if subreddit:
            for s in SUBREDDITS:
                print("Generate token list for", s)
                pattern = os.path.join(DIR["corpus_tag_xml"],
                                       "*_{}_*.xml".format(s))
                fn = "tokens_for_subreddit_{}.csv".format(s)
                files = glob.glob(pattern)
                token_list_from_files(files, fn)
        if month:
            for m in range(1, 13):
                m = str(m).zfill(2)
                pattern = os.path.join(DIR["corpus_tag_xml"],
                                       "*-{}.xml".format(m))
                fn = "tokens_for_month_{}.csv".format(m)
                token_list_from_files(glob.glob(pattern), fn)
        if year and month:
            for y in YEARS:
                for m in range(1, 13):
                    m = str(m).zfill(2)
                    pattern = os.path.join(DIR["corpus_tag_xml"],
                                           "*_{}-{}.xml".format(y, m))
                    fn = "tokens_for_year_month_{}_{}.csv".format(y, m)
                    token_list_from_files(glob.glob(pattern), fn)
        if subreddit and year:
            for s in SUBREDDITS:
                for y in YEARS:
                    pattern = os.path.join(DIR["corpus_tag_xml"],
                                           "*_{}_{}-*.xml".format(s, y))
                    fn = "tokens_for_subreddit_year_{}_{}.csv".format(s, y)
                    token_list_from_files(glob.glob(pattern), fn)
        if subreddit and year and month:
            for s in SUBREDDITS:
                for y in YEARS:
                    for m in range(1, 13):
                        m = str(m).zfill(2)
                        pattern = os.path.join(DIR["corpus_tag_xml"],
                                               "*_{}_{}-{}.xml".format(s, y,
                                                                       m))
                        fn = "tokens_for_subreddit_year_month_{}_{}_{}.csv"\
                             .format(s, y, m)
                        token_list_from_files(glob.glob(pattern), fn)
    if keywords:
        """
        Keyword generation is slow and not yet optimized, but suffices for now.
        """
        min_freq = 10
        all_pattern = os.path.join(DIR["corpus_tag_xml"], "*.xml")
        all_files = glob.glob(all_pattern)
        if year:
            for y in YEARS:
                tar_pattern = os.path.join(DIR["corpus_tag_xml"],
                                           "*_{}-*.xml".format(y))
                fn = "keywords_for_year_{}.csv".format(y)
                get_keywords(tar_pattern, all_files, fn, min_freq)
        if subreddit:
            for s in SUBREDDITS:
                tar_pattern = os.path.join(DIR["corpus_tag_xml"],
                                           "*_{}_*.xml".format(s))
                fn = "keywords_for_subreddit_{}.csv".format(s)
                get_keywords(tar_pattern, all_files, fn, min_freq)
        if month:
            for m in range(1, 13):
                m = str(m).zfill(2)
                tar_pattern = os.path.join(DIR["corpus_tag_xml"],
                                           "*-{}.xml".format(m))
                fn = "keywords_for_month_{}.csv".format(m)
                get_keywords(tar_pattern, all_files, fn, min_freq)
        if year and month:
            for y in YEARS:
                for m in range(1, 13):
                    m = str(m).zfill(2)
                    tar_pattern = os.path.join(DIR["corpus_tag_xml"],
                                               "*_{}-{}.xml".format(y, m))
                    fn = "keywords_for_year_month_{}_{}.csv".format(y, m)
                    get_keywords(tar_pattern, all_files, fn, min_freq)
        if subreddit and year:
            for s in SUBREDDITS:
                for y in YEARS:
                    tar_pattern = os.path.join(DIR["corpus_tag_xml"],
                                               "*_{}_{}-*.xml".format(s, y))
                    fn = "keywords_for_subreddit_year_{}_{}.csv".format(s, y)
                    get_keywords(tar_pattern, all_files, fn, min_freq)
        if subreddit and year and month:
            for s in SUBREDDITS:
                for y in YEARS:
                    for m in range(1, 13):
                        m = str(m).zfill(2)
                        tar_pattern = os.path.join(DIR["corpus_tag_xml"],
                                                   "*_{}_{}-{}.xml"
                                                   .format(s, y, m))
                        fn = "tokens_for_subreddit_year_month_{}_{}_{}.csv"\
                             .format(s, y, m)
                        get_keywords(tar_pattern, all_files, fn, min_freq)


def get_keywords(tar_pattern, all_files, fn, min_freq):
    start = datetime.datetime.now()
    print("Generating", fn, start)
    tar_files, ref_files = get_tar_and_ref_files(tar_pattern, all_files)
    keyword_list_from_files(tar_files, ref_files, fn, min_freq)
    end = datetime.datetime.now()
    diff = end - start
    m, s = divmod(diff.total_seconds(), 60)
    print("Keyword generation took", int(m), "min", round(s, 2), "sec")


def get_tar_and_ref_files(tar_pattern, all_files):
    tar_files = glob.glob(tar_pattern)
    ref_files = [f for f in all_files if f not in tar_files]
    return tar_files, ref_files


def main(args=None):
    try:
        os.makedirs(DIR["tokens"])
    except FileExistsError:
        pass
    try:
        os.makedirs(DIR["keywords"])
    except FileExistsError:
        pass
    if args:
        create_lists(frequency=args.freq, keywords=args.kw, year=False,
                     min_freq=args.min_freq)
    else:
        create_lists(frequency=True, keywords=True, year=False,
                     min_freq=10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create frequency and keyword"
                                     "lists")
    parser.add_argument('-k', '--keyword', dest="kw",
                              help="Create keyword lists",
                              action="store_true")
    parser.add_argument('-f', '--frequency', dest="freq",
                              help="Create frequency lists",
                              action="store_true")
    parser.add_argument('-m', '--min-freq', dest="min_freq",
                              help="Minimum token frequency during"
                              "keyword generation (default: 10)",
                              action="store", type=int, metavar="N",
                              default=10)
    args = parser.parse_args()
    main(args)
