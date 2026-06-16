import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from src.config.config import (
    TRACE_ID_HEADER_NAME,
    USER_ID_HEADER_NAME,
    get_request_logger,
    MAX_BODY_LOG_LENGTH,
    ctx_trace_id,
    ctx_user_id,
    ctx_tokens_used  # ◄── Imported
)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get(TRACE_ID_HEADER_NAME, str(uuid.uuid4()))
        user_id = request.headers.get(USER_ID_HEADER_NAME, None)

        # Set core context states
        t_token = ctx_trace_id.set(trace_id)
        u_token = ctx_user_id.set(user_id)
        tok_token = ctx_tokens_used.set(0)  # ◄── Initialize token context tracking at zero

        start_time = time.time()
        try:
            logger = get_request_logger()
            request.state.trace_id = trace_id

            body_bytes = await request.body()
            body_str = body_bytes.decode("utf-8", errors="replace")
            if len(body_str) > MAX_BODY_LOG_LENGTH:
                body_str = body_str[:MAX_BODY_LOG_LENGTH] + "...(truncated)"

            logger.info(
                f"Incoming request: {request.method} {request.url.path} "
                f"query={dict(request.query_params)} "
                f"user={user_id} "
                f"client={request.client.host if request.client else 'unknown'} "
                f"user-agent={request.headers.get('user-agent')} "
                f"body_length={len(body_str)}"
            )

            response = await call_next(request)

            # Extract final calculated metrics registered inside task context lifecycle
            final_tokens_processed = ctx_tokens_used.get()

            duration = (time.time() - start_time) * 1000
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"status_code={response.status_code} "
                f"duration={duration:.2f}ms "
                f"tokens_consumed={final_tokens_processed}"  # ◄── Appended metrics to tracking log
            )
            response.headers[TRACE_ID_HEADER_NAME] = trace_id

            return response
        except Exception as e:
            get_request_logger().exception(f"Unhandled error within request execution flow: {e}")
            raise
        finally:
            # Clean context variables cleanly to prevent memory leaks across thread scopes
            ctx_trace_id.reset(t_token)
            ctx_user_id.reset(u_token)
            ctx_tokens_used.reset(tok_token)  # ◄── Reset token variable context