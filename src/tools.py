from typing import Dict, List, Optional
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
from newsapi import NewsApiClient
import requests
from datetime import timedelta
from dotenv import load_dotenv
import os

from src.database import databases



load_dotenv()




class tools(databases):
    def __init__(self):
        # Call parent class constructor with db_path
        db_path = './database'
        if not os.path.exists(db_path):
            os.makedirs(db_path, exist_ok=True)
        
        # Initialize parent class (databases)
        super().__init__(db_path=db_path)
        
        # Initialize tools-specific attributes
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    def execute_news_api(self,keyword):
        url = f"https://newsapi.org/v2/everything?q={keyword}&from={self.date}&sortBy=publishedAt&apiKey={api_key}"
        print(url)

        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def load_news_to_databse(self, json):
        self.insert_news_articles_batch(json['articles'])
    


