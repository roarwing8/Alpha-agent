# Project Alpha — Crypto Trading AI Agent

> Institutional-grade crypto trading intelligence. Powered by OpenAI, OpenRouter, or Ollama.
> **For educational purposes only. Not financial advice.**

---

## Features

- **5-Step Analysis Hierarchy** enforced via system prompt (Macro → MTF → Smart Money → Trade Construction → Risk)
- **Multi-provider support**: OpenAI, OpenRouter (100+ models), Ollama (local/offline)
- **Session memory** — persistent conversation history per session
- **Binance Futures auto-trading** — place orders and check positions (optional)
- **Structured responses** — includes which analysis steps were addressed
- **FastAPI** with auto-generated docs at `/docs`

---

## Setup

### 1. Clone & install

```bash
git clone https://gitlab.com/black-group6513024/black-project.git
cd black-project
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your chosen provider and API key
```

### 3. Run

```bash
python main.py
# or
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

## Provider Configuration

### OpenAI
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
```

### OpenRouter (access 100+ models)
```env
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-4o          # or anthropic/claude-3.5-sonnet, mistralai/mixtral-8x7b-instruct
OPENROUTER_API_KEY=sk-or-...
```
Get your key at https://openrouter.ai

### Ollama (local, no API key needed)
```bash
# Install Ollama: https://ollama.com
ollama pull llama3
```
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434/v1
```

### Binance Trading (optional)
```env
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
```

---

## API Reference

### `GET /health`
Returns agent status and active provider.

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "operational",
  "agent": "Project AlphaQ",
  "version": "1.0.0",
  "provider": "openai",
  "model": "gpt-4o"
}
```

---

### `POST /chat`
Send a market query to AlphaQ.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze BTC current market structure and give me a trade setup",
    "session_id": "my-session-001"
  }'
```

**With context:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Is this a good long entry?",
    "session_id": "my-session-001",
    "context": "BTC at 67,500. Daily closed above 200MA. Funding rate: +0.01%"
  }'
```

**Response:**
```json
{
  "session_id": "my-session-001",
  "response": "## 1. Macro Context\n...",
  "analysis_steps": [
    "1. Macro Context",
    "2. Multi-Timeframe Analysis",
    "3. Smart Money & On-Chain",
    "4. Trade Construction",
    "5. Risk Management"
  ],
  "timestamp": "2025-01-01T12:00:00+00:00",
  "provider": "openai/gpt-4o"
}
```

---

### `DELETE /session/{session_id}`
Clear conversation history for a session.

```bash
curl -X DELETE http://localhost:8000/session/my-session-001
```

### `GET /sessions`
List all active sessions.

```bash
curl http://localhost:8000/sessions
```

---

### `POST /trade` (requires Binance API keys)
Place a futures order on Binance.

```bash
curl -X POST http://localhost:8000/trade \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "BUY",
    "order_type": "MARKET",
    "quantity": 0.001
  }'
```

### `GET /positions` (requires Binance API keys)
Get open futures positions.

```bash
curl http://localhost:8000/positions
```

---

## Example Queries

- `"Analyze BTC market structure on the daily and 4H"`
- `"ETH funding rates are extremely negative. What does this signal?"`
- `"Give me a BTC long setup with entry, SL, and 3 TPs"`
- `"Evaluate this strategy: buy when RSI < 30, sell when RSI > 70 on 4H"`
- `"What are the key liquidation levels for BTC right now?"`
- `"How does DXY strength affect crypto in the current macro environment?"`

---

## Architecture

```
main.py                  # FastAPI app entry point
crypto_agent/
  __init__.py
  agent.py               # AlphaQ agent, system prompt, provider factory
  models.py              # Pydantic request/response models
  routes.py              # API route handlers (including /trade, /positions)
  trading.py             # Binance futures trading integration
requirements.txt
.env.example
```

---

## Disclaimer

This project is for **educational and research purposes only**.
It does **not** constitute financial advice, investment advice, or trading recommendations.
Always conduct your own research. Never risk more than you can afford to lose.
