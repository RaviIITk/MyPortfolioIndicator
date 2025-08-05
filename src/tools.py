


from typing import Dict, List, Optional
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
from newsapi import NewsApiClient
import requests
from datetime import timedelta

class StockPrice(BaseModel):
    symbol: str
    current_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: int
    price_change: float
    price_change_percent: float
    last_updated: datetime

class PortfolioMetrics(BaseModel):
    total_value: float
    daily_return: float
    ytd_return: float
    alpha: float
    beta: float
    sharpe_ratio: float
    tracking_error: float

class HoldingInfo(BaseModel):
    symbol: str
    quantity: float
    market_value: float
    weight: float
    cost_basis: float
    gain_loss: float
    gain_loss_percent: float

class NewsItem(BaseModel):
    title: str
    source: str
    url: str
    published_at: datetime
    sentiment_score: float

class MarketData(BaseModel):
    symbol: str
    sector: str
    industry: str
    market_cap: float
    pe_ratio: Optional[float]
    dividend_yield: Optional[float]

class tools:
    def __init__(self):
        # Initialize API clients
        import os
        api_key = os.getenv('NEWS_API_KEY')
        if not api_key:
            raise ValueError("NEWS_API_KEY environment variable not set.")
        self.newsapi = NewsApiClient(api_key=api_key)
        
    # Analyst Agent Tools
    def get_stock_price(self, symbol: str) -> StockPrice:
        """
        Get current and historical stock price data using yfinance
        """
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            hist = stock.history(period='1d')
            
            return StockPrice(
                symbol=symbol,
                current_price=info['regularMarketPrice'],
                open_price=hist['Open'][-1],
                high_price=hist['High'][-1],
                low_price=hist['Low'][-1],
                volume=info['volume'],
                price_change=info['regularMarketPrice'] - hist['Open'][-1],
                price_change_percent=((info['regularMarketPrice'] - hist['Open'][-1]) / hist['Open'][-1]) * 100,
                last_updated=datetime.now()
            )
        except Exception as e:
            raise Exception(f"Error fetching stock price for {symbol}: {str(e)}")

    def analyze_portfolio_performance(self, portfolio: Dict[str, float]) -> PortfolioMetrics:
        """
        Calculate comprehensive portfolio performance metrics
        """
        try:
            # Get market data for calculation
            sp500 = yf.Ticker('^GSPC')
            risk_free_rate = 0.03  # Assuming 3% risk-free rate
            
            portfolio_daily_returns = []
            portfolio_values = []
            
            for symbol, quantity in portfolio.items():
                stock = yf.Ticker(symbol)
                hist = stock.history(period='1y')
                portfolio_values.append(hist['Close'][-1] * quantity)
                portfolio_daily_returns.append(hist['Close'].pct_change() * quantity)
            
            portfolio_return = pd.concat(portfolio_daily_returns, axis=1).sum(axis=1)
            market_return = sp500.history(period='1y')['Close'].pct_change()
            
            return PortfolioMetrics(
                total_value=sum(portfolio_values),
                daily_return=portfolio_return[-1],
                ytd_return=portfolio_return.mean() * 252,  # Annualized return
                alpha=self._calculate_alpha(portfolio_return, market_return, risk_free_rate),
                beta=self._calculate_beta(portfolio_return, market_return),
                sharpe_ratio=self._calculate_sharpe_ratio(portfolio_return, risk_free_rate),
                tracking_error=self._calculate_tracking_error(portfolio_return, market_return)
            )
        except Exception as e:
            raise Exception(f"Error analyzing portfolio performance: {str(e)}")

    # Trader Agent Tools
    def get_holdings_info(self, portfolio: Dict[str, float]) -> List[HoldingInfo]:
        """
        Get detailed information about current portfolio holdings
        """
        holdings = []
        total_value = 0
        
        try:
            for symbol, quantity in portfolio.items():
                stock = yf.Ticker(symbol)
                current_price = stock.info['regularMarketPrice']
                market_value = current_price * quantity
                total_value += market_value
                
                holdings.append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'market_value': market_value,
                    'current_price': current_price,
                    'cost_basis': stock.info['regularMarketPreviousClose'] * quantity
                })
            
            # Calculate weights and create HoldingInfo objects
            return [
                HoldingInfo(
                    symbol=h['symbol'],
                    quantity=h['quantity'],
                    market_value=h['market_value'],
                    weight=h['market_value'] / total_value,
                    cost_basis=h['cost_basis'],
                    gain_loss=h['market_value'] - h['cost_basis'],
                    gain_loss_percent=((h['market_value'] - h['cost_basis']) / h['cost_basis']) * 100
                )
                for h in holdings
            ]
        except Exception as e:
            raise Exception(f"Error getting holdings info: {str(e)}")

    # Research Agent Tools
    def get_market_news(self, symbol: str) -> List[NewsItem]:
        """
        Get recent news articles and sentiment for a stock
        """
        try:
            news = self.newsapi.get_everything(
                q=symbol,
                language='en',
                sort_by='publishedAt',
                from_param=(datetime.now() - timedelta(days=7)).date().isoformat()
            )
            
            return [
                NewsItem(
                    title=article['title'],
                    source=article['source']['name'],
                    url=article['url'],
                    published_at=datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
                    sentiment_score=self._analyze_text_sentiment(article['title'])
                )
                for article in news['articles'][:5]  # Get top 5 recent news
            ]
        except Exception as e:
            raise Exception(f"Error fetching news for {symbol}: {str(e)}")

    def get_market_data(self, symbol: str) -> MarketData:
        """
        Get detailed market data for a stock
        """
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            return MarketData(
                symbol=symbol,
                sector=info.get('sector', ''),
                industry=info.get('industry', ''),
                market_cap=info.get('marketCap', 0),
                pe_ratio=info.get('forwardPE'),
                dividend_yield=info.get('dividendYield')
            )
        except Exception as e:
            raise Exception(f"Error fetching market data for {symbol}: {str(e)}")

    # Risk Manager Tools
    def calculate_portfolio_risk(self, portfolio: Dict[str, float]) -> Dict:
        """
        Calculate comprehensive risk metrics for the portfolio
        """
        try:
            # Get historical data for all symbols
            historical_data = {}
            for symbol in portfolio:
                stock = yf.Ticker(symbol)
                historical_data[symbol] = stock.history(period='1y')['Close']
            
            # Calculate returns
            returns_df = pd.DataFrame(historical_data)
            
            # Calculate portfolio volatility
            weights = np.array([portfolio[symbol] for symbol in portfolio])
            weights = weights / weights.sum()
            cov_matrix = returns_df.pct_change().cov()
            portfolio_vol = np.sqrt(weights.T @ cov_matrix @ weights) * np.sqrt(252)
            
            # Calculate VaR
            portfolio_returns = (returns_df * weights).sum(axis=1).pct_change()
            var_95 = portfolio_returns.quantile(0.05)
            
            # Maximum drawdown
            cumulative_returns = (1 + portfolio_returns).cumprod()
            rolling_max = cumulative_returns.expanding(min_periods=1).max()
            drawdowns = cumulative_returns / rolling_max - 1
            max_drawdown = drawdowns.min()
            
            return {
                'volatility': portfolio_vol,
                'var_95': var_95,
                'max_drawdown': max_drawdown,
                'diversification_score': self._calculate_diversification_score(returns_df),
                'beta': self._calculate_portfolio_beta(returns_df, weights),
                'sharpe_ratio': self._calculate_portfolio_sharpe(returns_df, weights)
            }
        except Exception as e:
            raise Exception(f"Error calculating portfolio risk: {str(e)}")

    # Helper methods
    def _calculate_alpha(self, portfolio_returns, market_returns, risk_free_rate):
        beta = self._calculate_beta(portfolio_returns, market_returns)
        return portfolio_returns.mean() - (risk_free_rate + beta * (market_returns.mean() - risk_free_rate))

    def _calculate_beta(self, portfolio_returns, market_returns):
        return portfolio_returns.cov(market_returns) / market_returns.var()

    def _calculate_sharpe_ratio(self, returns, risk_free_rate):
        excess_returns = returns - risk_free_rate/252
        return np.sqrt(252) * excess_returns.mean() / returns.std()

    def _calculate_tracking_error(self, portfolio_returns, market_returns):
        return (portfolio_returns - market_returns).std() * np.sqrt(252)

    def _analyze_text_sentiment(self, text: str) -> float:
        # Implement sentiment analysis here (using a service like TextBlob or NLTK)
        # Returns a score between -1 and 1
        return 0.0  # Placeholder

    def _calculate_diversification_score(self, returns_df):
        corr_matrix = returns_df.corr()
        return 1 - corr_matrix.mean().mean()  # Higher score means better diversification

    def _calculate_portfolio_beta(self, returns_df, weights):
        market = yf.Ticker('^GSPC').history(period='1y')['Close'].pct_change()
        portfolio_returns = (returns_df.pct_change() * weights).sum(axis=1)
        return portfolio_returns.cov(market) / market.var()

    def _calculate_portfolio_sharpe(self, returns_df, weights):
        risk_free_rate = 0.03  # Assuming 3% risk-free rate
        portfolio_returns = (returns_df.pct_change() * weights).sum(axis=1)
        return self._calculate_sharpe_ratio(portfolio_returns, risk_free_rate)