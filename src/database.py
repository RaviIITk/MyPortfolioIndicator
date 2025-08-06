import sqlite3
import os
import pandas as pd
from datetime import datetime

class databases:
    def __init__(self, db_path='./database'):
        self.db_path = db_path
        self.db_name = 'database.db'
        self.conn = sqlite3.connect(os.path.join(self.db_path, self.db_name))

    def run_query(self, query):
        return pd.read_sql_query(query, self.conn)
    
    def populate_empty_db(self):
        """
        Create a single table for storing news articles with all necessary fields
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_news (
            article_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT,
            source_name TEXT NOT NULL,
            author TEXT,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT,
            url_image TEXT,
            published_at TIMESTAMP NOT NULL,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Add index for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_date ON market_news(published_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_name ON market_news(source_name)")
        
        self.conn.commit()

    def insert_news_article(self, article_data: dict):
        """
        Insert a single news article from the API response format
        
        Args:
            article_data (dict): News article data in the API response format
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
        INSERT INTO market_news (
            source_id,
            source_name,
            author,
            title,
            description,
            url,
            url_image,
            published_at,
            content
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article_data['source'].get('id'),
            article_data['source'].get('name'),
            article_data.get('author'),
            article_data.get('title'),
            article_data.get('description'),
            article_data.get('url'),
            article_data.get('urlToImage'),
            article_data.get('publishedAt'),
            article_data.get('content')
        ))
        
        self.conn.commit()
        return cursor.lastrowid

    def insert_news_articles_batch(self, articles: list):
        """
        Insert multiple news articles in batch
        
        Args:
            articles (list): List of article dictionaries in the API response format
        """
        cursor = self.conn.cursor()
        
        values = [(
            article['source'].get('id'),
            article['source'].get('name'),
            article.get('author'),
            article.get('title'),
            article.get('description'),
            article.get('url'),
            article.get('urlToImage'),
            article.get('publishedAt'),
            article.get('content')
        ) for article in articles]
        
        cursor.executemany("""
        INSERT INTO market_news (
            source_id,
            source_name,
            author,
            title,
            description,
            url,
            url_image,
            published_at,
            content
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
        
        self.conn.commit()