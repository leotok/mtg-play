from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

from app.services.cache_service import get_cache_service
from app.services.scryfall import get_scryfall_service


router = APIRouter()


class CacheWarmRequest(BaseModel):
    """Request for cache warming"""
    card_names: List[str]
    by_name: bool = True


class CacheStatsResponse(BaseModel):
    """Cache statistics response"""
    hits: int
    misses: int
    cached: int
    hit_rate: float
    total_keys: int
    memory_usage: str
    connected_clients: str
    redis_version: str


class CacheClearResponse(BaseModel):
    """Cache clearing response"""
    message: str
    cleared_count: int


class CacheWarmResponse(BaseModel):
    """Cache warming response"""
    message: str
    warmed_cards: int
    requested: int
    failed_cards: List[str] = []


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """Get cache statistics"""
    cache_service = get_cache_service()
    try:
        stats = await cache_service.get_cache_stats()
        
        if 'error' in stats:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Cache service unavailable: {stats['error']}"
            )
        
        return CacheStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting cache stats: {str(e)}"
        )


@router.post("/reset", response_model=CacheClearResponse)
async def reset_cache():
    """Clear all cache entries"""
    cache_service = get_cache_service()
    try:
        cleared_count = await cache_service.clear_all()
        return CacheClearResponse(
            message=f"Successfully cleared {cleared_count} cache entries",
            cleared_count=cleared_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing cache: {str(e)}"
        )


@router.post("/clear-pattern", response_model=CacheClearResponse)
async def clear_cache_pattern(pattern: str):
    """Clear cache entries matching pattern"""
    cache_service = get_cache_service()
    try:
        cleared_count = await cache_service.clear_pattern(pattern)
        return CacheClearResponse(
            message=f"Successfully cleared {cleared_count} entries matching pattern '{pattern}'",
            cleared_count=cleared_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing cache pattern: {str(e)}"
        )


@router.post("/warm", response_model=CacheWarmResponse)
async def warm_cache(request: CacheWarmRequest):
    """Warm cache with popular cards"""
    cache_service = get_cache_service()
    scryfall_service = get_scryfall_service()
    
    try:
        # Get cards in parallel (this will use cache + API)
        card_results = await scryfall_service.get_multiple_cards(
            request.card_names, 
            by_name=request.by_name
        )
        
        # Count successful vs failed
        warmed_count = 0
        failed_cards = []
        
        for card_name in request.card_names:
            if card_results.get(card_name):
                warmed_count += 1
            else:
                failed_cards.append(card_name)
        
        return CacheWarmResponse(
            message=f"Warmed {warmed_count} out of {len(request.card_names)} cards in cache",
            warmed_cards=warmed_count,
            requested=len(request.card_names),
            failed_cards=failed_cards
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error warming cache: {str(e)}"
        )


@router.get("/popular", response_model=List[str])
async def get_popular_cards(limit: int = 50):
    """Get most popular cards from cache"""
    cache_service = get_cache_service()
    try:
        popular_cards = await cache_service.get_popular_cards(limit)
        return popular_cards
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting popular cards: {str(e)}"
        )


@router.get("/health")
async def cache_health():
    """Check cache service health"""
    cache_service = get_cache_service()
    try:
        stats = await cache_service.get_cache_stats()
        
        if 'error' in stats:
            return {
                "status": "unhealthy",
                "error": stats['error']
            }
        
        return {
            "status": "healthy",
            "total_keys": stats.get('total_keys', 0),
            "memory_usage": stats.get('memory_usage', 'N/A'),
            "connected_clients": stats.get('connected_clients', 'N/A')
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
