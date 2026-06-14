import uuid
from fastapi import APIRouter, HTTPException
from .agent import agent
from .models import ChatRequest, ChatResponse, HealthResponse, TradeRequest, TradeResponse
from .trading import place_order, get_positions

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    return HealthResponse(
        status="operational",
        agent="Project AlphaQ",
        version="1.0.0",
        provider=agent.provider,
        model=agent.model,
    )


@router.get("/status", response_model=HealthResponse, tags=["System"])
async def status_check():
    return await health_check()


@router.post("/chat", response_model=ChatResponse, tags=["Agent"])
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    try:
        result = await agent.chat(
            session_id=session_id,
            user_message=request.message,
            context=request.context,
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.post("/trade", response_model=TradeResponse, tags=["Trading"])
async def execute_trade(request: TradeRequest):
    try:
        result = await place_order(
            symbol=request.symbol.upper(),
            side=request.side.upper(),
            order_type=request.order_type.upper(),
            quantity=request.quantity,
            price=request.price,
        )
        return TradeResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trade error: {str(e)}")


@router.get("/positions", tags=["Trading"])
async def positions():
    try:
        positions = await get_positions()
        return {"positions": positions}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Positions error: {str(e)}")


@router.delete("/session/{session_id}", tags=["Session"])
async def clear_session(session_id: str):
    cleared = agent.clear_session(session_id)
    if not cleared:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": f"Session {session_id} cleared"}


@router.get("/sessions", tags=["Session"])
async def list_sessions():
    return {
        "active_sessions": list(agent.sessions.keys()),
        "count": len(agent.sessions),
    }
