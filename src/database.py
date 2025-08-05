import sqlite3
import os
import pandas as pd

class database:
    def __init__(self, db_path='./databse'):
        self.db_path = db_path
        self.db_name = 'databse.db'
        self.conn = sqlite3.connect(os.path.join(self.db_path, self.db_name))

    def run_query(self, query):
        return pd.read_sql_query(query, self.conn)