import feedparser
import pandas as pd
import datetime
import time
import re

# --- CONFIGURATION (The Signal Cleaning Kit) ---
BLACKLISTED_DOMAINS = [
    "account.microsoft.com", "login.", "dictionary.", "cambridge.org", 
    "merriam-webster.com", "wikipedia.org", "thefreedictionary.com", 
    "collinsdictionary.com", "britannica.com", "wiktionary.org",
    "microsoft.com/en-us/account"
]

TOPIC_MAP = {
    "AI & Tech": ["ai", "generative ai", "llm", "automation", "digital", "technology", "quantum", "software", "data", "robotics"],
    "Macro & Economy": ["gdp", "inflation", "interest rates", "macro", "economy", "growth", "recession", "markets", "fiscal"],
    "ESG & Sustainability": ["esg", "climate", "carbon", "net zero", "sustainability", "energy", "green", "renewables", "decarbonization"],
    "Healthcare": ["biopharma", "clinical", "health", "patient", "medical", "biotech", "pharmaceutical", "life sciences"],
    "Strategy & Ops": ["transformation", "supply chain", "operations", "strategic", "leadership", "ma", "merger", "procurement"],
    "Geopolitics & Policy": ["global", "trade", "policy", "government", "regulation", "international", "sanctions", "compliance"]
}

class ImpactScorer:
    def __init__(self):
        self.weights = {
            "outlook": 25, "forecast": 25, "2026": 30, "2025": 20,
            "global": 15, "strategic": 20, "report": 20, "white paper": 30,
            "perspective": 10, "transformation": 15, "executive": 15
        }
        # Stronger noise detection - especially for dictionary/login patterns
        self.noise = [
            "career", "hiring", "webinar", "register", "podcast", "account", 
            "sign in", "login", "meaning", "definition", "synonym", "pronunciation"
        ]
        
    def score(self, title, summary):
        score = 40 # Base Score
        text = (title + " " + summary).lower()
        
        for word, weight in self.weights.items():
            if word in text:
                score += weight
        
        for word in self.noise:
            if word in text:
                score -= 60 # Aggressive penalty for noise
                
        return max(0, min(100, score))

def classify_topic(title, summary):
    text = (title + " " + summary).lower()
    for topic, keywords in TOPIC_MAP.items():
        if any(kw in text for kw in keywords):
            return topic
    return "Others"

def get_rss_url(strategy, query):
    if strategy == "google_news":
        return f"https://news.google.com/rss/search?q={query}+when:30d&hl=en-US&gl=US&ceid=US:en"
    elif strategy == "bing" or strategy == "bing_rss":
        return f"https://www.bing.com/search?q={query}&format=rss"
    return query

def fetch_and_rank(sources_df):
    scorer = ImpactScorer()
    all_results = []
    
    for _, row in sources_df.iterrows():
        url = get_rss_url(row['strategy'], row['query'])
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                link = entry.get('link', '')
                
                # NOISE FILTER 1: Domain Blacklist
                if any(domain in link.lower() for domain in BLACKLISTED_DOMAINS):
                    continue
                
                title = entry.get('title', 'No Title').rsplit(' - ', 1)[0]
                summary = entry.get('summary', '').replace('<b>', '').replace('</b>', '').strip()
                
                # NOISE FILTER 2: Keyword-based Score Check
                impact = scorer.score(title, summary)
                if impact < 20: # Drop high-probability noise early
                    continue
                
                published = entry.get('published_parsed')
                pub_date = datetime.datetime.fromtimestamp(time.mktime(published)).date() if published else datetime.date.today()
                
                topic = classify_topic(title, summary)
                
                all_results.append({
                    "Firm": row['name'],
                    "Region": row['region'],
                    "Topic": topic,
                    "Headline": title,
                    "Impact": impact,
                    "Date": pub_date,
                    "Link": link
                })
        except Exception:
            continue
            
    df = pd.DataFrame(all_results)
    if not df.empty:
        # Final Signal-to-Noise: Drop duplicates and sort
        df = df.sort_values(by=["Impact", "Date"], ascending=False)
        df = df.drop_duplicates(subset=["Link"])
    return df
