import httpx
import asyncio
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.services.cache_service import RedisCacheService, SmartRateLimiter, get_cache_service

# Global service instance
_scryfall_service = None


class ScryfallService:
    def __init__(self, cache_service: Optional[RedisCacheService] = None):
        self.base_url = settings.SCRYFALL_API_URL
        self.client = httpx.AsyncClient(timeout=30.0)
        self.cache = cache_service
        self.semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests
        self.rate_limiter = SmartRateLimiter(max_requests_per_second=10)
        self._rate_limit_delay = 0.1  # Fallback delay

    async def close(self):
        """Close HTTP client and cache service"""
        await self.client.aclose()
        if self.cache:
            await self.cache.close()

    async def get_card_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get card information by name using cache first, then Scryfall API"""
        # Check cache first
        if self.cache:
            cached_card = await self.cache.get_card_by_name(name)
            if cached_card:
                return cached_card
        
        # Fetch from API
        try:
            await self.rate_limiter.acquire()
            response = await self.client.get(
                f"{self.base_url}/cards/named",
                params={"exact": name}
            )
            response.raise_for_status()
            card_data = response.json()
            
            # Cache the result
            if self.cache:
                await self.cache.cache_card(card_data['id'], name, card_data)
            
            return card_data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            print(f"Error fetching card {name}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching card {name}: {e}")
            return None

    async def get_card_by_scryfall_id(self, scryfall_id: str) -> Optional[Dict[str, Any]]:
        """Get card information by Scryfall ID using cache first, then API"""
        # Check cache first
        if self.cache:
            cached_card = await self.cache.get_card_by_id(scryfall_id)
            if cached_card:
                return cached_card
        
        # Fetch from API
        try:
            await self.rate_limiter.acquire()
            response = await self.client.get(
                f"{self.base_url}/cards/{scryfall_id}"
            )
            response.raise_for_status()
            card_data = response.json()
            
            # Cache the result
            if self.cache:
                await self.cache.cache_card(card_data['id'], card_data['name'], card_data)
            
            return card_data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            print(f"Error fetching card {scryfall_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching card {scryfall_id}: {e}")
            return None

    async def get_multiple_cards(self, identifiers: List[str], by_name: bool = True) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple cards in parallel with caching and rate limiting"""
        if not identifiers:
            return {}
        
        # First, check cache for all cards
        cache_results = {}
        uncached_identifiers = []
        
        if self.cache:
            cache_results = await self.cache.get_multiple_cards(identifiers, by_name)
            uncached_identifiers = [id for id, result in cache_results.items() if result is None]
        else:
            uncached_identifiers = identifiers
        
        # Fetch uncached cards from API in parallel
        api_results = {}
        if uncached_identifiers:
            api_results = await self._fetch_multiple_from_api(uncached_identifiers, by_name)
        
        # Combine results
        final_results = {}
        for identifier in identifiers:
            if identifier in cache_results and cache_results[identifier] is not None:
                final_results[identifier] = cache_results[identifier]
            elif identifier in api_results:
                final_results[identifier] = api_results[identifier]
            else:
                final_results[identifier] = None
        
        return final_results
    
    async def _fetch_multiple_from_api(self, identifiers: List[str], by_name: bool) -> Dict[str, Optional[Dict[str, Any]]]:
        """Fetch multiple cards from API in parallel"""
        tasks = []
        for identifier in identifiers:
            if by_name:
                task = self._get_card_by_name_with_semaphore(identifier)
            else:
                task = self._get_card_by_id_with_semaphore(identifier)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        api_results = {}
        for i, identifier in enumerate(identifiers):
            result = results[i]
            if isinstance(result, Exception):
                print(f"Error fetching {identifier}: {result}")
                api_results[identifier] = None
            else:
                api_results[identifier] = result
                # Cache the successful result
                if result and self.cache:
                    await self.cache.cache_card(result['id'], result['name'], result)
        
        return api_results
    
    async def _get_card_by_name_with_semaphore(self, name: str) -> Optional[Dict[str, Any]]:
        """Get card by name with semaphore control"""
        async with self.semaphore:
            return await self.get_card_by_name(name)
    
    async def _get_card_by_id_with_semaphore(self, scryfall_id: str) -> Optional[Dict[str, Any]]:
        """Get card by ID with semaphore control"""
        async with self.semaphore:
            return await self.get_card_by_scryfall_id(scryfall_id)

    async def validate_commander(self, scryfall_id: str) -> Dict[str, Any]:
        """Validate if a card can be a commander (Legendary Creature)"""
        card_data = await self.get_card_by_scryfall_id(scryfall_id)
        if not card_data:
            return {"valid": False, "reason": "Card not found"}
        
        type_line = card_data.get("type_line", "")
        if not ("Legendary" in type_line and "Creature" in type_line):
            return {"valid": False, "reason": "Commander must be a Legendary creature"}
        
        return {"valid": True, "card": card_data}

    async def search_cards(self, query: str, type_line: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for cards by name"""
        try:
            await self.rate_limiter.acquire()
            
            # Build search query
            search_query = query
            if type_line:
                search_query = f"{query} type:{type_line}"
            
            response = await self.client.get(
                f"{self.base_url}/cards/search",
                params={"q": search_query, "limit": limit}
            )
            response.raise_for_status()
            search_data = response.json()
            
            # Cache the results
            if self.cache and search_data.get("data"):
                for card in search_data["data"]:
                    await self.cache.cache_card(card['id'], card['name'], card)
            
            return search_data.get("data", [])
        except Exception as e:
            print(f"Error searching cards: {e}")
            return []


# Update singleton instance to use cache
def get_scryfall_service() -> ScryfallService:
    """Get or create Scryfall service instance with cache"""
    global _scryfall_service
    if _scryfall_service is None:
        cache_service = get_cache_service()
        _scryfall_service = ScryfallService(cache_service)
    return _scryfall_service
