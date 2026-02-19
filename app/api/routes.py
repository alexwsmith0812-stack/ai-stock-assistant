from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.schemas import AskRequest
from app.services.ai_service import get_ai_response

router = APIRouter()


async def _stream_ask_chunks(question: str):
    """Yield SSE-style text chunks (data: <chunk>\n\n) for the frontend."""
    def to_sse(s: str) -> str:
        # SSE: newlines in payload become separate data lines so newlines are preserved
        s = s.replace("\r", "").replace("\0", "")
        return "\n".join(f"data: {line}" for line in s.split("\n")) + "\n\n"

    try:
        async for chunk in get_ai_response(question):
            yield to_sse(chunk)
    except RuntimeError as exc:
        yield to_sse(str(exc))
    except Exception:
        yield to_sse("Sorry — something went wrong on the server while answering that.")


@router.post("/ask")
async def ask_question(payload: AskRequest) -> StreamingResponse:
    return StreamingResponse(
        _stream_ask_chunks(payload.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

