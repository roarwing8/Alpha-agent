import os
import uuid
from datetime import datetime, timezone
from typing import Optional
from openai import AsyncOpenAI

# ---------------------------------------------------------------------------
# AlphaQ System Prompt
# ---------------------------------------------------------------------------
ALPHAQ_SYSTEM_PROMPT = """
You are Project AlphaQ — an institutional-grade crypto trading intelligence agent.

IDENTITY
--------
You are an expert in BTC, ETH, and altcoins, with deep knowledge of:
- Market structure, liquidity dynamics, and price action
- On-chain data interpretation (netflows, whale activity, exchange reserves)
- Funding rates, open interest, liquidation heatmaps
- Macro factors: Fed policy, DXY, equities correlation, ETF flows, halving cycles, stablecoin supply
- Risk management and institutional position sizing

ANALYSIS HIERARCHY — ALWAYS FOLLOW IN ORDER
--------------------------------------------
For every market query, you MUST address each step in sequence:

1. MACRO CONTEXT
   Assess: Fed stance, DXY trend, equities (SPX/NDX), BTC ETF flows, halving cycle phase,
   stablecoin supply growth/contraction, exchange reserve trends.

2. MULTI-TIMEFRAME ANALYSIS (MTF)
   Start from Monthly → Weekly → Daily → 4H → 1H → 15M → 5M.
   Never analyze a lower timeframe without establishing higher timeframe context first.
   Identify key S/R levels, trend direction, and momentum on each relevant TF.

3. SMART MONEY & ON-CHAIN ANALYSIS
   Identify: liquidity sweeps, order blocks (OB), fair value gaps (FVG), change of character (CHoCH),
   break of structure (BOS), whale accumulation/distribution, liquidation heatmap clusters,
   funding rate extremes, OI divergence.

4. TRADE CONSTRUCTION
   Define precisely:
   - Entry zone (limit or market, with rationale)
   - Stop Loss (SL) with invalidation logic
   - Take Profit levels: TP1 (partial, ~1.5R), TP2 (~2.5R), TP3 (runner, 4R+)
   - Risk:Reward ratio
   - Probability estimate (%) with reasoning
   - Trade narrative (why this setup has edge)
   - Invalidation conditions

5. RISK MANAGEMENT
   Specify:
   - Suggested position size (% of portfolio, e.g. 1-2% risk per trade)
   - Funding rate impact if holding futures overnight
   - Slippage considerations for entry/exit
   - Explicit warning: NO revenge trading, NO martingale, NO gambling behavior.

CRYPTO SPECIALIST RULES
------------------------
For BTC and ETH specifically, ALWAYS evaluate:
- Current funding rates (positive = crowded longs, negative = crowded shorts)
- Open Interest trend (rising OI + price = conviction; divergence = caution)
- Key liquidation levels above and below current price
- Exchange netflows (inflows = sell pressure, outflows = accumulation)
- CME gap locations and probability of fill
- DXY inverse correlation strength

STRATEGY EVALUATION MODE
-------------------------
When asked to evaluate a strategy:
- Calculate or estimate: win rate, average RR, max drawdown, expectancy
- Flag overfitting risks (curve-fitting to historical data)
- Identify recency bias or survivorship bias
- Suggest walk-forward testing or out-of-sample validation

COMMUNICATION STANDARDS
------------------------
- Precise, data-driven, and professional at all times
- No hype, no moon/doom predictions, no certainty claims
- Always state assumptions when data is incomplete
- Present multiple scenarios with probability weights when uncertain
- Clearly define what would invalidate each scenario
- Use structured formatting: headers, bullet points, tables where helpful

MISSION
-------
Identify high-probability asymmetric setups. Protect capital above all else.
Think like an institutional desk: process, discipline, and edge over emotion.

DISCLAIMER (include when giving trade ideas)
--------------------------------------------
This analysis is for educational and informational purposes only.
It does not constitute financial advice. Always do your own research.
Past performance does not guarantee future results.
""".strip()

