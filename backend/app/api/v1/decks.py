from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.schemas.deck import DeckCreate, DeckUpdate, DeckResponse, DeckList, DeckStats
from app.schemas.deck_card import DeckCardCreate, DeckCardUpdate, DeckCardResponse
from app.schemas.deck_import import ImportRequest, ImportResult, ImportedCard
from app.schemas.simple_import import SimpleDeckImport, SimpleImportResult
from app.schemas.text_import import TextDeckImport, TextImportResult
from app.schemas.deck_text_import import DeckTextImport, DeckImportResult
from app.services.deck_service import get_deck_service
from app.services.deck_analytics import DeckAnalytics
from app.services.scryfall import get_scryfall_service
from app.services.arena_parser import ArenaParser
from app.models.user import User
from app.models.deck import Deck
from app.services.deck_service import DeckService

# Authentication dependencies
from app.core.auth import get_current_user, get_user_deck_or_404, get_public_deck_or_404

router = APIRouter()


def get_deck_service(db: Session = Depends(get_db)) -> DeckService:
    """Dependency to get deck service"""
    from app.services.deck_service import DeckService
    service = DeckService.create_with_repositories(db)
    service.set_validator(db)
    return service


def get_deck_analytics(db: Session = Depends(get_db)) -> DeckAnalytics:
    """Dependency to get deck analytics"""
    return DeckAnalytics.create_with_repositories(db)


@router.get("/decks", response_model=List[DeckList])
async def get_user_decks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    deck_service: DeckService = Depends(get_deck_service),
    current_user: User = Depends(get_current_user)
):
    """Get all decks for the current user"""
    return await deck_service.get_user_decks(current_user.id, skip, limit)


