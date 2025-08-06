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




class tools:
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.database_flag = os.makedirs('./database', exist_ok=True)
        if self.database_flag:
            self.db = databases(db_path='./database')
        else:
            print('Add databse to the application')

        self.date= (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    def execute_news_api(self,keyword, date,):
        url = f"https://newsapi.org/v2/everything?q={keyword}&from={date}&sortBy=publishedAt&apiKey={api_key}"
        print(url)

        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def load_news_to_databse(self, json):
        self.db.insert_news_articles_batch(json['articles'])
    


