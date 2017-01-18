import os
import logging

import spacy
import pandas as pd
from lxml import etree

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


def get_xml(fp):
    try:
        return etree.parse(os.path.join(DIR["xml"], fp))
    except (IOError, TypeError):
        return None


def create_subcorpus(g):
    r = g.iloc[0]
    y = str(int(r["YEAR"]))
    m = str(int(r["MONTH"])).zfill(2)
    handle = "{}_{}-{}".format(r["SUBREDDIT"], int(r["YEAR"]), m)
    num_subs = len(g)
    filenames = sorted(g["XML_FN"])
    root = etree.Element("subcorpus")
    root.set("num_sub", str(num_subs))
    root.set("year", str(r["YEAR"]))
    root.set("month", str(r["MONTH"]))
    root.set("subreddit", r["SUBREDDIT"])
    root.set("handle", handle)
    id_set = set([])
    for fn in filenames:
        tree = get_xml(os.path.join(r["SUBREDDIT"].lower(), y, fn))
        if tree is not None:
            subs = tree.findall(".//submission")
            for sub in subs:
                sid = sub.get("id")
                # why is this dedup even needed? DL bug?
                if sid not in id_set:
                    id_set.add(sid)
                    sub.set("handle", handle)
                    root.append(sub)
    tree = etree.ElementTree(root)
    fn = "corpus_{}.xml".format(handle)
    fp = os.path.join(DIR["corpus_xml"], fn)
    tree.write(fp, pretty_print=True, encoding='utf-8', xml_declaration=True)
    g["CORPUS_FN"] = fn
    g["SUBCORPUS"] = handle
    logging.info("Compiled {}".format(fn))
    return g


def get_wc(s):
    tokens = ["{}_{}".format(t.split("_")[0].lower(), t.split("_")[1])
              for t in s.split() if len(t) > 3 and "_" in t and
              any([c.isalnum() for c in t.split("_")[0]])]
    return len(tokens)


def parse_with_spacy(text, nlp):
    doc = nlp(text)
    entities = [e for e in doc.ents]
    ent_elems = []
    for i, ent in enumerate(entities):
        e = etree.Element("entity")
        e.text = ent.orth_
        e.set("label", ent.label_)
        e.set("n", str(i + 1))
        ent_elems.append(e)
    sent_elems = []
    text_wc = 0
    for i, sent in enumerate(doc.sents):
        tokens = [t for t in sent]
        text = " ".join(["{}_{}".format(t.orth_, t.tag_) for t in tokens])
        wc = get_wc(text)
        text_wc += wc
        s = etree.Element("s")
        s.text = text
        s.set("n", str(i + 1))
        s.set("wc", str(wc))
        sent_elems.append(s)
    return sent_elems, ent_elems, text_wc


def tag(files, nlp):
    for fn in files:
        in_path = os.path.join(DIR["corpus_xml"], fn)
        out_path = os.path.join(DIR["corpus_tag_xml"], fn)
        tree = etree.parse(in_path)
        subs = tree.findall(".//submission")
        for sub in subs:
            entities = etree.Element("entities")
            if sub.text:
                sents, ents, wc = parse_with_spacy(sub.text, nlp)
                sub.set("wc", str(wc))
                for i, s in enumerate(sents):
                    sub.insert(i, s)
                sub.text = ""
                entities = etree.Element("entities")
                entities.set("num", str(len(ents)))
                for e in ents:
                    entities.append(e)
            sub.append(entities)
            coms = sub.findall(".//comment")
            for com in coms:
                entities = etree.Element("entities")
                if com.text:
                    sents, ents, wc = parse_with_spacy(com.text, nlp)
                    com.set("wc", str(wc))
                    com.set("num_sentences", str(len(sents)))
                    for s in sents:
                        com.append(s)
                    com.text = ""
                    entities.set("num", str(len(ents)))
                    for e in ents:
                        entities.append(e)
                com.append(entities)
        tree.write(out_path, pretty_print=True, encoding='utf-8',
                   xml_declaration=True)
        logging.info("Tagged {}".format(fn))


