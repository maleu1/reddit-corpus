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
r/nba was created on 2008-11-04,with r/lakers and r/ripcity also in 2008.
Most of the other team subs were created in 2010.
Posts are rare even in early 2010, so skipping 2008 & 2009 seems reasonable.

If CONTINUE_FROM_LAST is True the script will start with from the last day for which
it has downloaded data instead of FIRST_DAY after a restart. If FALSE it will
always iterate from FIRST_DAY to LAST_DAY no matter what has been indexed.
"""
FIRST_DAY = "2016-12-31"
LAST_DAY = "2016-12-31"
FIRST_DAY = datetime.datetime.strptime(FIRST_DAY, "%Y-%m-%d").date()
LAST_DAY = datetime.datetime.strptime(LAST_DAY, "%Y-%m-%d").date()
YEARS = range(2010, 2017)
CONTINUE_FROM_LAST = False
INCLUDE_RELATED = True


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

RELATED_SUBREDDITS = {"Eurolague": "euroleague",
                      "nbabreakdown": "nbabreakdown",
                      "nbadiscussion": "nbadiscussion",
                      "collegebasketball": "collegebasketball",
                      "basketball": "basketball",
                      "nbalounge": "nbalounge",
                      "nbaww": "nbaww",
                      "fantasybball": "fantasybball",
                      "NBAGifs": "nbagifs",
                      "WNBA": "wnba",
                      "nbaimages": "nbaimages"}
if INCLUDE_RELATED:
    SUBREDDITS += list(RELATED_SUBREDDITS.values())

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
       "links": os.path.join(BASE_DIR, "links"),
       "logs": os.path.join(BASE_DIR, "logs")
       }

PATH = {"metadata": os.path.join(BASE_DIR, "meta", "metadata.csv")}
