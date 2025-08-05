import autogen
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from tools import tools

class StockMetrics(BaseModel):
    symbol: str
    current_price: float
    volume: int
    price_change_percent: float
    last_updated: datetime

class MarketSentiment(BaseModel):
    symbol: str
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    news_summary: str
    sentiment_label: str = Field(description="Either 'Positive', 'Negative', or 'Neutral'")
    confidence: float = Field(ge=0.0, le=1.0)

class RiskMetrics(BaseModel):
    volatility: float
    beta: float
    sharpe_ratio: float
    var_95: float  # Value at Risk at 95% confidence
    max_drawdown: float
    diversification_score: float = Field(ge=0.0, le=1.0)

class PortfolioPerformance(BaseModel):
    total_value: float
    daily_return: float
    ytd_return: float
    holdings: List[StockMetrics]
    risk_metrics: RiskMetrics
    last_updated: datetime

class TradingSuggestion(BaseModel):
    symbol: str
    action: str = Field(description="Either 'BUY', 'SELL', or 'HOLD'")
    target_price: float
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)

class MarketAnalysis(BaseModel):
    symbols: List[str]
    market_conditions: List[MarketSentiment]
    sector_analysis: str
    market_trends: str
    timestamp: datetime = Field(default_factory=datetime.now)

class PortfolioAgents:
    def __init__(self):
        self.tools = tools()
        self.config_list = [
            {
                "model": "gpt-4",
                "api_key": "your-api-key-here"
            }
        ]

        # Initialize the specialized agents
        self.analyst_agent = autogen.AssistantAgent(
            name="PortfolioAnalyst",
            system_message="I am a portfolio analyst specialized in analyzing market trends, portfolio performance, and risk assessment.",
            llm_config={"config_list": self.config_list}
        )

        self.trader_agent = autogen.AssistantAgent(
            name="TraderAgent",
            system_message="I am a trading specialist focused on executing trades and monitoring market conditions.",
            llm_config={"config_list": self.config_list}
        )

        self.research_agent = autogen.AssistantAgent(
            name="ResearchAgent",
            system_message="I am a research specialist focused on gathering market news, company information, and sector analysis.",
            llm_config={"config_list": self.config_list}
        )

        self.risk_manager = autogen.AssistantAgent(
            name="RiskManager",
            system_message="I am a risk management specialist focused on portfolio risk assessment and mitigation strategies.",
            llm_config={"config_list": self.config_list}
        )

        # User proxy agent that orchestrates the interaction
        self.user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
            code_execution_config={"work_dir": "coding"},
            llm_config={"config_list": self.config_list}
        )

    async def analyze_portfolio(self, portfolio: Dict[str, float]) -> PortfolioPerformance:
        """
        Coordinate agents to perform comprehensive portfolio analysis
        Args:
            portfolio (Dict[str, float]): Dictionary of stock symbols and their quantities
        Returns:
            PortfolioPerformance: Comprehensive portfolio analysis results
        """
        performance_data = []
        
        # Get performance analysis
        performance_response = await self.user_proxy.initiate_chat(
            self.analyst_agent,
            message=f"Analyze the performance of this portfolio: {portfolio}"
        )
        
        # Get risk assessment
        risk_response = await self.user_proxy.initiate_chat(
            self.risk_manager,
            message="Assess the risk factors of the portfolio"
        )
        
        # Get market sentiment
        sentiment_response = await self.user_proxy.initiate_chat(
            self.research_agent,
            message="Gather recent market news and sentiment"
        )

        # Convert responses to Pydantic models
        holdings = [
            StockMetrics(
                symbol=symbol,
                **self.tools.get_stock_price(symbol)
            ) for symbol in portfolio.keys()
        ]

        risk_metrics = RiskMetrics(**risk_response)
        
        return PortfolioPerformance(
            total_value=sum(h.current_price * portfolio[h.symbol] for h in holdings),
            holdings=holdings,
            risk_metrics=risk_metrics,
            daily_return=performance_response.get("daily_return", 0.0),
            ytd_return=performance_response.get("ytd_return", 0.0),
            last_updated=datetime.now()
        )

    async def get_trading_suggestions(self, portfolio: Dict[str, float]) -> List[TradingSuggestion]:
        """
        Get trading suggestions based on current portfolio and market conditions
        Args:
            portfolio (Dict[str, float]): Dictionary of stock symbols and their quantities
        Returns:
            List[TradingSuggestion]: List of trading suggestions for portfolio optimization
        """
        response = await self.user_proxy.initiate_chat(
            self.trader_agent,
            message=f"Provide trading suggestions for portfolio optimization: {portfolio}"
        )
        
        return [TradingSuggestion(**suggestion) for suggestion in response]

    async def research_market_conditions(self, symbols: List[str]) -> MarketAnalysis:
        """
        Research specific market conditions and news for given symbols
        Args:
            symbols (List[str]): List of stock symbols to research
        Returns:
            MarketAnalysis: Detailed market analysis including sentiment and trends
        """
        response = await self.user_proxy.initiate_chat(
            self.research_agent,
            message=f"Research market conditions and news for these symbols: {symbols}"
        )
        
        market_conditions = [
            MarketSentiment(**self.tools.analyze_market_sentiment(symbol))
            for symbol in symbols
        ]
        
        return MarketAnalysis(
            symbols=symbols,
            market_conditions=market_conditions,
            sector_analysis=response.get("sector_analysis", ""),
            market_trends=response.get("market_trends", "")
        )

    async def assess_portfolio_risk(self, portfolio: Dict[str, float]) -> RiskMetrics:
        """
        Get detailed risk assessment of the portfolio
        Args:
            portfolio (Dict[str, float]): Dictionary of stock symbols and their quantities
        Returns:
            RiskMetrics: Detailed risk assessment metrics
        """
        response = await self.user_proxy.initiate_chat(
            self.risk_manager,
            message=f"Provide detailed risk assessment for portfolio: {portfolio}"
        )
        
        return RiskMetrics(**response)

    def terminate_agents(self):
        """
        Properly terminate all agent sessions
        """
        self.user_proxy.send({"content": "TERMINATE"})