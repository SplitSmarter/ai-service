import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from contextvars import ContextVar

# Explicitly pull configurations from secrets text file
load_dotenv("ai_service_secrets.txt")


class AppSettings:
    """Production configuration registry containing global application parameters."""

    def __init__(self):
        self.APP_NAME: str = os.getenv("APP_NAME", "ai-inference-service")
        self.APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")

        # Redis Core Connections
        self.REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

        # API Core Security Configuration Keys
        self.USER_ID_HEADER_NAME: str = "X-User-Id"
        self.TRACE_ID_HEADER_NAME: str = "X-Trace-Id"
        self.MAX_BODY_LOG_LENGTH: int = 500
        self.TRACE_ID_KEY: str = "trace_id"

        # Raw format template pattern string: "provider:identifier:value"
        self.AI_API_KEYS_RAW: str = os.getenv("AI_API_KEYS", "gemini:dev_agent:mock_secret_key")

    @property
    def parsed_ai_keys(self) -> list[dict[str, str]]:
        """
        Parses complex multi-provider API structural matrices.
        Returns: [{'provider': 'gemini', 'identifier': 'dev_agent', 'value': 'mock_key'}]
        """
        parsed_keys = []
        if not self.AI_API_KEYS_RAW:
            return parsed_keys

        for item in self.AI_API_KEYS_RAW.split(","):
            parts = item.strip().split(":", 2)
            if len(parts) == 3:
                parsed_keys.append({
                    "provider": parts[0].strip().lower(),
                    "identifier": parts[1].strip(),
                    "value": parts[2].strip()
                })
        return parsed_keys


# Instantiate global settings block for explicit component reference imports
settings = AppSettings()

USER_ID_HEADER_NAME = "X-User-Id"
TRACE_ID_HEADER_NAME = "X-Trace-Id"
TIME_ZONE_HEADER_NAME = "X-Time-Zone"
MAX_BODY_LOG_LENGTH = 500
MAX_OUTPUT_TOKENS = 1024

# ==== Thread-safe Request Context Trackers ====
ctx_trace_id: ContextVar[str] = ContextVar("trace_id", default="-")
ctx_user_id: ContextVar[str] = ContextVar("user_id", default=None)
ctx_tokens_used: ContextVar[dict] = ContextVar("tokens_used", default=None)


# ==== Logging Infrastructure Engine ====

class UTCFormatter(logging.Formatter):
    """Custom UTC formatter for consistent structural tracking timestamps."""
    converter = datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


LOG_FORMAT = "%(asctime)s - %(levelname)s - [%(trace_id)s] - %(name)s - %(module)s - %(message)s"
formatter = UTCFormatter(LOG_FORMAT)

# Standard Output Pipeline (Container/Docker Native Output)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

# Enforce target logs folder structural presence on initialization boot
LOG_FILE_PATH = "logs/user-service.log"
Path(LOG_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)

# Standard Local Output Log File Handling Pipeline
file_handler = logging.FileHandler(LOG_FILE_PATH)
file_handler.setFormatter(formatter)

# Build centralized application logger tracking instance
logger = logging.getLogger(settings.APP_NAME)
logger.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)
logger.propagate = False


class ContextLoggerAdapter(logging.LoggerAdapter):
    """Intercepts standard execution parameters to inject ongoing ContextVar fields."""

    def process(self, msg, kwargs):
        trace_id = ctx_trace_id.get()
        extra = kwargs.get("extra", {})
        kwargs["extra"] = {settings.TRACE_ID_KEY: trace_id, **self.extra, **extra}
        return msg, kwargs


def get_logger(**context) -> logging.LoggerAdapter:
    return ContextLoggerAdapter(logger, context)


def get_request_logger() -> logging.LoggerAdapter:
    return get_logger()