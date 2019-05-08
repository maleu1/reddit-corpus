import os
import datetime

"""
    This file is part of reddit-corpus.

    reddit-corpus is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    reddit-corpus is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with reddit-corpus.  If not, see <http://www.gnu.org/licenses/>.
"""

FIRST_DAY = "2005-01-01"
LAST_DAY = "2019-04-22"

FIRST_DAY = datetime.datetime.strptime(FIRST_DAY, "%Y-%m-%d").date()
LAST_DAY = datetime.datetime.strptime(LAST_DAY, "%Y-%m-%d").date()

CONTINUE_FROM_LAST = False
INCLUDE_RELATED = False

MAIN_SUBREDDITS = {"Rupaul": "rupaulsdragrace"}

SUBREDDITS = [v for v in MAIN_SUBREDDITS.values()]

RELATED_SUBREDDITS = {"MechanicalKeyboards": "mechanicalkeyboards",
                      "ArcherFX": "archerfx",
                      "freefolk": "freefolk"}
if INCLUDE_RELATED:
    SUBREDDITS += list(RELATED_SUBREDDITS.values())
