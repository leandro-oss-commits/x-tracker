#!/usr/bin/env python3
"""
X/Twitter Tracker — Fetch recent tweets from tracked accounts via Nitter RSS
"""

import urllib.request
import xml.etree.ElementTree as ET
import json
import time
import os
import re
from datetime import datetime

ACCOUNTS = [
    # Harness Engineering / AI Builders
    "karpathy",
    "AnthropicAI",
    "latent_space_pod",
    "garytalksstuff",
    
    # Practical AI
    "OpenAI",
    "ycombinator",
    "indydevdan",
    "tobi",
    "amasad",
]

MAX_TWEETS_PER_ACCOUNT = 10

def clean_html(text):
    """Strip HTML tags from text."""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
    return text.strip()

def parse_date(date_str):
    """Parse RSS date to ISO format."""
    from email.utils import parsedate_to_datetime
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except:
        return date_str

def fetch_tweets(username, max_results=MAX_TWEETS_PER_ACCOUNT):
    """Fetch recent tweets from a user via Nitter RSS."""
    url = f"https://nitter.net/{username}/rss"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (XTracker/1.0)"})
    
    tweets = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read().decode()
    except Exception as e:
        print(f"  [WARN] Failed to fetch @{username}: {e}")
        return tweets
    
    try:
        root = ET.fromstring(xml_data)
        ns = {"dc": "http://purl.org/dc/elements/1.1/"}
        
        for i, item in enumerate(root.findall(".//item")):
            if i >= max_results:
                break
            
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            creator = item.findtext("dc:creator", "", ns)
            desc = item.findtext("description", "")
            
            # Clean the description to get plain text
            text = clean_html(desc)
            # Truncate to first meaningful paragraph
            text = text.split("\n")[0] if "\n" in text else text
            text = text[:280] if len(text) > 280 else text
            
            # Skip retweets (optional)
            is_rt = title.startswith("RT") if title else False
            
            tweets.append({
                "username": username,
                "displayName": creator or username,
                "text": text,
                "link": link,
                "publishedAt": parse_date(pub_date),
                "isRetweet": is_rt,
                "avatar": f"https://nitter.net/pic/pbs.twimg.com%2Fprofile_images%2Fdefault_profile_normal.png",
            })
    except Exception as e:
        print(f"  [WARN] Parse error for @{username}: {e}")
    
    return tweets

def main():
    all_tweets = []
    
    for username in ACCOUNTS:
        print(f"Fetching @{username}...")
        tweets = fetch_tweets(username)
        if tweets:
            print(f"  Got {len(tweets)} tweets")
            all_tweets.extend(tweets)
        else:
            print(f"  [WARN] No tweets for @{username}")
        time.sleep(1)  # Rate limiting
    
    # Sort by date descending
    all_tweets.sort(key=lambda x: x["publishedAt"], reverse=True)
    
    # Save
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tweets.json")
    with open(path, "w") as f:
        json.dump(all_tweets, f, indent=2)
    
    print(f"\nDone! Saved {len(all_tweets)} tweets to tweets.json")

if __name__ == "__main__":
    main()
