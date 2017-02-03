import os
import glob
import argparse
import datetime
from pprint import pprint

import spacy
import pymongo as pm
from lxml import etree

from config import DIR


def strip_pos(s):
    tokens = [t.split("_")[0] for t in s.split()]
    return " ".join(tokens)


def get_text(post):
    return "".join(post.itertext())


def tag_with_spacy(text, nlp):
    doc = nlp(text)
    for i, sent in enumerate(doc.sents):
        tokens = [t for t in sent]
    text = " ".join(["{}_{}".format(t.orth_, t.tag_) for t in tokens])
    return text


def get_wc(s):
    tokens = ["{}_{}".format(t.split("_")[0].lower(), t.split("_")[1])
              for t in s.split() if len(t) > 3 and "_" in t and
              any([c.isalnum() for c in t.split("_")[0]])]
    return len(tokens)


def get_post_fields(sub, com):
    d = {}
    sid = sub.get("id")
    if com:
        d["parent_id"] = com.get("parent_id")
        d["post_id"] = com.get("id")
        d["_id"] = "{}_{}_{}".format(sid, d["parent_id"], d["post_id"])
        d["author"] = com.get("author_name")
        d["date"] = datetime.datetime.strptime(com.get("date"), "%Y-%m-%d")
        d["created"] = datetime.datetime.utcfromtimestamp(
            float(com.get("created_utc")))
        d["gilded"] = bool(com.get("gilded"))
        d["title"] = ""
        d["score"] = int(com.get("score"))
        d["permalink"] = com.get("permalink")
    else:
        d["_id"] = sid
        d["author"] = sub.get("author_name")
        d["date"] = sub.get("date")
        d["post_id"] = sid
        d["created"] = datetime.datetime.utcfromtimestamp(
            float(sub.get("created_utc")))
        d["gilded"] = bool(sub.get("gilded"))
        d["title"] = sub.get("title")
        d["parent_id"] = ""
        d["self"] = bool(sub.get("is_self"))
        d["score"] = int(sub.get("score"))
        d["url"] = sub.get("url")
        d["permalink"] = sub.get("permalink")
    d["subreddit"] = sub.get("subreddit_name").lower()
    return d


def ingest_file(f, db, nlp, verbose=1):
    fn = os.path.basename(f)
    if verbose > 0:
        print(fn)
    root = etree.parse(f).getroot()
    for sub in root.findall(".//submission"):
        d = get_post_fields(sub, None)
        if sub.text:
            d["text"] = sub.text
            d["pos"] = tag_with_spacy(d["text"], nlp)
            d["wc"] = get_wc(d["pos"])
        else:
            d["wc"] = 0
        if verbose > 1:
            print(fn, "\t", d["_id"])
        try:
            db.posts.insert_one(d)
        except pm.errors.DuplicateKeyError:
            pass
        for com in sub.findall(".//comment"):
            d = get_post_fields(sub, com)
            if com.text:
                d["text"] = com.text
                d["pos"] = tag_with_spacy(d["text"], nlp)
                d["wc"] = get_wc(d["pos"])
            else:
                d["wc"] = 0
            if verbose > 2:
                print(fn, "\t\t", d["_id"])
            try:
                db.posts.insert_one(d)
            except pm.errors.DuplicateKeyError:
                pass


def ingest(client, scope, verbose=1):
    db = client.nbareddit
    nlp = spacy.load('en')
    for f in glob.iglob(os.path.join(DIR["xml"], "**/**/"
                                     "{}.xml".format(scope)),
                        recursive=True):
        ingest_file(f, db, nlp, verbose)


def drop_database(client, verbose=1):
    client.drop_database('nbareddit')
    if verbose > 0:
        print("Dropped database")


def drop_collection(client, which, verbose=1):
    client.nbareddit.drop_collection(which)
    if verbose > 0:
        print("Dropped collection {}".format(which))


def main(args):
    client = pm.MongoClient()
    if args.info:
        print("Database: nbareddit")
        db = client.nbareddit
        pprint(db.command("dbstats"))
        print("Collection: sentences")
        pprint(db.command("collstats", "posts"))
        exit()
    if args.drop:
        if args.drop == "db":
            drop_database(client, args.verbose)
        else:
            drop_collection(client, args.drop, args.verbose)
    ingest(client, args.scope, args.verbose)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Insert sentences into"
                                     "MongoDB database")
    parser.add_argument("-d", "--drop", dest="drop",
                        help="Drop database ('db') or specified collection",
                        action="store", type=str, default="")
    parser.add_argument("-v", "--verbose", dest="verbose",
                        help="Set level of verbosity (default=1)",
                        action="store", type=int, default=1)
    parser.add_argument("-s", "--scope", action="store", default="*",
                        help="Specify a glob-style pattern to restrict"
                        "which corpus files are imported (default: *)")
    parser.add_argument("-i", "-info", action="store_true", dest="info",
                        help="Only print database/collection info and exit")

    args = parser.parse_args()
    main(args)
