import json
import logging
import os

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.chat_flow import (
    generate_chat_response,
    handle_chat_command,
    resolve_biography,
)
from app.profiles import fill_persona_profiles_in_background, get_cached_persona_profiles

from app.rate_limits import check_if_ip_limited, add_or_remove_user_requestlist, check_if_user_ongoing_request

router = APIRouter()
log = logging.getLogger(__name__)


class ChatMessageRequest(BaseModel):
    message: str
    persona_details: dict
    persona_country: str
    chat_history: list


@router.get("/chat/personas")
def list_chat_personas(background_tasks: BackgroundTasks, country: str = "netherlands", limit: int = 30):
    """Return the persisted chat-only persona profile set."""
    try:
        bounded_limit = max(1, min(limit, 30))
        personas = get_cached_persona_profiles(country=country, limit=bounded_limit)
        is_complete = len(personas) >= bounded_limit

        if not is_complete:
            background_tasks.add_task(
                fill_persona_profiles_in_background,
                country=country,
                limit=bounded_limit,
            )

        return {
            "personas": personas,
            "is_complete": is_complete,
            "target_count": bounded_limit,
        }
    except Exception as exc:
        log.exception("Error resolving chat personas")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/chat/chat_message")
async def stream_chat_message(request: Request, request_body: ChatMessageRequest):

    """Stream one guardrailed persona response back to the frontend."""

    def single_message_stream(text: str, event: str = "error"):
        yield f"event: {event}\ndata: {json.dumps({'text': text})}\n\n"
        yield "data: [DONE]\n\n"

    def stream_generator():
        try:
            for chunk in generate_chat_response(
                persona_biography=biography,
                user_message=request_body.message,
                chat_history=request_body.chat_history,
                persona_details=persona_details,
                persona_country=persona_country,
                client_id=ip,
            ):
                yield f"event: message\ndata: {json.dumps({'text': chunk})}\n\n"
        except Exception as e:
            log.exception("Error generating persona chat response")
            message = "Sorry, there was an error generating the response. Please try again."
            if os.getenv("ENV") == "development":
                message = f"{message} Backend error: {type(e).__name__}: {e}"
            yield f"event: error\ndata: {json.dumps({'text': message})}\n\n"
        finally:
            add_or_remove_user_requestlist('remove', ip)
        yield "data: [DONE]\n\n"

    if os.getenv('ENV') == 'development':
        ip = "dev-ip"
    else:
        forwarded_for = request.headers.get("x-forwarded-for")
        ip = forwarded_for.split(",")[0] if forwarded_for else request.client.host


    user_has_ongoing_request = check_if_user_ongoing_request(ip)

    if user_has_ongoing_request:
        return StreamingResponse(
            single_message_stream("Message request already ongoing."),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no"}
        )
    
    user_ip_is_limited = check_if_ip_limited(ip)

    if user_ip_is_limited == True:
        return StreamingResponse(
            single_message_stream("Sorry, you have reached your limit for messages today."),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no"}
        )
    
    add_or_remove_user_requestlist('add', ip)

    persona_details = request_body.persona_details
    persona_country = request_body.persona_country
    try:
        biography = resolve_biography(
            persona_details=persona_details,
            persona_country=persona_country,
        )
    except Exception as e:
        log.exception("Error generating persona biography")
        add_or_remove_user_requestlist('remove', ip)
        message = "Sorry, there was an error generating the persona biography. Please try again."
        if os.getenv("ENV") == "development":
            message = f"{message} Backend error: {type(e).__name__}: {e}"
        return StreamingResponse(
            single_message_stream(message),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no"}
        )

    command_response = handle_chat_command(
        message=request_body.message,
        biography=biography,
    )
    if command_response is not None:
        add_or_remove_user_requestlist('remove', ip)
        return StreamingResponse(
            single_message_stream(command_response, event="system"),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no"}
        )

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"}
    )
