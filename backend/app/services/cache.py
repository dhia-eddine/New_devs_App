import json
import logging
from typing import Any

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config import settings
from app.services.reservations import calculate_total_revenue

logger = logging.getLogger(__name__)
redis_client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)


async def get_revenue_summary(
    property_id: str,
    tenant_id: str | None,
    year: int | None = None,
    month: int | None = None,
) -> dict[str, Any] | None:
    cache_key = f"revenue:v2:{json.dumps([tenant_id, property_id, year, month])}"
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except (RedisError, ValueError):
        logger.warning("Revenue cache read failed")

    result = await calculate_total_revenue(property_id, tenant_id, year, month)
    if result is not None:
        try:
            await redis_client.setex(cache_key, 300, json.dumps(result))
        except RedisError:
            logger.warning("Revenue cache write failed")

    return result
