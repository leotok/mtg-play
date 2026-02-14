from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import logging

from app.schemas.card import CardBasic
from app.schemas.deck_import import CardLookupRequest, CardValidationRequest, CardValidationResponse, ValidatedCard
from app.services.scryfall import get_scryfall_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search")
async def search_cards(q: str, type: Optional[str] = None, limit: int = 10):
    """Search for cards by name"""
    logger.info(f"Card search - Query: {q}, Type: {type}, Limit: {limit}")
    scryfall_service = get_scryfall_service()
    
    try:
        # Search using Scryfall API
        results = await scryfall_service.search_cards(q, type_line=type, limit=limit)
        logger.info(f"Card search successful - Found {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Card search failed - Query: {q}, Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching cards: {str(e)}"
        )


@router.get("/scryfall/{scryfall_id}", response_model=CardBasic)
async def get_card_by_scryfall_id(scryfall_id: str):
    """Get card information by Scryfall ID"""
    scryfall_service = get_scryfall_service()
    
    # Fetch from Scryfall API
    try:
        scryfall_data = await scryfall_service.get_card_by_scryfall_id(scryfall_id)
        if not scryfall_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        return CardBasic(
            scryfall_id=scryfall_data.get("id"),
            name=scryfall_data.get("name"),
            mana_cost=scryfall_data.get("mana_cost"),
            cmc=scryfall_data.get("cmc"),
            type_line=scryfall_data.get("type_line"),
            colors=scryfall_data.get("colors"),
            color_identity=scryfall_data.get("color_identity"),
            oracle_text=scryfall_data.get("oracle_text"),
            power=scryfall_data.get("power"),
            toughness=scryfall_data.get("toughness"),
            loyalty=scryfall_data.get("loyalty"),
            image_uris=scryfall_data.get("image_uris"),
            legalities=scryfall_data.get("legalities")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching card: {str(e)}"
        )


@router.post("/lookup", response_model=CardBasic)
async def lookup_card(request: CardLookupRequest):
    """Lookup card by name or Scryfall ID"""
    scryfall_service = get_scryfall_service()
    
    try:
        if request.by_name:
            scryfall_data = await scryfall_service.get_card_by_name(request.identifier)
        else:
            scryfall_data = await scryfall_service.get_card_by_scryfall_id(request.identifier)
        
        if not scryfall_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        return CardBasic(
            scryfall_id=scryfall_data.get("id"),
            name=scryfall_data.get("name"),
            mana_cost=scryfall_data.get("mana_cost"),
            cmc=scryfall_data.get("cmc"),
            type_line=scryfall_data.get("type_line"),
            colors=scryfall_data.get("colors"),
            color_identity=scryfall_data.get("color_identity"),
            oracle_text=scryfall_data.get("oracle_text"),
            power=scryfall_data.get("power"),
            toughness=scryfall_data.get("toughness"),
            loyalty=scryfall_data.get("loyalty"),
            image_uris=scryfall_data.get("image_uris"),
            legalities=scryfall_data.get("legalities")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error looking up card: {str(e)}"
        )


@router.post("/validate", response_model=CardValidationResponse)
async def validate_cards(request: CardValidationRequest):
    """Validate a list of card names against Scryfall"""
    scryfall_service = get_scryfall_service()
    
    try:
        # Get all cards in parallel
        card_results = await scryfall_service.get_multiple_cards(request.card_names, by_name=True)
        
        valid_cards = []
        invalid_cards = []
        
        for name in request.card_names:
            card_data = card_results.get(name)
            if card_data:
                valid_cards.append(ValidatedCard(
                    name=name,
                    found=True,
                    scryfall_id=card_data.get("id")
                ))
            else:
                invalid_cards.append(ValidatedCard(
                    name=name,
                    found=False,
                    error="Card not found"
                ))
        
        return CardValidationResponse(
            valid_cards=valid_cards,
            invalid_cards=invalid_cards,
            total_valid=len(valid_cards),
            total_invalid=len(invalid_cards),
            errors=[]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating cards: {str(e)}"
        )