@router.post("/decks", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
async def create_deck(
    deck_data: DeckCreate,
    deck_service: DeckService = Depends(get_deck_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new deck"""
    logger.info(f"Deck creation attempt - User: {current_user.id}, Name: {deck_data.name}, Commander ID: {deck_data.commander_scryfall_id}")
    try:
        result = await deck_service.create_deck(deck_data, current_user.id)
        logger.info(f"Deck created successfully - ID: {result.id}, User: {current_user.id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deck creation failed - User: {current_user.id}, Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create deck: {str(e)}"
        )


@router.get("/decks/{deck_id}", response_model=DeckResponse)
async def get_deck(
    deck_id: int,
    deck: Deck = Depends(get_user_deck_or_404),
    deck_service: DeckService = Depends(get_deck_service)
):
    """Get a specific deck"""
    return await deck_service.get_deck(deck_id, deck.owner_id)


@router.put("/decks/{deck_id}", response_model=DeckResponse)
async def update_deck(
    deck_id: int,
    deck_data: DeckUpdate,
    deck: Deck = Depends(get_user_deck_or_404),
    deck_service: DeckService = Depends(get_deck_service)
):
    """Update a deck"""
    return await deck_service.update_deck(deck_id, deck_data, deck.owner_id)


@router.delete("/decks/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(
    deck_id: int,
    deck: Deck = Depends(get_user_deck_or_404),
    deck_service: DeckService = Depends(get_deck_service)
):
    """Delete a deck"""
    await deck_service.delete_deck(deck_id, deck.owner_id)


@router.delete("/decks/{deck_id}/cards", status_code=status.HTTP_204_NO_CONTENT)
async def clear_deck_cards(
    deck_id: int,
    deck: Deck = Depends(get_user_deck_or_404),
    deck_service: DeckService = Depends(get_deck_service)
):
    """Remove all non-commander cards from a deck"""
    deck_service.deck_repo.clear_non_commander_cards(deck_id)


@router.get("/decks/{deck_id}/cards", response_model=List[DeckCardResponse])
async def get_deck_cards(
    deck_id: int,
    deck: Deck = Depends(get_user_deck_or_404),
    deck_service: DeckService = Depends(get_deck_service)
):
    """Get all cards in a deck"""
    return await deck_service.get_deck_cards(deck_id, deck.owner_id)


@router.post("/import", response_model=ImportResult, status_code=status.HTTP_201_CREATED)
async def import_deck(
    request: ImportRequest,
    deck_service: DeckService = Depends(get_deck_service),
    current_user: User = Depends(get_current_user)
):
    """Import a deck from various formats"""
    try:
        if request.format == "json":
            scryfall_service = get_scryfall_service()
            return await _import_json_deck(request.json_data, deck_service, scryfall_service, current_user.id)
        elif request.format == "arena":
            scryfall_service = get_scryfall_service()
            return await _import_arena_deck(request.arena_data, deck_service, scryfall_service, current_user.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported import format: {request.format}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing deck: {str(e)}"
        )


async def _import_json_deck(
    json_data, 
    deck_service: DeckService, 
    scryfall_service, 
    current_user_id: int
) -> ImportResult:
    """Import deck from JSON format with Scryfall-only approach"""
    from app.schemas.deck_import import JsonImportCard
    
    imported_cards = []
    failed_cards = []
    warnings = []
    errors = []
    
    # Find commander
    commander_name = json_data.get("commander")
    if not commander_name:
        errors.append("No commander found in deck")
        return ImportResult(success=False, errors=errors)
    
    # Get commander from Scryfall
    commander_data = await scryfall_service.get_card_by_name(commander_name)
    if not commander_data:
        errors.append(f"Commander '{commander_name}' not found")
        return ImportResult(success=False, errors=errors)
    
    # Validate commander is legendary creature
    validation = await scryfall_service.validate_commander(commander_data.get("id"))
    if not validation["valid"]:
        errors.append(f"Commander validation failed: {validation['reason']}")
        return ImportResult(success=False, errors=errors)
    
    # Create deck
    deck_create = DeckCreate(
        name=json_data.get("name", "Imported Deck"),
        description=json_data.get("description", ""),
        commander_scryfall_id=commander_data.get("id"),
        is_public=json_data.get("is_public", False)
    )
    
    try:
        deck = await deck_service.create_deck(deck_create, current_user_id)
    except Exception as e:
        errors.append(f"Error creating deck: {str(e)}")
        return ImportResult(success=False, errors=errors)
    
    # Add commander to imported cards
    imported_cards.append(ImportedCard(
        name=commander_data.get("name"),
        scryfall_id=commander_data.get("id"),
        quantity=1,
        is_commander=True,
        found=True
    ))
    
    # Get all card names from deck
    card_names = [card["name"] for card in json_data.get("cards", [])]
    
    # Fetch all cards from Scryfall in parallel
    card_data_map = await scryfall_service.get_multiple_cards(card_names, by_name=True)
    
    # Import cards
    for card_info in json_data.get("cards", []):
        card_name = card_info["name"]
        quantity = card_info["quantity"]
        
        card_data = card_data_map.get(card_name)
        if not card_data:
            failed_cards.append({
                "name": card_name,
                "error": "Card not found"
            })
            continue
        
        try:
            # Add card to deck
            deck_card_data = {
                "card_scryfall_id": card_data.get("id"),
                "quantity": quantity,
                "is_commander": False
            }
            
            deck_service.deck_repo.add_card_to_deck(deck.id, card_data.get("id"), quantity, False)
            
            imported_cards.append(ImportedCard(
                name=card_data.get("name"),
                scryfall_id=card_data.get("id"),
                quantity=quantity,
                is_commander=False,
                found=True
            ))
        except Exception as e:
            failed_cards.append({
                "name": card_name,
                "error": str(e)
            })
    
    return ImportResult(
        success=True,
        deck_id=deck.id,
        deck_name=deck.name,
        imported_cards=imported_cards,
        failed_cards=failed_cards,
        warnings=warnings,
        errors=errors,
    )


async def _import_arena_deck(
    arena_data, 
    deck_service: DeckService, 
    scryfall_service, 
    current_user_id: int
) -> ImportResult:
    """Import deck from MTG Arena format with parallel processing"""
    imported_cards = []
    failed_cards = []
    warnings = []
    errors = []
    
    # Parse Arena format
    parser = ArenaParser()
    parse_result = parser.parse_and_validate(arena_data.deck_text)
    
    if parse_result["parse_errors"]:
        errors.extend([f"Parse error: {error}" for error in parse_result["parse_errors"]])
    
    if parse_result["validation_errors"]:
        warnings.extend([f"Validation warning: {error}" for error in parse_result["validation_errors"]])
    
    if not parse_result["cards"]:
        errors.append("No cards found in deck text")
        return ImportResult(success=False, errors=errors)
    
    # Find commander
    commander_entry = parse_result["commander"]
    if not commander_entry:
        # Try to infer commander (first legendary creature, for now just use first card)
        commander_entry = parse_result["cards"][0]
        warnings.append("No explicit commander found, using first card as commander")
    
    # Get all unique card names for parallel processing
    unique_card_names = list(set(card.name for card in parse_result["cards"]))
    
    # Fetch all cards in parallel
    card_results = await scryfall_service.get_multiple_cards(unique_card_names, by_name=True)
    
    # Create card name to data mapping
    card_data_map = {name: data for name, data in card_results.items() if data is not None}
    
    # Check for missing cards
    missing_cards = [name for name in unique_card_names if name not in card_data_map]
    if missing_cards:
        for missing_card in missing_cards:
            failed_cards.append({
                "name": missing_card,
                "error": "Card not found"
            })
    
    # Get commander from fetched cards
    commander_scryfall_data = card_data_map.get(commander_entry.name)
    if not commander_scryfall_data:
        errors.append(f"Commander '{commander_entry.name}' not found")
        return ImportResult(success=False, errors=errors)
    
    # Create deck with Scryfall-only approach
    deck_create = DeckCreate(
        name=arena_data.name,
        description=arena_data.description or "",
        commander_scryfall_id=commander_scryfall_data.get("id"),
        is_public=arena_data.is_public
    )
    
    try:
        deck = await deck_service.create_deck(deck_create, current_user_id)
    except Exception as e:
        errors.append(f"Error creating deck: {str(e)}")
        return ImportResult(success=False, errors=errors)
    
    # Add commander to imported cards
    imported_cards.append(ImportedCard(
        name=commander_scryfall_data.get("name"),
        scryfall_id=commander_scryfall_data.get("id"),
        quantity=1,
        is_commander=True,
        found=True
    ))
    
    # Import cards in batch (skip commander since it's already added)
    non_commander_entries = [card for card in parse_result["cards"] if not card.is_commander]
    
    for card_entry in non_commander_entries:
        try:
            scryfall_data = card_data_map.get(card_entry.name)
            if not scryfall_data:
                failed_cards.append({
                    "name": card_entry.name,
                    "error": "Card data not available"
                })
                continue
            
            # Add card to deck via repository (Scryfall-only)
            deck_service.deck_repo.add_card_to_deck(
                deck.id,
                scryfall_data.get("id"),
                card_entry.quantity,
                False
            )
            
            imported_cards.append(ImportedCard(
                name=scryfall_data.get("name"),
                scryfall_id=scryfall_data.get("id"),
                quantity=card_entry.quantity,
                is_commander=False,
                found=True
            ))
            
        except Exception as e:
            failed_cards.append({
                "name": card_entry.name,
                "error": str(e)
            })
    
    # Validate deck
    validation = deck_service.validate_deck(deck.id, current_user_id)
    if not validation["is_valid"]:
        warnings.extend(validation["validation_errors"])
    
    return ImportResult(
        success=True,
        deck_id=deck.id,
        deck_name=deck.name,
        imported_cards=imported_cards,
        failed_cards=failed_cards,
        warnings=warnings,
        errors=errors,
        validation_errors=validation["validation_errors"]
    )


@router.post("/decks/{deck_id}/validate")
async def validate_deck(
    deck_id: int,
    deck: Deck = Depends(get_user_deck_or_404),
    deck_service: DeckService = Depends(get_deck_service)
):
    """Validate a deck against Commander format rules"""
    return deck_service.validate_deck(deck_id, deck.owner_id)


@router.get("/decks/{deck_id}/export")
async def export_deck(
    deck_id: int,
    deck: Deck = Depends(get_user_deck_or_404),
    deck_service: DeckService = Depends(get_deck_service)
):
    """Export deck in JSON format with full card details from Scryfall"""
    export_data = await deck_service.export_deck(deck_id, deck.owner_id)
    if "error" in export_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=export_data["error"]
        )
    return export_data


@router.get("/decks/{deck_id}/stats", response_model=DeckStats)
async def get_deck_stats(
    deck_id: int,
    deck: Deck = Depends(get_user_deck_or_404),
    deck_analytics: DeckAnalytics = Depends(get_deck_analytics),
    deck_service: DeckService = Depends(get_deck_service)
):
    """Get basic deck statistics"""
    stats = deck_analytics.get_deck_stats(deck_id)
    if "error" in stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=stats["error"]
        )
    # Add validation results
    validation = deck_service.validate_deck(deck_id, deck.owner_id)
    stats.update({
        "is_valid": validation["is_valid"],
        "validation_errors": validation["validation_errors"]
    })
    return DeckStats(**stats)


@router.delete("/decks/{deck_id}/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_card_from_deck(
    deck_id: int,
    card_id: int,
    deck: Deck = Depends(get_user_deck_or_404),
    deck_service: DeckService = Depends(get_deck_service)
):
    """Remove a card from a deck"""
    deck_service.remove_card_from_deck(deck_id, card_id, deck.owner_id)


@router.put("/decks/{deck_id}/cards/{card_id}", response_model=DeckCardResponse)
async def update_card_in_deck(
    deck_id: int,
    card_id: int,
    card_data: DeckCardUpdate,
    deck: Deck = Depends(get_user_deck_or_404),
    deck_service: DeckService = Depends(get_deck_service)
):
    """Update a card in a deck (card_id is the DeckCard primary key)"""
    return await deck_service.update_card_in_deck(deck_id, card_id, card_data, deck.owner_id)


@router.post("/decks/{deck_id}/cards", response_model=DeckCardResponse, status_code=status.HTTP_201_CREATED)
async def add_card_to_deck(
    deck_id: int,
    card_data: dict,
    deck: Deck = Depends(get_user_deck_or_404),
    deck_service: DeckService = Depends(get_deck_service)
):
    """Add a card to a deck"""
    from app.schemas.deck_card import DeckCardCreate
    deck_card_data = DeckCardCreate(
        deck_id=deck_id,
        card_scryfall_id=card_data["card_scryfall_id"],
        quantity=card_data.get("quantity", 1),
        is_commander=card_data.get("is_commander", False)
    )
    return await deck_service.add_card_to_deck(deck_id, deck_card_data, deck.owner_id)


@router.post("/decks/{deck_id}/import/text", response_model=DeckImportResult, status_code=status.HTTP_201_CREATED)
async def import_cards_to_deck(
    deck_id: int,
    request: DeckTextImport,
    deck: Deck = Depends(get_user_deck_or_404),
    deck_service: DeckService = Depends(get_deck_service)
):
    """Import cards into an existing deck from text"""
    scryfall_service = get_scryfall_service()
    
    imported_count = 0
    failed_cards = []
    errors = []
    
    try:
        # Parse deck text - one card per line, format: "quantity cardname"
        lines = [line.strip() for line in request.deck_text.split('\n') if line.strip()]
        parsed_cards = []
        
        for line in lines:
            if not line:
                continue
            
            # Skip sideboard section
            if line.startswith("SIDEBOARD:") or line.startswith("SIDEBOARD"):
                break
                
            parts = line.split(' ', 1)
            if len(parts) >= 2:
                try:
                    quantity = int(parts[0])
                    card_name = ' '.join(parts[1:]).strip()
                    parsed_cards.append({"name": card_name, "quantity": quantity})
                    print(f"Parsed: {quantity}x {card_name}")  # Debug logging
                except ValueError:
                    failed_cards.append(f"{line}: Invalid quantity format")
                    print(f"Failed to parse quantity: {line}")  # Debug logging
            else:
                # Default quantity 1 if just card name
                card_name = line.strip()
                parsed_cards.append({"name": card_name, "quantity": 1})
                print(f"Parsed (no quantity): 1x {card_name}")  # Debug logging
        
        if not parsed_cards:
            errors.append("No valid cards found in deck text")
            return DeckImportResult(
                success=False,
                imported_count=0,
                failed_cards=failed_cards,
                errors=errors
            )
        
        # Get unique card names for batch lookup
        unique_card_names = list(set(card["name"] for card in parsed_cards))
        
        # Fetch all cards from Scryfall in parallel
        card_data_map = await scryfall_service.get_multiple_cards(unique_card_names, by_name=True)
        
        # Group cards by name to handle quantities properly
        cards_by_name = {}
        total_expected = 0
        for card in parsed_cards:
            card_name = card["name"]
            total_expected += card["quantity"]
            if card_name not in cards_by_name:
                cards_by_name[card_name] = 0
            cards_by_name[card_name] += card["quantity"]
        
        print(f"Total cards parsed: {total_expected}")
        print(f"Unique card names: {len(cards_by_name)}")
        print(f"Cards by name: {cards_by_name}")
        
        # Import cards
        for card_name, total_quantity in cards_by_name.items():
            card_data = card_data_map.get(card_name)
            if not card_data:
                failed_cards.append(card_name)
                print(f"Card not found in Scryfall: {card_name}")  # Debug logging
                continue
            
            try:
                from app.schemas.deck_card import DeckCardCreate
                deck_card_data = DeckCardCreate(
                    deck_id=deck_id,
                    card_scryfall_id=card_data.get("id"),
                    quantity=total_quantity,
                    is_commander=False  # Don't change commander when importing cards
                )
                
                await deck_service.add_card_to_deck(deck_id, deck_card_data, deck.owner_id)
                imported_count += total_quantity
                print(f"Successfully imported: {total_quantity}x {card_name}")
                
            except Exception as e:
                print(f"Error importing {card_name}: {str(e)}")
                failed_cards.append(f"{card_name}: {str(e)}")
        
        print(f"Final imported count: {imported_count}")
        print(f"Failed cards: {failed_cards}")
        
        return DeckImportResult(
            success=imported_count > 0,
            imported_count=imported_count,
            failed_cards=failed_cards,
            errors=errors
        )
        
    except Exception as e:
        print(f"Import error: {str(e)}")  # Debug print
        import traceback
        traceback.print_exc()  # Print full traceback
        errors.append(f"Error importing cards: {str(e)}")
        return DeckImportResult(
            success=False,
            imported_count=0,
            failed_cards=failed_cards,
            errors=errors
        )


@router.get("/decks/{deck_id}", response_model=DeckResponse)
async def get_deck(
    deck_id: int,
    deck: Deck = Depends(get_user_deck_or_404),
    deck_service: DeckService = Depends(get_deck_service)
):
    """Get a specific deck"""
    return await deck_service.get_deck(deck_id, deck.owner_id)





@router.post("/decks", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
async def create_deck(
    deck_data: DeckCreate,
    deck_service: DeckService = Depends(get_deck_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new deck"""
    return await deck_service.create_deck(deck_data, current_user.id)


@router.post("/simple_deck_import", response_model=SimpleImportResult, status_code=status.HTTP_201_CREATED)
async def simple_import_deck(
    request: SimpleDeckImport,
    deck_service: DeckService = Depends(get_deck_service),
    current_user: User = Depends(get_current_user)
):
    """Simple deck import using card names (auto-searches Scryfall)"""
    scryfall_service = get_scryfall_service()
    
    imported_cards = []
    failed_cards = []
    warnings = []
    errors = []
    
    try:
        # Get commander from Scryfall
        commander_data = await scryfall_service.get_card_by_name(request.commander)
        if not commander_data:
            errors.append(f"Commander '{request.commander}' not found")
            return SimpleImportResult(
                success=False,
                errors=errors,
                total_cards=0
            )
        
        # Validate commander is legendary creature
        validation = await scryfall_service.validate_commander(commander_data.get("id"))
        if not validation["valid"]:
            errors.append(f"Commander validation failed: {validation['reason']}")
            return SimpleImportResult(
                success=False,
                errors=errors,
                total_cards=0
            )
        
        # Create deck
        from app.schemas.deck import DeckCreate
        deck_create = DeckCreate(
            name=request.name,
            description=request.description,
            commander_scryfall_id=commander_data.get("id"),
            is_public=request.is_public
        )
        
        deck = await deck_service.create_deck(deck_create, current_user.id)
        
        # Add commander to imported cards
        imported_cards.append({
            "name": commander_data.get("name"),
            "scryfall_id": commander_data.get("id"),
            "quantity": 1,
            "is_commander": True
        })
        
        # Get all unique card names
        unique_card_names = list(set(request.cards))
        
        # Fetch all cards from Scryfall in parallel
        card_data_map = await scryfall_service.get_multiple_cards(unique_card_names, by_name=True)
        
        # Import cards
        total_imported = 1  # Commander
        for card_name in unique_card_names:
            quantity = request.cards.count(card_name)
            
            card_data = card_data_map.get(card_name)
            if not card_data:
                failed_cards.append({
                    "name": card_name,
                    "error": "Card not found"
                })
                continue
            
            try:
                # Add card to deck
                deck_service.deck_repo.add_card_to_deck(deck.id, card_data.get("id"), quantity, False)
                
                imported_cards.append({
                    "name": card_data.get("name"),
                    "scryfall_id": card_data.get("id"),
                    "quantity": quantity,
                    "is_commander": False
                })
                total_imported += quantity
            except Exception as e:
                failed_cards.append({
                    "name": card_name,
                    "error": str(e)
                })
        
        return SimpleImportResult(
            success=True,
            deck_id=deck.id,
            deck_name=deck.name,
            imported_cards=imported_cards,
            failed_cards=failed_cards,
            warnings=warnings,
            errors=errors,
            total_cards=total_imported
        )
        
    except Exception as e:
        errors.append(f"Error importing deck: {str(e)}")
        return SimpleImportResult(
            success=False,
            errors=errors,
            total_cards=0
        )


@router.post("/text-import", response_model=TextImportResult, status_code=status.HTTP_201_CREATED)
async def text_import_deck(
    request: TextDeckImport,
    deck_service: DeckService = Depends(get_deck_service),
    current_user: User = Depends(get_current_user)
):
    """Text deck import - parses raw decklist text"""
    scryfall_service = get_scryfall_service()
    
    imported_cards = []
    failed_cards = []
    warnings = []
    errors = []
    
    try:
        # Parse deck text - one card per line, format: "quantity cardname"
        lines = [line.strip() for line in request.deck_text.split('\n') if line.strip()]
        parsed_cards = []
        
        for line in lines:
            if not line:
                continue
            
            # Skip sideboard section
            if line.startswith("SIDEBOARD:") or line.startswith("SIDEBOARD"):
                break
                
            parts = line.split(' ', 1)
            if len(parts) >= 2:
                try:
                    quantity = int(parts[0])
                    card_name = ' '.join(parts[1:])
                    parsed_cards.append({"name": card_name, "quantity": quantity})
                except ValueError:
                    failed_cards.append({
                        "name": line,
                        "error": f"Invalid quantity format: {parts[0]}"
                    })
            else:
                # Default quantity 1 if just card name
                card_name = line.strip()
                parsed_cards.append({"name": card_name, "quantity": 1})
        
        if not parsed_cards:
            errors.append("No valid cards found in deck text")
            return TextImportResult(
                success=False,
                errors=errors,
                total_cards=0,
                parsed_cards=0
            )
        
        # Find commander (first card with quantity 1, or first card if no quantities)
        commander_card = None
        commander_name = None
        
        for card in parsed_cards:
            if card["quantity"] == 1:
                commander_card = card
                commander_name = card["name"]
                break
        
        if not commander_card:
            errors.append("No commander found (first card with quantity 1)")
            return TextImportResult(
                success=False,
                errors=errors,
                total_cards=0,
                parsed_cards=0
            )
        
        # Get commander from Scryfall
        commander_data = await scryfall_service.get_card_by_name(commander_name)
        if not commander_data:
            errors.append(f"Commander '{commander_name}' not found")
            return TextImportResult(
                success=False,
                errors=errors,
                total_cards=0,
                parsed_cards=0
            )
        
        # Validate commander is legendary creature
        validation = await scryfall_service.validate_commander(commander_data.get("id"))
        if not validation["valid"]:
            errors.append(f"Commander validation failed: {validation['reason']}")
            return TextImportResult(
                success=False,
                errors=errors,
                total_cards=0,
                parsed_cards=0
            )
        
        # Create deck
        from app.schemas.deck import DeckCreate
        deck_create = DeckCreate(
            name=request.name,
            description=request.description,
            commander_scryfall_id=commander_data.get("id"),
            is_public=request.is_public
        )
        
        deck = await deck_service.create_deck(deck_create, current_user.id)
        
        # Add commander to imported cards
        imported_cards.append({
            "name": commander_data.get("name"),
            "scryfall_id": commander_data.get("id"),
            "quantity": 1,
            "is_commander": True
        })
        
        # Get non-commander cards
        non_commander_cards = [card for card in parsed_cards if card["quantity"] != 1 or card["name"] != commander_name]
        unique_card_names = list(set(card["name"] for card in non_commander_cards))
        
        # Fetch all cards from Scryfall in parallel
        card_data_map = await scryfall_service.get_multiple_cards(unique_card_names, by_name=True)
        
        # Import cards
        total_imported = 1  # Commander
        for card in non_commander_cards:
            quantity = card["quantity"]
            card_name = card["name"]
            
            card_data = card_data_map.get(card_name)
            if not card_data:
                failed_cards.append({
                    "name": card_name,
                    "error": "Card not found"
                })
                continue
            
            try:
                # Add card to deck
                deck_service.deck_repo.add_card_to_deck(deck.id, card_data.get("id"), quantity, False)
                
                imported_cards.append({
                    "name": card_data.get("name"),
                    "scryfall_id": card_data.get("id"),
                    "quantity": quantity,
                    "is_commander": False
                })
                total_imported += quantity
            except Exception as e:
                failed_cards.append({
                    "name": card_name,
                    "error": str(e)
                })
        
        return TextImportResult(
            success=True,
            deck_id=deck.id,
            deck_name=deck.name,
            imported_cards=imported_cards,
            failed_cards=failed_cards,
            warnings=warnings,
            errors=errors,
            total_cards=total_imported,
            parsed_cards=len(parsed_cards)
        )
        
    except Exception as e:
        errors.append(f"Error importing deck: {str(e)}")
        return TextImportResult(
            success=False,
            errors=errors,
            total_cards=0,
            parsed_cards=0
        )
