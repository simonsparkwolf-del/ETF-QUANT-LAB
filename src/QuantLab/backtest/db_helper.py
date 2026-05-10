import sqlite3
from pathlib import Path
import pandas as pd
class dblite:
    def __init__(self, db_path: Path):
        self.conn = self._connect(db_path)
    
    def _connect(self, db_path: Path):
        if not db_path.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")
        return sqlite3.connect(str(db_path))
    
    def load_table(self) -> pd.DataFrame:
        query = """
        SELECT date,a.ticker,close,volume,b.category FROM weekly_bar a LEFT JOIN asset b
        ON a.ticker = b.ticker 
        WHERE b.category = 'ETF'
        """
        bars = pd.read_sql_query(query,self.conn)

        query = """
        SELECT * FROM weekly_alpha a
            WHERE alpha_id IN (SELECT alpha_id FROM alpha WHERE applicable = 'A')
        """
        alpha = pd.read_sql_query(query,self.conn)
        alpha = alpha.pivot_table(index=['date', 'ticker'], 
            columns='alpha_id',  
            values='value' )
        alpha.columns = [f'alpha_{c}' for c in alpha.columns]
        alpha = alpha.reset_index()

        data = bars.merge(alpha,how="left",on=["date","ticker"])
        data["date"] = pd.to_datetime(data["date"]).dt.date
        return data

if __name__ == "__main__":
    db_path = Path(r"E:\CUHK\trimester3\practicum\LAB\simon_test\ML001_data\datapool.db")
    db_helper = dblite(db_path)
    data = db_helper.load_table()
    data.to_csv(r"E:\CUHK\trimester3\practicum\LAB\simon_test\backtest\debug\data.csv",index=False)
