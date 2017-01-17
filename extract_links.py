import os
import glob
import re
from urllib.parse import urlsplit

from lxml import etree
import pandas as pd

from config import DIR, YEARS, SUBREDDITS


class LinkExtractor():
    """A class to extract and classify links from reddit posts

    The extraction regex fails at validating complex links,
    but is faster than more comprehensive solutions
    (e.g. https://gist.github.com/imme-emosol/731338) that aim to validate
    correct links as well."""
    RE_URL = re.compile(r'https?://[^\s)>\]]+')
    IMAGE_KEYWORDS = [".png", ".jpg", ".jpeg", ".bmp",
                      "imgur.com", "flickr.com"]
    VIDEO_KEYWORDS = ["watch?v", "youtube.com", "youtu.be", "streamable.com",
                      "vimeo.com", "?gifv", "gfycat.com", "reactiongifs.com",
                      "vine.co"]
    IMG_OR_VID_KEYWORDS = ["instagram.com", "imgur.com", ".gif",
                           "reddituploads.com"]

    def __init__(self):
        self.df = pd.DataFrame()

    def extract(self, text, metadata=None):
        links = []
        for m in self.RE_URL.finditer(text):
            if not metadata:
                metadata = {}
            metadata["LINK_DOMAIN"] = self.get_domain(m.group(0))
            metadata["LINK_MEDIA"] = self.identify_media(m.group(0))
            metadata["EXTRACTED_LINK"] = m.group(0)
            links.append(metadata)
        if links:
            df = pd.DataFrame.from_dict(links)
            df.columns = [c.upper().replace(" ", "_") for c in df.columns]
            self.df = self.df.append(df, ignore_index=True)

    @staticmethod
    def get_domain(s):
        try:
            d = "{0.netloc}".format(urlsplit(s)).replace("www.", "")
        except ValueError as e:
            print(e)
            d = s.replace("//", "").split("/")[0].replace("www.", "")
            print(d)

        return d

    def identify_media(self, s):
        last = s.split("/")[-1].lower()
        domain = self.get_domain(s)
        media = ""
        for kw in self.IMAGE_KEYWORDS:
            if kw in last or kw in domain:
                media = "image"
                break
        if not media:
            for kw in self.VIDEO_KEYWORDS:
                if kw in last or kw in domain:
                    media = "video"
        if not media:
            for kw in self.IMG_OR_VID_KEYWORDS:
                if kw in last or kw in domain:
                    media = "image/video"
        return media

    def add_link(self, link, metadata=None):
        """Utility to explicitly add a single link"""
        if not metadata:
            metadata = {}
        metadata["EXTRACTED_LINK"] = link
        df = pd.DataFrame.from_dict([metadata])
        df.columns = [c.upper().replace(" ", "_") for c in df.columns]
        self.df = self.df.append(df, ignore_index=True)

    def sort(self, by="DATE", asc=False):
        try:
            self.df.sort_values(by=by, ascending=asc, inplace=True)
        except KeyError as e:
            print(e)

    def count(self):
        return len(self.df.index)

    def save(self, filepath):
        self.sort()
        self.df.to_csv(filepath)

    def get_top_links(self, n=1):
        return self.df["EXTRACTED_LINK"].value_counts().nlargest(n)


def main():
    try:
        os.makedirs(DIR["links"])
    except FileExistsError:
        pass
    for year in YEARS:
        for subreddit in SUBREDDITS:
            extr = LinkExtractor()
            fp = os.path.join(DIR["links"], "links_{}_{}.csv"
                              .format(subreddit.lower(), year))
            pattern = os.path.join(DIR["xml"], "{}/{}/reddit_*.xml"
                                   .format(subreddit.lower(), year))
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
                    for ci, c in enumerate(coms):
                        if c.text:
                            meta = dict(c.attrib)
                            meta["TYPE"] = "submission"
                            extr.extract(c.text, metadata=dict(meta))
                extr.save(fp)
            if len(extr.df.index > 0):
                extr.sort()


if __name__ == "__main__":
    main()
