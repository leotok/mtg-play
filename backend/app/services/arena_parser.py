import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ArenaCardEntry:
    name: str
    quantity: int
    is_commander: bool = False


class ArenaParser:
    """Parser for MTG Arena deck export format"""
    
    def __init__(self):
        # Pattern for regular cards: "1 Card Name"
        self.card_pattern = re.compile(r'^(\d+)\s+(.+)$')
        # Pattern for commander: "[Commander] Card Name"
        self.commander_pattern = re.compile(r'^\[Commander\]\s+(.+)$')
        # Pattern for sideboard (ignore for now)
        self.sideboard_pattern = re.compile(r'^\[Sideboard\]')
    
    def parse_deck_text(self, deck_text: str) -> Tuple[List[ArenaCardEntry], List[str]]:
        """
        Parse MTG Arena deck text format
        
        Args:
            deck_text: Raw text from Arena export
            
        Returns:
            Tuple of (cards_list, errors_list)
        """
        cards = []
        errors = []
        lines = deck_text.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Skip sideboard section
            if self.sideboard_pattern.match(line):
                break
            
            # Check for commander
            commander_match = self.commander_pattern.match(line)
            if commander_match:
                card_name = commander_match.group(1).strip()
                cards.append(ArenaCardEntry(
                    name=card_name,
                    quantity=1,
                    is_commander=True
                ))
                continue
            
            # Check for regular card
            card_match = self.card_pattern.match(line)
            if card_match:
                try:
                    quantity = int(card_match.group(1))
                    card_name = card_match.group(2).strip()
                    
                    if quantity <= 0:
                        errors.append(f"Line {line_num}: Invalid quantity {quantity} for card '{card_name}'")
                        continue
                    
                    cards.append(ArenaCardEntry(
                        name=card_name,
                        quantity=quantity,
                        is_commander=False
                    ))
                except ValueError:
                    errors.append(f"Line {line_num}: Invalid format '{line}'")
                continue
            
            # If no pattern matched, it's an error
            errors.append(f"Line {line_num}: Unrecognized format '{line}'")
        
        return cards, errors
    
    def find_commander(self, cards: List[ArenaCardEntry]) -> Optional[ArenaCardEntry]:
        """Find the commander in the card list"""
        commanders = [card for card in cards if card.is_commander]
        
        if len(commanders) > 1:
            return None  # Multiple commanders found
        elif len(commanders) == 1:
            return commanders[0]
        else:
            # No explicit commander marked, try to infer
            # For Commander format, there should be exactly one legendary creature
            # This will be validated later with Scryfall data
            return None
    
    def validate_basic_format(self, cards: List[ArenaCardEntry]) -> List[str]:
        """Basic validation of deck format"""
        errors = []
        
        if not cards:
            errors.append("Deck contains no cards")
            return errors
        
        # Check for commander
        commander = self.find_commander(cards)
        if not commander:
            errors.append("No commander found in deck")
        
        # Check total card count (excluding commander)
        non_commander_cards = [card for card in cards if not card.is_commander]
        total_cards = sum(card.quantity for card in non_commander_cards)
        
        if total_cards != 99:  # 99 + 1 commander = 100
            errors.append(f"Deck has {total_cards} main deck cards (should be 99)")
        
        return errors
    
    def parse_and_validate(self, deck_text: str) -> Dict[str, any]:
        """
        Parse deck text and perform basic validation
        
        Returns:
            Dict with parsed data and validation results
        """
        cards, parse_errors = self.parse_deck_text(deck_text)
        validation_errors = self.validate_basic_format(cards) if cards else ["No cards to validate"]
        
        commander = self.find_commander(cards)
        
        return {
            "cards": cards,
            "commander": commander,
            "parse_errors": parse_errors,
            "validation_errors": validation_errors,
            "is_valid": len(parse_errors) == 0 and len(validation_errors) == 0
        }


def test_arena_parser():
    """Test function to verify parser works correctly"""
    parser = ArenaParser()
    
    # Test deck text
    test_deck = """# Test Commander Deck
1 Lightning Bolt
4 Sol Ring
1 Command Tower
[Commander] Arcane Signet
2 Counterspell
"""
    
    result = parser.parse_and_validate(test_deck)
    
    print("Parsed cards:")
    for card in result["cards"]:
        print(f"  {card.quantity}x {card.name} {'(Commander)' if card.is_commander else ''}")
    
    print(f"\nCommander: {result['commander'].name if result['commander'] else 'None'}")
    print(f"Parse errors: {result['parse_errors']}")
    print(f"Validation errors: {result['validation_errors']}")
    print(f"Is valid: {result['is_valid']}")


if __name__ == "__main__":
    test_arena_parser()
