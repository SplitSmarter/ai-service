# src/services/manager/key_manager.py
import logging

from redis import RedisError

from src.config.config import settings, ctx_tokens_used
from src.database.redis import get_redis

logger = logging.getLogger(__name__)


class DynamicRotationManager:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        # Updated to use the clean settings object property method
        self.configured_keys = settings.parsed_ai_keys

    async def select_least_used_key(self, target_provider: str) -> tuple[str, str]:
        """
        Scans Redis for matching configuration variants and shifts workload balancing
        directly onto the key that has processed the fewest lifetime tokens.

        Returns: Tuple containing (identifier, api_key_value)
        """
        # 1. Filter out raw settings entries matching the explicit provider
        provider_keys = [k for k in self.configured_keys if k["provider"].lower() == target_provider.lower()]

        if not provider_keys:
            raise ValueError(f"No credentials configured inside system memory matching provider: {target_provider}")

        # Shortcut optimal routing bypass check
        if len(provider_keys) == 1:
            return provider_keys[0]["identifier"], provider_keys[0]["value"]

        r = await get_redis(self.logger)

        # 2. Extract execution balances across keys simultaneously using an absolute MGET pipeline
        redis_lookup_keys = [f"metrics:usage:{k['provider']}:{k['identifier']}" for k in provider_keys]
        metrics_results = await r.mget(redis_lookup_keys)

        least_used_index = 0
        minimum_tokens_tracked = float("inf")

        # 3. Analyze output structures to trace the key with lowest transaction data
        for index, raw_token_count in enumerate(metrics_results):
            current_count = int(raw_token_count) if raw_token_count is not None else 0

            if current_count < minimum_tokens_tracked:
                minimum_tokens_tracked = current_count
                least_used_index = index

        selected_match = provider_keys[least_used_index]
        self.logger.info(
            f"Key Rotation selected candidate identity '{selected_match['identifier']}' "
            f"for processing workload (recorded volume usage: {minimum_tokens_tracked} tokens)"
        )

        return selected_match["identifier"], selected_match["value"]

    async def commit_usage_metrics(self, provider: str, key_identifier: str, tokens: int):
        """Increments key usage in Redis. Fails gracefully if Redis is unreachable."""
        if not tokens:
            return

        redis_metric_key = f"metrics:{provider}:{key_identifier}"
        try:
            await self.redis_client.incrby(redis_metric_key, tokens)
        except RedisError as err:
            # Fallback: log warning so the primary inference response isn't lost
            logger.warning(f"Failed to record token usage in Redis ({err}). Skipping metric commit.")
        except Exception as err:
            logger.warning(f"Unexpected error committing metrics to Redis: {err}")
