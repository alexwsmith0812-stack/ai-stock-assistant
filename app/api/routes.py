from fastapi import APIRouter, HTTPException

from app.models.schemas import AskRequest, AskResponse
from app.services.ai_service import get_ai_response

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask_question(payload: AskRequest) -> AskResponse:
    try:
        answer = await get_ai_response(payload.question)
        return AskResponse(answer=answer)
    except HTTPException:
        raise
    except RuntimeError as exc:
        return AskResponse(answer=str(exc))
    except Exception:
        return AskResponse(
            answer="Sorry — something went wrong on the server while answering that."
        )

