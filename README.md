# reddit-nba-corpus
A (work-in-progress) toolkit to create and explore a corpus of posts from r/nba, team subreddits, and other related boards (r/fantasybball, r/collegebasketball, r/nbaww, r/nbabreakdown, etc).

You will need to create a copy of sample_config.py, rename it to config.py and fill it with reddit account credentials plus whatever settings you want. You can specify a start date and end date in config.py and then use download_posts.py to download date-by-date (either date-first or subreddit-first based on provided arguments) or simply provide the --live argument to the script to download just posts "from N days ago". The latter makes sense if you intend to set up a daily cron job to, e.g., get "yesterday's submissions".

To download the files, combine the medatadata and create compiled "SUBREDDIT-YEAR-MONTH" corpus files with and without part-of-speech tagging in XML and TXT, run the scripts in the following order:

1.  download_posts.py
2.  aggregate_metadata.py
3.  compile_corpus.py

Once the corpus is compiled you can use generate_lists.py to create token frequency and keyword lists and extract_links to extract links (duh). Both scripts are still very basic, but could be used for some interesting things.

Not optimized for runtime/efficiency, yet.
