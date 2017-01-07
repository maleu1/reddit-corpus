import os
import datetime

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


CLIENT_ID = "REDDIT_API_CLIENT_ID"
CLIENT_SECRET = "REDDIT_API_CLIENT_SECRET"
USER_AGENT = "MEANINGFUL TEXT TO IDENTIFY THE PROJECT AND ACCOUNT"

"""
Default setup is to get data from the years 2010 to 2016. Modify as desired.

r/nba was created on 2008-11-04,with r/lakers and r/ripcity also in 2008.
Most of the other team subs were created in 2010.
Posts are rare even in early 2010, so skipping 2008 & 2009 seems reasonable.
"""
FIRST_DAY = "2010-01-01"
LAST_DAY = "2016-12-31"
FIRST_DAY = datetime.datetime.strptime(FIRST_DAY, "%Y-%m-%d")
LAST_DAY = datetime.datetime.strptime(LAST_DAY, "%Y-%m-%d")

YEARS = range(2010, 2017)

TEAM_SUBREDDITS = {"Los Angeles Lakers ": "lakers",
                   "Golden State Warriors ": "warriors",
                   "Chicago Bulls ": "chicagobulls",
                   "Toronto Raptors ": "torontoraptors",
                   "Boston Celtics ": "bostonceltics",
                   "Cleveland Cavaliers ": "clevelandcavs",
                   "New York Knicks ": "nyknicks",
                   "San Antonio Spurs ": "nbaspurs",
                   "Miami Heat ": "heat",
                   "Houston Rockets ": "rockets",
                   "Philadelphia 76ers ": "sixers",
                   "Portland Trail Blazers ": "ripcity",
                   "Oklahoma City Thunder ": "thunder",
                   "Minnesota Timberwolves ": "timberwolves",
                   "Dallas Mavericks ": "mavericks",
                   "Atlanta Hawks ": "atlantahawks",
                   "Los Angeles Clippers ": "laclippers",
                   "Detroit Pistons ": "detroitpistons",
                   "Washington Wizards ": "washingtonwizards",
                   "Charlotte Hornets ": "charlottehornets",
                   "Sacramento Kings ": "kings",
                   "Milwaukee Bucks ": "mkebucks",
                   "Phoenix Suns ": "suns",
                   "Indiana Pacers ": "pacers",
                   "Orlando Magic ": "orlandomagic",
                   "Denver Nuggets ": "denvernuggets",
                   "Utah Jazz ": "utahjazz",
                   "Brooklyn Nets ": "gonets",
                   "Memphis Grizzlies ": "memphisgrizzlies",
                   "New Orleans Pelicans ": "nolapelicans"}

SUBREDDITS = [v for v in TEAM_SUBREDDITS.values()]
SUBREDDITS.append("nba")

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

DIR = {"xml": os.path.join(BASE_DIR, "xml"),
       "meta": os.path.join(BASE_DIR, "meta"),
       "corpus_xml": os.path.join(BASE_DIR, "corpus", "xml"),
       "corpus_txt": os.path.join(BASE_DIR, "corpus", "txt"),
       "corpus_tag_xml": os.path.join(BASE_DIR, "corpus", "tag_xml"),
       "corpus_tag_txt": os.path.join(BASE_DIR, "corpus", "tag_txt"),
       "tokens": os.path.join(BASE_DIR, "lists", "tokens"),
       "keywords": os.path.join(BASE_DIR, "lists", "keywords"),
       "stats": os.path.join(BASE_DIR, "stats"),
       "plots": os.path.join(BASE_DIR, "plots")
       }

PATH = {"metadata": os.path.join(BASE_DIR, "full_metadata.csv")}
