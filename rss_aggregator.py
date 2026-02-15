import os
import feedparser
import pandas as pd
import sqlite3
import datetime
import re
import time
import urllib.parse

# Configuration
DB_PATH = 'research.db'
SOURCES_PATH = 'sources.csv'

class ImpactScorer:
    """
    Zero-cost heuristic engine to rate the 'Strategic Impact' of a headline.
    Rates from 0 to 100 based on keywords and patterns.
    """
    
    HIGH_VALUE_PATTERNS = [
        r"report", r"outlook", r"forecast", r"trends?", r"202\d", r"future of", 
        r"state of", r"comprehensive", r"strategic", r"global economy", 
        r"white ?paper", r"survey", r"index", r"roadmap", r"playbook",
        r"implications", r"deep dive", r"research", r"study", r"shift"
    ]
    
    NOISE_PATTERNS = [
        r"webinar", r"podcast", r"join us", r"register", r"hiring", r"career", 
        r"award", r"appointed", r"partner", r"quarterly results", r"earnings", 
        r"dividend", r"stock", r"shareholder", r"meet our", r"congratulations"
    ]

    def score(self, title, description):
        text = (title + " " + description).lower()
        score = 50 # Base score
        
        # Check high value indicators
        for pattern in self.HIGH_VALUE_PATTERNS:
            if re.search(pattern, text):
                score += 15
                
        # Check noise indicators
        for pattern in self.NOISE_PATTERNS:
            if re.search(pattern, text):
                score -= 50
                
        return max(0, min(100, score))

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            url TEXT PRIMARY KEY,
            title TEXT,
            firm TEXT,
            published_date DATE,
            summary TEXT,
            impact_score INTEGER,
            region TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_rss_url(strategy, query):
    """
    Constructs the RSS url based on the strategy type.
    """
    encoded_query = urllib.parse.quote(query)
    if strategy == 'google_news':
        return f"https://news.google.com/rss/search?q={encoded_query}"
    elif strategy == 'bing_rss':
        # Bing requires format=rss
        return f"https://www.bing.com/search?q={encoded_query}&format=rss"
    # Fallback or direct link
    return query

def fetch_feed(source_row, scorer):
    url = get_rss_url(source_row['strategy'], source_row['query'])
    print(f"Fetching {source_row['name']} via {source_row['strategy']}...")
    
    try:
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries[:10]: # Top 10 only
            title = entry.get('title', 'No Title')
            link = entry.get('link', '')
            summary = entry.get('summary', '').replace('<b>', '').replace('</b>', '').replace('...','').strip()
            # Clean up Google's " - SourceName" suffix
            title = title.rsplit(' - ', 1)[0]
            
            # Date handling
            published = entry.get('published_parsed', entry.get('updated_parsed'))
            if published:
                pub_date = datetime.datetime.fromtimestamp(time.mktime(published)).date()
            else:
                pub_date = datetime.date.today()

            score = scorer.score(title, summary)
            
            articles.append({
                'url': link,
                'title': title,
                'firm': source_row['name'],
                'published_date': pub_date,
                'summary': summary,
                'impact_score': score,
                'region': source_row['region']
            })
            
        return articles
    except Exception as e:
        print(f"Error fetching {source_row['name']}: {e}")
        return []

def run_aggregator():
    init_db()
    
    if not os.path.exists(SOURCES_PATH):
        print(f"Source file {SOURCES_PATH} not found.")
        return

    sources_df = pd.read_csv(SOURCES_PATH)
    scorer = ImpactScorer()
    
    all_articles = []
    for _, row in sources_df.iterrows():
        all_articles.extend(fetch_feed(row, scorer))
        
    # Save to DB
    conn = sqlite3.connect(DB_PATH)
    count = 0
    for a in all_articles:
        try:
            conn.execute('''
                INSERT OR IGNORE INTO articles (url, title, firm, published_date, summary, impact_score, region)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (a['url'], a['title'], a['firm'], a['published_date'], a['summary'], a['impact_score'], a['region']))
            count += 1
        except sqlite3.Error as e:
            pass
            
    conn.commit()
    conn.close()
    print(f"Completed. Processed {len(all_articles)} items. Saved {count} to DB.")

if __name__ == "__main__":
    run_aggregator()