# ---------------------------------------------------------------------------
# Step detection keywords
# ---------------------------------------------------------------------------
STEP_KEYWORDS = {
    "1. Macro Context": ["fed", "dxy", "etf", "halving", "stablecoin", "exchange reserve", "equities", "spx", "ndx", "macro"],
    "2. Multi-Timeframe Analysis": ["monthly", "weekly", "daily", "4h", "1h", "15m", "5m", "timeframe", "mtf", "higher tf", "lower tf"],
    "3. Smart Money & On-Chain": ["order block", "fvg", "fair value gap", "choch", "bos", "liquidity sweep", "whale", "liquidation", "on-chain", "netflow", "funding rate", "open interest"],
    "4. Trade Construction": ["entry", "stop loss", "sl", "take profit", "tp1", "tp2", "tp3", "risk:reward", "r:r", "probability", "invalidation", "narrative"],
    "5. Risk Management": ["position size", "portfolio", "slippage", "funding decay", "revenge", "martingale", "risk per trade"],
}


def detect_analysis_steps(text: str) -> list[str]:
    """Detect which of the 5 hierarchy steps appear in the response."""
    text_lower = text.lower()
    found = []
    for step, keywords in STEP_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(step)
    return found


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------
def build_client(provider: str, api_key: Optional[str], base_url: Optional[str]) -> AsyncOpenAI:
    """
    Build an AsyncOpenAI-compatible client for:
      - openai    : OpenAI API
      - openrouter: OpenRouter (openai-compatible)
      - ollama    : Local Ollama (openai-compatible endpoint)
    """
    if provider == "openrouter":
        return AsyncOpenAI(
            api_key=api_key or os.getenv("OPENROUTER_API_KEY", "no-key"),
            base_url=base_url or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        )
    elif provider == "ollama":
        return AsyncOpenAI(
            api_key="ollama",  # Ollama doesn't need a real key
            base_url=base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        )
    else:  # default: openai
        return AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
        )


# ---------------------------------------------------------------------------
# AlphaQ Agent
# ---------------------------------------------------------------------------
class AlphaQAgent:
    def __init__(self):
        self.sessions: dict[str, list[dict]] = {}
        self.provider: str = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model: str = os.getenv("LLM_MODEL", self._default_model())
        self.client: AsyncOpenAI = build_client(
            provider=self.provider,
            api_key=None,
            base_url=None,
        )

    def _default_model(self) -> str:
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        defaults = {
            "openai": "gpt-4o",
            "openrouter": "openai/gpt-4o",
            "ollama": "llama3",
        }
        return defaults.get(provider, "gpt-4o")

    def _get_or_create_session(self, session_id: str) -> list[dict]:
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]

    async def chat(self, session_id: str, user_message: str, context: Optional[str] = None) -> dict:
        history = self._get_or_create_session(session_id)

        # Prepend optional context to the user message
        full_message = user_message
        if context:
            full_message = f"[Context: {context}]\n\n{user_message}"

        history.append({"role": "user", "content": full_message})

        messages = [
            {"role": "system", "content": ALPHAQ_SYSTEM_PROMPT},
            *history,
        ]

        # Extra headers for OpenRouter (optional but recommended)
        extra_headers = {}
        if self.provider == "openrouter":
            extra_headers = {
                "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "https://github.com/alphaq-agent"),
                "X-Title": "Project AlphaQ",
            }

        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,  # Low temp for analytical precision
            extra_headers=extra_headers if extra_headers else None,
        )

        assistant_text = completion.choices[0].message.content
        history.append({"role": "assistant", "content": assistant_text})

        return {
            "session_id": session_id,
            "response": assistant_text,
            "analysis_steps": detect_analysis_steps(assistant_text),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": f"{self.provider}/{self.model}",
        }

    def clear_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


# Singleton instance
agent = AlphaQAgent()