def tagged_to_plaintext(files):
    for fn in files:
        in_path = os.path.join(DIR["corpus_tag_xml"], fn)
        out_path = os.path.join(DIR["corpus_tag_txt"],
                                fn.replace(".xml", ".txt"))
        with open(out_path, "w") as h:
            try:
                tree = etree.parse(in_path)
            except IOError:
                pass
            else:
                sents = tree.findall(".//s")
                for sent in sents:
                    if sent.text:
                        h.write(sent.text)
                        h.write("\n")


def to_plaintext(files):
    for fn in files:
        in_path = os.path.join(DIR["corpus_xml"], fn)
        out_path = os.path.join(DIR["corpus_txt"], fn.replace(".xml", ".txt"))
        with open(out_path, "w") as h:
            tree = etree.parse(in_path)
            subs = tree.findall(".//submission")
            for sub in subs:
                if sub.text:
                    h.write(sub.text)
                coms = sub.findall(".//comment")
                for com in coms:
                    if com.text:
                        h.write(com.text)
                        h.write("\n")
                h.write("\n\n")


def add_ling_information(r):
    handle = "{}_{}-{}".format(r["SUBREDDIT"], r["YEAR"], r["MONTH"])
    r["CORPUS_FN"] = "corpus_{}.xml".format(handle)
    try:
        tree = etree.parse(os.path.join(DIR["corpus_tag_xml"], r["CORPUS_FN"]))
    except (IOError, OSError):
        pass
    else:
        sub_str = ".//submission[@id='{}']".format(r["ID"])
        sub = tree.find(sub_str)
        if sub:
            r["SELF_WC"] = int(sub.get("wc", 0))
            coms = sub.findall(".//comment")
            com_wc = []
            com_sc = []
            for com in coms:
                com_wc.append(int(com.get("wc", 0)))
                com_sents = com.findall(".//s")
                com_sc.append(len(com_sents))
            r["COM_WC"] = sum(com_wc)
            try:
                r["COM_MEAN_WC"] = r["COM_WC"] / r["NUM_COM_FOUND"]
            except ZeroDivisionError:
                r["COM_MEAN_WC"] = 0
            r["COM_SC"] = sum(com_sc)
            try:
                r["COM_MEAN_SC"] = r["COM_SC"] / r["NUM_COM_FOUND"]
            except ZeroDivisionError:
                r["COM_MEAN_SC"] = 0
            r["WC"] = r["SELF_WC"] + r["COM_WC"]
            r["MEAN_WC"] = ((r["COM_WC"] + r["SELF_WC"]) /
                            (r["NUM_COM_FOUND"] + 1))
    return r


def ensure_dirs():
    try:
        os.makedirs(DIR["corpus_xml"])
    except FileExistsError:
        pass
    try:
        os.makedirs(DIR["corpus_txt"])
    except FileExistsError:
        pass
    try:
        os.makedirs(DIR["corpus_tag_xml"])
    except FileExistsError:
        pass
    try:
        os.makedirs(DIR["corpus_tag_txt"])
    except FileExistsError:
        pass


def main():
    try:
        os.makedirs(DIR["logs"])
    except FileExistsError:
        pass
    logfile = os.path.join(DIR["logs"], "download.log")
    logging.basicConfig(filename=logfile, level=logging.INFO,
                        filemode="w")
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)-8s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    ensure_dirs()
    try:
        meta_df = pd.read_csv(PATH["metadata"], index_col=0)
    except IOError:
        logging.warning("Run aggregate_metadata.py and make sure {} exists"
                        .format(PATH["METADATA"]))
    else:
        # group by subreddit and YYYY-MM for subcorpora
        grouped = meta_df.groupby(["SUBREDDIT", "YEAR", "MONTH"])
        logging.info("Creating the untagged XML corpus")
        meta_df = grouped.apply(create_subcorpus)
        files = set(meta_df["CORPUS_FN"])
        logging.info("Creating a plaintext version of the corpus")
        to_plaintext(files)
        logging.info("Creating the tagged XML corpus")
        nlp = spacy.load('en')
        tag(files, nlp)
        logging.info("Creating a plaintext version of the tagged corpus")
        tagged_to_plaintext(files)
        logging.info("Adding word and sentence counts to metadata")
        meta_df = meta_df.apply(add_ling_information, axis="columns")
        meta_df.to_csv(PATH["metadata"])


if __name__ == "__main__":
    main()
