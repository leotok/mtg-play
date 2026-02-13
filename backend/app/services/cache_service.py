import redis.asyncio as redis
import json
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta


class RedisCacheService:
    def __init__(self, redis_url: str, ttl_days: int = 7):
        self.redis_url = redis_url
        self.default_ttl = ttl_days * 24 * 3600  # Convert days to seconds
        self._redis = None
        self._available = None  # Cache Redis availability
    
    async def get_redis(self):
        """Get Redis connection (lazy initialization with availability check)"""
        if self._available is False:
            return None
        
        if self._redis is None:
            try:
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                await self._redis.ping()
                self._available = True
            except Exception as e:
                print(f"Redis connection failed: {e}")
                self._available = False
                self._redis = None
        
        return self._redis if self._available else None
    
    async def is_available(self) -> bool:
        """Check if Redis is available"""
        if self._available is None:
            await self.get_redis()
        return self._available
    
    async def get_card_by_id(self, scryfall_id: str) -> Optional[Dict[str, Any]]:
        """Get card by Scryfall ID from cache"""
        redis_client = await self.get_redis()
        if not redis_client:
            return None
            
        key = f"card:id:{scryfall_id}"
        
        try:
            data = await redis_client.get(key)
            if data:
                await self._increment_stats("hits")
                return json.loads(data)
            
            await self._increment_stats("misses")
            return None
        except Exception as e:
            print(f"Redis error getting card by ID {scryfall_id}: {e}")
            return None
    
    async def get_card_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get card by name from cache"""
        redis_client = await self.get_redis()
        if not redis_client:
            return None
            
        key = f"card:name:{name.lower()}"
        
        try:
            data = await redis_client.get(key)
            if data:
                await self._increment_stats("hits")
                return json.loads(data)
            
            await self._increment_stats("misses")
            return None
        except Exception as e:
            print(f"Redis error getting card by name {name}: {e}")
            return None
    
    async def cache_card(self, scryfall_id: str, name: str, card_data: Dict[str, Any]):
        """Cache card data with both ID and name keys"""
        redis_client = await self.get_redis()
        if not redis_client:
            return
            
        card_json = json.dumps(card_data)
        
        try:
            # Use pipeline for atomic operations
            pipe = redis_client.pipeline()
            
            # Cache by ID
            id_key = f"card:id:{scryfall_id}"
            pipe.setex(id_key, self.default_ttl, card_json)
            
            # Cache by name
            name_key = f"card:name:{name.lower()}"
            pipe.setex(name_key, self.default_ttl, card_json)
            
            # Update popular cards (sorted set with score = request count)
            pipe.zincrby("popular:cards", 1, name.lower())
            
            # Update cache statistics
            pipe.incr("stats:scryfall:cached")
            pipe.expire("stats:scryfall:cached", 24 * 3600)  # 1 day TTL
            
            await pipe.execute()
            
        except Exception as e:
            print(f"Redis error caching card {name}: {e}")
    
    async def get_multiple_cards(self, identifiers: List[str], by_name: bool = True) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple cards from cache in parallel"""
        redis_client = await self.get_redis()
        if not redis_client:
            return {id: None for id in identifiers}
        
        if by_name:
            keys = [f"card:name:{id.lower()}" for id in identifiers]
        else:
            keys = [f"card:id:{id}" for id in identifiers]
        
        try:
            # Use mget for batch operations
            values = await redis_client.mget(keys)
            
            results = {}
            hits = 0
            misses = 0
            
            for i, identifier in enumerate(identifiers):
                if values[i] is not None:
                    results[identifier] = json.loads(values[i])
                    hits += 1
                else:
                    results[identifier] = None
                    misses += 1
            
            # Update statistics
            await self._increment_stats_by_amount("hits", hits)
            await self._increment_stats_by_amount("misses", misses)
            
            return results
        except Exception as e:
            print(f"Redis error getting multiple cards: {e}")
            return {id: None for id in identifiers}
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        redis_client = await self.get_redis()
        if not redis_client:
            return {
                'error': 'Redis not available',
                'hits': 0,
                'misses': 0,
                'cached': 0,
                'hit_rate': 0,
                'total_keys': 0,
                'memory_usage': 'N/A',
                'connected_clients': 'N/A',
                'redis_version': 'N/A'
            }
        
        try:
            pipe = redis_client.pipeline()
            
            # Get basic stats
            pipe.get("stats:scryfall:hits")
            pipe.get("stats:scryfall:misses")
            pipe.get("stats:scryfall:cached")
            
            # Get Redis info
            pipe.dbsize()
            pipe.info()
            
            results = await pipe.execute()
            hits, misses, cached, total_keys, info = results
            
            hits = int(hits) if hits else 0
            misses = int(misses) if misses else 0
            cached = int(cached) if cached else 0
            
            hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
            
            return {
                'hits': hits,
                'misses': misses,
                'cached': cached,
                'hit_rate': hit_rate,
                'total_keys': total_keys,
                'memory_usage': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 'N/A'),
                'redis_version': info.get('redis_version', 'N/A')
            }
        except Exception as e:
            return {
                'error': str(e),
                'hits': 0,
                'misses': 0,
                'cached': 0,
                'hit_rate': 0,
                'total_keys': 0,
                'memory_usage': 'N/A'
            }
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache keys matching pattern"""
        redis_client = await self.get_redis()
        if not redis_client:
            return 0
            
        try:
            keys = await redis_client.keys(pattern)
            if keys:
                return await redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Redis error clearing pattern {pattern}: {e}")
            return 0
    
    async def clear_all(self) -> int:
        """Clear all cache entries"""
        return await self.clear_pattern("card:*")
    
    async def get_popular_cards(self, limit: int = 50) -> List[str]:
        """Get most popular cards from cache"""
        redis_client = await self.get_redis()
        if not redis_client:
            return []
            
        try:
            # Get top cards from sorted set (highest score first)
            popular_cards = await redis_client.zrevrange("popular:cards", 0, limit - 1, withscores=True)
            return [card for card, score in popular_cards]
        except Exception as e:
            print(f"Redis error getting popular cards: {e}")
            return []
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def _increment_stats(self, stat_type: str):
        """Increment cache statistics by 1"""
        redis_client = await self.get_redis()
        if not redis_client:
            return
            
        key = f"stats:scryfall:{stat_type}"
        try:
            await redis_client.incr(key)
            await redis_client.expire(key, 24 * 3600)  # 1 day TTL
        except Exception as e:
            print(f"Redis error incrementing stats {stat_type}: {e}")
    
    async def _increment_stats_by_amount(self, stat_type: str, amount: int):
        """Increment cache statistics by specific amount"""
        redis_client = await self.get_redis()
        if not redis_client:
            return
            
        key = f"stats:scryfall:{stat_type}"
        try:
            await redis_client.incrby(key, amount)
            await redis_client.expire(key, 24 * 3600)  # 1 day TTL
        except Exception as e:
            print(f"Redis error incrementing stats {stat_type} by {amount}: {e}")


class SmartRateLimiter:
    def __init__(self, max_requests_per_second: int = 10):
        self.max_requests = max_requests_per_second
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire rate limit with intelligent backoff"""
        async with self.lock:
            now = datetime.now()
            # Remove old requests (older than 1 second)
            self.requests = [req_time for req_time in self.requests if (now - req_time).total_seconds() < 1]
            
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                sleep_time = 1.0 - (now - self.requests[0]).total_seconds()
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            self.requests.append(now)


# Singleton instance for dependency injection
_cache_service = None

def get_cache_service() -> RedisCacheService:
    """Get or create cache service instance"""
    global _cache_service
    if _cache_service is None:
        from app.core.config import settings
        _cache_service = RedisCacheService(settings.REDIS_URL)
    return _cache_service
