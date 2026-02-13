from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from app.core.database import get_db

from app.models import Deck, DeckCard
from app.schemas.deck import DeckCreate, DeckUpdate, DeckResponse, DeckList
from app.schemas.deck_card import DeckCardCreate, DeckCardUpdate, DeckCardResponse
from app.services.deck_validator import DeckValidator
from app.services.scryfall import get_scryfall_service
from app.repositories import (
    DeckRepository,
    get_deck_repository
)


class DeckService:
    """Deck service with business logic, using repositories for data access"""
    
    def __init__(self, deck_repo: DeckRepository, scryfall_service):
        self.deck_repo = deck_repo
        self.scryfall_service = scryfall_service
        self.validator = None  # Will be set when needed
    
    @classmethod
    def create_with_repositories(cls, db_session):
        """Factory method to create service with repositories"""
        deck_repo = DeckRepository(db_session)
        scryfall_service = get_scryfall_service()
        return cls(deck_repo, scryfall_service)
    
    def set_validator(self, db_session):
        """Set validator when database session is available"""
        self.validator = DeckValidator.create_with_repositories(db_session)
    
    async def create_deck(self, deck_data: DeckCreate, owner_id: int) -> DeckResponse:
        """Create a new deck"""
        # Verify commander exists and is valid
        validation = await self.scryfall_service.validate_commander(deck_data.commander_scryfall_id)
        if not validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation["reason"]
            )

        # Create deck
        deck_data_dict = {
            "name": deck_data.name,
            "description": deck_data.description,
            "commander_scryfall_id": deck_data.commander_scryfall_id,
            "owner_id": owner_id,
            "is_public": deck_data.is_public
        }
        
        deck = self.deck_repo.create(deck_data_dict)

        # Add commander as deck card
        self.deck_repo.add_card_to_deck(deck.id, deck_data.commander_scryfall_id, 1, True)

        return await self._get_deck_response(deck.id)

    async def get_deck(self, deck_id: int, owner_id: int) -> DeckResponse:
        """Get a specific deck"""
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        # Check ownership or public access
        if deck.owner_id != owner_id and not deck.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't own this deck"
            )
        
        return await self._get_deck_response(deck_id)

    async def get_user_decks(self, owner_id: int, skip: int = 0, limit: int = 100) -> List[DeckList]:
        """Get all decks for a user"""
        decks = self.deck_repo.get_user_decks(owner_id, skip, limit)
        return [await self._deck_to_deck_list(deck) for deck in decks]

    async def update_deck(self, deck_id: int, deck_update: DeckUpdate, owner_id: int) -> DeckResponse:
        """Update a deck"""
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        # Check ownership
        if deck.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't own this deck"
            )
        
        # Validate commander if being updated
        if deck_update.commander_scryfall_id and deck_update.commander_scryfall_id != deck.commander_scryfall_id:
            validation = await self.scryfall_service.validate_commander(deck_update.commander_scryfall_id)
            if not validation["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=validation["reason"]
                )
        
        update_data = deck_update.model_dump(exclude_unset=True)
        updated_deck = self.deck_repo.update(deck, update_data)
        return await self._get_deck_response(updated_deck.id)

    async def delete_deck(self, deck_id: int, owner_id: int) -> bool:
        """Delete a deck"""
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        # Check ownership
        if deck.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't own this deck"
            )
        
        return self.deck_repo.delete(deck_id) is not None

    async def get_deck_cards(self, deck_id: int, owner_id: int) -> List[DeckCardResponse]:
        """Get all cards in a deck"""
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        # Check ownership or public access
        if deck.owner_id != owner_id and not deck.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't own this deck"
            )
        
        deck_cards = self.deck_repo.get_deck_cards(deck_id)
        response_cards = []
        for card in deck_cards:
            response_card = await self._deck_card_to_response(card)
            response_cards.append(response_card)
        return response_cards

    async def add_card_to_deck(self, deck_id: int, card_data: DeckCardCreate, owner_id: int) -> DeckCardResponse:
        """Add a card to a deck"""
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        # Check ownership
        if deck.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't own this deck"
            )
        
        # Verify card exists in Scryfall
        card_data_api = await self.scryfall_service.get_card_by_scryfall_id(card_data.card_scryfall_id)
        if not card_data_api:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        deck_card = self.deck_repo.add_card_to_deck(
            deck_id,
            card_data.card_scryfall_id,
            card_data.quantity,
            card_data.is_commander
        )
        
        return await self._deck_card_to_response(deck_card)

    async def update_card_in_deck(self, deck_id: int, deck_card_id: int, card_data: DeckCardUpdate, owner_id: int) -> DeckCardResponse:
        """Update a card in a deck (deck_card_id is the DeckCard primary key)"""
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        # Check ownership
        if deck.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't own this deck"
            )
        
        existing = self.deck_repo.get_deck_card_by_id(deck_id, deck_card_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found in deck"
            )
        quantity = card_data.quantity if card_data.quantity is not None else existing.quantity
        is_commander = card_data.is_commander if card_data.is_commander is not None else existing.is_commander
        
        deck_card = self.deck_repo.update_card_in_deck_by_id(
            deck_id,
            deck_card_id,
            quantity,
            is_commander
        )
        
        if not deck_card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found in deck"
            )
        
        return await self._deck_card_to_response(deck_card)

    def remove_card_from_deck(self, deck_id: int, deck_card_id: int, owner_id: int) -> bool:
        """Remove a card from a deck (deck_card_id is the DeckCard primary key)"""
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        # Check ownership
        if deck.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't own this deck"
            )
        
        return self.deck_repo.remove_card_from_deck_by_id(deck_id, deck_card_id)

    def validate_deck(self, deck_id: int, owner_id: int) -> dict:
        """Validate a deck against Commander format rules"""
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        # Check ownership or public access
        if deck.owner_id != owner_id and not deck.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't own this deck"
            )
        
        # Use validator if available
        if self.validator:
            return self.validator.validate_deck(deck_id)
        
        # Basic validation if validator not available
        cards = self.deck_repo.get_deck_cards(deck_id)
        commander_cards = [c for c in cards if c.is_commander]
        
        if len(commander_cards) != 1:
            return {
                "is_valid": False,
                "validation_errors": ["Deck must have exactly one commander"]
            }
        
        return {
            "is_valid": True,
            "validation_errors": []
        }

    def get_deck_stats(self, deck_id: int, owner_id: int) -> dict:
        """Get deck statistics"""
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        # Check ownership or public access
        if deck.owner_id != owner_id and not deck.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't own this deck"
            )
        
        return self.deck_repo.get_deck_statistics(deck_id)

    async def export_deck(self, deck_id: int, owner_id: int) -> dict:
        """Export deck in JSON format"""
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        # Check ownership or public access
        if deck.owner_id != owner_id and not deck.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't own this deck"
            )
        
        deck_cards = self.deck_repo.get_deck_cards(deck_id)
        card_scryfall_ids = [dc.card_scryfall_id for dc in deck_cards]
        card_details = await self.scryfall_service.get_multiple_cards(card_scryfall_ids, by_name=False)
        
        exported_cards = []
        for deck_card in deck_cards:
            card_data = card_details.get(deck_card.card_scryfall_id)
            if card_data:
                exported_cards.append({
                    "scryfall_id": deck_card.card_scryfall_id,
                    "name": card_data.get("name"),
                    "quantity": deck_card.quantity,
                    "is_commander": deck_card.is_commander
                })
        
        return {
            "name": deck.name,
            "description": deck.description,
            "commander_scryfall_id": deck.commander_scryfall_id,
            "is_public": deck.is_public,
            "created_at": deck.created_at.isoformat() if deck.created_at else None,
            "cards": exported_cards
        }

    async def import_deck(self, import_data, owner_id: int) -> dict:
        """Import a deck from various formats"""
        if import_data.format == "json":
            return await self._import_json_deck(import_data.json_data, owner_id)
        elif import_data.format == "arena":
            return await self._import_arena_deck(import_data.arena_data, owner_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported import format: {import_data.format}"
            )

    async def _import_json_deck(self, json_data, owner_id: int) -> dict:
        """Import deck from JSON format using Scryfall"""
        # Verify commander exists in Scryfall
        commander_data = await self.scryfall_service.get_card_by_scryfall_id(json_data.commander_scryfall_id)
        if not commander_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Commander card not found"
            )
        
        validation = await self.scryfall_service.validate_commander(json_data.commander_scryfall_id)
        if not validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation["reason"]
            )
        
        # Create deck
        deck_data = {
            "name": json_data.name,
            "description": json_data.description or "",
            "commander_scryfall_id": json_data.commander_scryfall_id,
            "owner_id": owner_id,
            "is_public": getattr(json_data, "is_public", False)
        }
        
        deck = self.deck_repo.create(deck_data)
        self.deck_repo.add_card_to_deck(deck.id, json_data.commander_scryfall_id, 1, True)
        
        # Import cards
        imported_cards = []
        failed_cards = []
        
        for card_data in json_data.cards:
            try:
                card_api_data = await self.scryfall_service.get_card_by_scryfall_id(card_data.scryfall_id)
                if not card_api_data:
                    failed_cards.append({
                        "scryfall_id": card_data.scryfall_id,
                        "error": "Card not found"
                    })
                    continue
                
                self.deck_repo.add_card_to_deck(
                    deck.id,
                    card_data.scryfall_id,
                    card_data.quantity,
                    card_data.is_commander
                )
                
                imported_cards.append({
                    "scryfall_id": card_data.scryfall_id,
                    "name": card_api_data.get("name"),
                    "quantity": card_data.quantity
                })
                
            except Exception as e:
                failed_cards.append({
                    "scryfall_id": getattr(card_data, "scryfall_id", str(card_data)),
                    "error": str(e)
                })
        
        return {
            "deck_id": deck.id,
            "imported_cards": imported_cards,
            "failed_cards": failed_cards
        }

    async def _import_arena_deck(self, arena_data, owner_id: int) -> dict:
        """Import deck from MTG Arena format"""
        # This would need to be implemented based on Arena format parsing
        # For now, return a placeholder
        return {
            "deck_id": None,
            "imported_cards": [],
            "failed_cards": [],
            "error": "Arena format import not yet implemented"
        }

    # Helper methods
    async def _get_deck_response(self, deck_id: int) -> DeckResponse:
        """Helper method to build deck response"""
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        cards = self.deck_repo.get_deck_cards(deck_id)
        card_scryfall_ids = [str(card.card_scryfall_id) for card in cards]
        
        # Also fetch commander details if not already in the list
        commander_id = str(deck.commander_scryfall_id) if deck.commander_scryfall_id else None
        if commander_id and commander_id not in card_scryfall_ids:
            card_scryfall_ids.append(commander_id)
        
        # Fetch card details from Scryfall API
        card_details = await self.scryfall_service.get_multiple_cards(card_scryfall_ids, by_name=False)
        print(f"DEBUG: card_scryfall_ids = {card_scryfall_ids[:3]}")
        print(f"DEBUG: card_details keys = {list(card_details.keys())[:3]}")
        
        deck_cards = []
        for deck_card in cards:
            card_id = str(deck_card.card_scryfall_id)
            print(f"DEBUG: looking for {card_id} in card_details")
            card_data = card_details.get(card_id)
            if card_data:
                print(f"DEBUG: found card_data with power={card_data.get('power')}")
                # Handle cards with card_faces (transform, modal dfc, etc.)
                image_uris = card_data.get("image_uris")
                card_faces = None
                if card_data.get("card_faces"):
                    faces = []
                    for face in card_data["card_faces"]:
                        faces.append({
                            "name": face.get("name"),
                            "mana_cost": face.get("mana_cost"),
                            "type_line": face.get("type_line"),
                            "oracle_text": face.get("oracle_text"),
                            "power": face.get("power"),
                            "toughness": face.get("toughness"),
                            "image_uris": face.get("image_uris")
                        })
                    card_faces = faces
                    if not image_uris:
                        image_uris = card_data["card_faces"][0].get("image_uris")
                
                deck_cards.append({
                    "id": deck_card.id,
                    "card_scryfall_id": deck_card.card_scryfall_id,
                    "quantity": deck_card.quantity,
                    "is_commander": deck_card.is_commander,
                    "card_name": card_data.get("name"),
                    "name": card_data.get("name"),
                    "mana_cost": card_data.get("mana_cost"),
                    "cmc": card_data.get("cmc"),
                    "type_line": card_data.get("type_line"),
                    "colors": card_data.get("colors"),
                    "color_identity": card_data.get("color_identity"),
                    "rarity": card_data.get("rarity"),
                    "set": card_data.get("set"),
                    "power": card_data.get("power"),
                    "toughness": card_data.get("toughness"),
                    "keywords": card_data.get("keywords"),
                    "oracle_text": card_data.get("oracle_text"),
                    "image_uris": image_uris,
                    "card_faces": card_faces
                })
        
        # Get commander details
        commander_scryfall_id = str(deck.commander_scryfall_id) if deck.commander_scryfall_id else None
        commander_data = card_details.get(commander_scryfall_id) if commander_scryfall_id else None
        
        # Handle commander card_faces (transform cards)
        commander_image_uris = None
        if commander_data:
            commander_image_uris = commander_data.get("image_uris")
            if not commander_image_uris and commander_data.get("card_faces"):
                first_face = commander_data["card_faces"][0]
                commander_image_uris = first_face.get("image_uris")
        
        return DeckResponse(
            id=deck.id,
            name=deck.name,
            description=deck.description,
            commander_scryfall_id=deck.commander_scryfall_id,
            owner_id=deck.owner_id,
            is_public=deck.is_public,
            created_at=deck.created_at,
            updated_at=deck.updated_at,
            cards=deck_cards,
            commander={
                "scryfall_id": commander_data.get("id"),
                "name": commander_data.get("name"),
                "mana_cost": commander_data.get("mana_cost"),
                "cmc": commander_data.get("cmc"),
                "type_line": commander_data.get("type_line"),
                "colors": commander_data.get("colors"),
                "color_identity": commander_data.get("color_identity"),
                "image_uris": commander_image_uris
            } if commander_data else None
        )

    async def _deck_to_deck_list(self, deck: Deck) -> DeckList:
        """Helper method to convert deck to deck list format"""
        commander_data = await self.scryfall_service.get_card_by_scryfall_id(deck.commander_scryfall_id) if deck.commander_scryfall_id else None
        
        commander_image_uris = None
        color_identity = None
        if commander_data:
            commander_image_uris = commander_data.get("image_uris")
            if not commander_image_uris and commander_data.get("card_faces"):
                commander_image_uris = commander_data["card_faces"][0].get("image_uris")
            color_identity = commander_data.get("color_identity")
        
        return DeckList(
            id=deck.id,
            name=deck.name,
            description=deck.description,
            commander_scryfall_id=deck.commander_scryfall_id,
            is_public=deck.is_public,
            created_at=deck.created_at,
            commander={
                "scryfall_id": commander_data.get("id"),
                "name": commander_data.get("name"),
                "mana_cost": commander_data.get("mana_cost"),
                "cmc": commander_data.get("cmc"),
                "type_line": commander_data.get("type_line"),
                "colors": commander_data.get("colors"),
                "color_identity": commander_data.get("color_identity")
            } if commander_data else None,
            commander_image_uris=commander_image_uris,
            color_identity=color_identity
        )

    async def _deck_card_to_response(self, deck_card: DeckCard) -> DeckCardResponse:
        """Helper method to convert deck card to response format"""
        print(f"Converting deck card: {deck_card.card_scryfall_id}")  # Debug
        
        # Force fresh fetch by bypassing cache temporarily
        card_data = await self.scryfall_service.get_card_by_scryfall_id(deck_card.card_scryfall_id)
        
        if not card_data:
            print(f"No card data found for: {deck_card.card_scryfall_id}")  # Debug
            return DeckCardResponse(
                id=deck_card.id,
                card_scryfall_id=deck_card.card_scryfall_id,
                quantity=deck_card.quantity,
                is_commander=deck_card.is_commander,
                card_name="Unknown",
                name="Unknown"
            )
        
        print(f"Card found: {card_data.get('name')}, has images: {'image_uris' in card_data}")  # Debug
        if 'image_uris' in card_data:
            print(f"Image URIs: {card_data['image_uris']}")  # Debug
        
        return DeckCardResponse(
            id=deck_card.id,
            card_scryfall_id=deck_card.card_scryfall_id,
            quantity=deck_card.quantity,
            is_commander=deck_card.is_commander,
            card_name=card_data.get("name"),
            name=card_data.get("name"),  # Keep for backward compatibility
            mana_cost=card_data.get("mana_cost"),
            cmc=card_data.get("cmc"),
            type_line=card_data.get("type_line"),
            colors=card_data.get("colors"),
            color_identity=card_data.get("color_identity"),
            rarity=card_data.get("rarity"),
            set=card_data.get("set"),
            power=card_data.get("power"),
            toughness=card_data.get("toughness"),
            keywords=card_data.get("keywords"),
            oracle_text=card_data.get("oracle_text"),
            image_uris=card_data.get("image_uris")
        )


# Dependency injection function
def get_deck_service(db: Session = Depends(get_db)) -> DeckService:
    """Get deck service instance with repositories"""
    service = DeckService.create_with_repositories(db)
    service.set_validator(db)
    return service
