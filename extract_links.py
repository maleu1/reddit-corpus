import os
import glob
import re

from lxml import etree
import pandas as pd

from config import DIR, PATH


class LinkExtractor():
    # Expression from https://gist.github.com/imme-emosol/731338
    R = re.compile(r'^(?:(?:https?|ftp)://)(?:\S+(?::\S*)?@)?'
                   '(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])'
                   '(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}'
                   '(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))'
                   '|(?:(?:[a-z\u00a1-\uffff0-9]+-?)*[a-z\u00a1-\uffff0-9]+)'
                   '(?:\.(?:[a-z\u00a1-\uffff0-9]+-?)*[a-z\u00a1-\uffff0-9]+)'
                   '*(?:\.(?:[a-z\u00a1-\uffff]{2,})))(?::\d{2,5})?'
                   '(?:/[^\s]*)?$')

    def __init__(self):
        self.df = pd.DataFrame()

    def extract(self, text, metadata=None):
        links = []
        for m in self.R.finditer(text):
            print(m)
            if not metadata:
                metadata = {}
            metadata["EXTRACTED_LINK"] = m.group(0)
            links.append(metadata)
        if links:
            df = pd.DataFrame.from_dict(links)
            df.columns = [c.upper().replace(" ", "_") for c in df.columns]
            self.df = self.df.append(df, ignore_index=True)

    def add_link(self, link, metadata=None):
        """Utility to explicitly add a single link"""
        if not metadata:
            metadata = {}
        metadata["EXTRACTED_LINK"] = link
        df = pd.DataFrame.from_dict([metadata])
        df.columns = [c.upper().replace(" ", "_") for c in df.columns]
        self.df = self.df.append(df, ignore_index=True)

    def sort(self, by="DATE", asc=False):
        self.df.sort_values(by=by, ascending=asc, inplace=True)

    def count(self):
        return len(self.df.index)

    def save(self, filepath):
        self.sort()
        self.df.to_csv(filepath)

    def get_top_links(self, n=1):
        return self.df["EXTRACTED_LINK"].value_counts().nlargest(n)


def main():
    extr = LinkExtractor()
    pattern = os.path.join(DIR["xml"], "**/**/reddit_*.xml")
    for f in glob.iglob(pattern, recursive=True):
        fn = os.path.basename(f)
        tree = etree.parse(f)
        subs = tree.findall(".//submission")
        num_subs = len(subs)
        for si, s in enumerate(subs):
            print(fn, "\t", si, "/", num_subs)
            meta = dict(s.attrib)
            if s.text:
                meta["TYPE"] = "submission"
                extr.extract(s.text, metadata=meta)
            else:
                extr.add_link(meta["url"], metadata=meta)

            coms = s.findall(".//comment")
            num_coms = len(coms)
            for ci, c in enumerate(coms):
                print(fn, "\t", si, "/", num_subs, "\t", ci, "/", num_coms)
                if c.text:
                    meta = dict(c.attrib)
                    meta["TYPE"] = "submission"
                    extr.extract(c.text, metadata=dict(meta))
        extr.save(PATH["links"])
    if len(extr.df.index > 0):
        extr.sort()
        print(extr.df)


if __name__ == "__main__":
    main()
