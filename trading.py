import os
from typing import Optional, List
from binance import AsyncClient
from binance.exceptions import BinanceAPIException


async def get_binance_client():
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        raise ValueError("Binance API credentials not configured")
    return await AsyncClient.create(api_key=api_key, api_secret=api_secret)


async def place_order(
    symbol: str,
    side: str,
    order_type: str = "MARKET",
    quantity: Optional[float] = None,
    price: Optional[float] = None,
) -> dict:
    client = await get_binance_client()
    try:
        if order_type == "MARKET":
            order = await client.futures_create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity,
            )
        elif order_type == "LIMIT":
            if not price or not quantity:
                raise ValueError("Price and quantity required for LIMIT orders")
            order = await client.futures_create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity,
                price=price,
                timeInForce="GTC",
            )
        else:
            raise ValueError(f"Unsupported order type: {order_type}")
        return {
            "order_id": order.get("orderId"),
            "symbol": symbol,
            "side": side,
            "status": order.get("status", "unknown"),
            "message": f"Order placed successfully: {order.get('status')}",
        }
    except BinanceAPIException as e:
        return {
            "order_id": None,
            "symbol": symbol,
            "side": side,
            "status": "error",
            "message": f"Binance error: {e.message}",
        }
    finally:
        await client.close_connection()


async def get_positions() -> List[dict]:
    client = await get_binance_client()
    try:
        positions = await client.futures_position_information()
        result = []
        for pos in positions:
            amt = float(pos.get("positionAmt", 0))
            if amt != 0:
                result.append({
                    "symbol": pos.get("symbol"),
                    "position_amt": amt,
                    "entry_price": float(pos.get("entryPrice", 0)),
                    "mark_price": float(pos.get("markPrice", 0)),
                    "unrealized_profit": float(pos.get("unRealizedProfit", 0)),
                    "liquidation_price": float(pos.get("liquidationPrice")) if pos.get("liquidationPrice") else None,
                })
        return result
    except BinanceAPIException as e:
        return [{"symbol": "error", "position_amt": 0, "entry_price": 0, "mark_price": 0, "unrealized_profit": 0, "liquidation_price": None, "error": e.message}]
    finally:
        await client.close_connection()