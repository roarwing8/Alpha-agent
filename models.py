from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message or market query")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    context: Optional[str] = Field(None, description="Optional extra context (e.g. current price, timeframe)")


class ChatResponse(BaseModel):
    session_id: str
    response: str
    analysis_steps: List[str] = Field(default_factory=list, description="Which of the 5 hierarchy steps were addressed")
    timestamp: str
    provider: str = Field(default="unknown", description="LLM provider used")


class HealthResponse(BaseModel):
    status: str
    agent: str
    version: str
    provider: str
    model: str


class TradeRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair (e.g. BTCUSDT, ETHUSDT)")
    side: str = Field(..., description="Order side: BUY or SELL")
    order_type: str = Field(default="MARKET", description="Order type: MARKET, LIMIT")
    quantity: Optional[float] = Field(None, description="Order quantity (optional for market orders)")
    price: Optional[float] = Field(None, description="Limit price (required for LIMIT orders)")


class TradeResponse(BaseModel):
    order_id: Optional[str] = None
    symbol: str
    side: str
    status: str
    message: str


class PositionResponse(BaseModel):
    symbol: str
    position_amt: float
    entry_price: float
    mark_price: float
    unrealized_profit: float
    liquidation_price: Optional[float] = None
