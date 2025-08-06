import sqlite3
import os
import pandas as pd

class databases:
    def __init__(self, db_path='./databse'):
        self.db_path = db_path
        self.db_name = 'databse.db'
        self.conn = sqlite3.connect(os.path.join(self.db_path, self.db_name))

    def run_query(self, query):
        return pd.read_sql_query(query, self.conn)
    
    def populate_empty_db(self):
        """
        Create tables for storing news data from different sources with proper datetime tracking
        """
        cursor = self.conn.cursor()
        
        # Create news sources table with updated datetime fields
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_sources (
            source_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            reliability_score FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create news articles table with enhanced datetime tracking
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_articles (
            article_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            title VARCHAR(255) NOT NULL,
            content TEXT,
            url VARCHAR(500),
            published_at TIMESTAMP NOT NULL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sentiment_score FLOAT,
            symbols TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES news_sources(source_id)
        )
        """)

        # Create symbols mentioned table with datetime tracking
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS article_symbols (
            article_id INTEGER,
            symbol VARCHAR(20),
            mention_count INTEGER DEFAULT 1,
            first_mentioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_mentioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (article_id, symbol),
            FOREIGN KEY (article_id) REFERENCES news_articles(article_id)
        )
        """)

        # Create sentiment history table with enhanced datetime fields
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_history (
            sentiment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol VARCHAR(20),
            date DATE,
            analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sentiment_score FLOAT,
            article_count INTEGER,
            period_start TIMESTAMP,
            period_end TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Add indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_date ON news_articles(published_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_fetch ON news_articles(fetched_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_period ON sentiment_history(period_start, period_end)")
        
        self.conn.commit()

    def insert_news_source_df(self, df: pd.DataFrame):
        """
        Insert multiple news sources from a DataFrame
        
        DataFrame columns should include:
        - name (required)
        - description (optional)
        - reliability_score (optional)
        """
        cursor = self.conn.cursor()
        
        for _, row in df.iterrows():
            cursor.execute("""
            INSERT INTO news_sources (
                name,
                description,
                reliability_score
            ) VALUES (?, ?, ?)
            """, (
                row.get('name'),
                row.get('description'),
                row.get('reliability_score')
            ))
        
        self.conn.commit()

    def insert_news_articles_df(self, df: pd.DataFrame):
        """
        Insert multiple news articles from a DataFrame
        
        DataFrame columns should include:
        - source_id
        - title
        - content
        - url
        - published_at
        - sentiment_score
        - symbols (list or comma-separated string)
        """
        cursor = self.conn.cursor()
        
        for _, row in df.iterrows():
            # Handle symbols if they're in list format
            symbols = row['symbols']
            if isinstance(symbols, list):
                symbols = ','.join(symbols)
                
            # Insert article
            cursor.execute("""
            INSERT INTO news_articles (
                source_id,
                title,
                content,
                url,
                published_at,
                sentiment_score,
                symbols
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                row['source_id'],
                row['title'],
                row['content'],
                row['url'],
                row['published_at'],
                row['sentiment_score'],
                symbols
            ))
            
            article_id = cursor.lastrowid
            
            # Insert symbol mentions
            if isinstance(row['symbols'], list):
                symbols_list = row['symbols']
            else:
                symbols_list = row['symbols'].split(',')
                
            for symbol in symbols_list:
                cursor.execute("""
                INSERT INTO article_symbols (
                    article_id,
                    symbol,
                    mention_count
                ) VALUES (?, ?, 1)
                """, (article_id, symbol.strip()))
        
        self.conn.commit()