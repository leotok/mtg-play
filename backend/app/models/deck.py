from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Deck(Base):
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    commander_scryfall_id = Column(String, nullable=False)  # No foreign key constraint
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="decks")
    cards = relationship("DeckCard", back_populates="deck", cascade="all, delete-orphan")


class DeckCard(Base):
    __tablename__ = "deck_cards"

    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(Integer, ForeignKey("decks.id"), nullable=False)
    card_scryfall_id = Column(String, nullable=False)  # No foreign key constraint
    quantity = Column(Integer, default=1)
    is_commander = Column(Boolean, default=False)
    
    # Relationships
    deck = relationship("Deck", back_populates="cards")
