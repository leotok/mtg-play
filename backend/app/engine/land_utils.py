import re
from typing import Optional, Set

from app.engine.models import ManaColor


TRIGAME_NAMES = set()

COLOR_MAP = {
    'w': ManaColor.WHITE,
    'u': ManaColor.BLUE,
    'b': ManaColor.BLACK,
    'r': ManaColor.RED,
    'g': ManaColor.GREEN,
}


def get_land_colors(
    type_line: Optional[str],
    name: Optional[str],
    oracle_text: Optional[str] = None,
) -> Set[ManaColor]:
    """Get the colors a land can produce.
    
    Args:
        type_line: The card's type line (e.g., "Land — Swamp Mountain")
        name: The card's name (e.g., "Haunted Ridge")
        oracle_text: The card's oracle text (e.g., "Tap: Add {B} or {R}.")
    
    Returns:
        Set of ManaColor values the land can produce.
    """
    colors: Set[ManaColor] = set()
    
    type_lower = type_line.lower() if type_line else ""
    name_lower = name.lower() if name else ""
    oracle_lower = oracle_text.lower() if oracle_text else ""
    
    if "plains" in type_lower:
        colors.add(ManaColor.WHITE)
    if "island" in type_lower:
        colors.add(ManaColor.BLUE)
    if "swamp" in type_lower:
        colors.add(ManaColor.BLACK)
    if "mountain" in type_lower:
        colors.add(ManaColor.RED)
    if "forest" in type_lower:
        colors.add(ManaColor.GREEN)
    
    if not colors and oracle_text:
        hybrid_pattern = r'\{([WUBRG])\}.*?or.*?\{([WUBRG])\}'
        matches = re.findall(hybrid_pattern, oracle_lower, re.IGNORECASE)
        for match in matches:
            for color_char in match:
                if color_char.lower() in COLOR_MAP:
                    colors.add(COLOR_MAP[color_char.lower()])
    
    if not colors and oracle_text:
        single_color_pattern = r'add+d?\s*\{([WUBRG])\}'
        matches = re.findall(single_color_pattern, oracle_lower, re.IGNORECASE)
        for match in matches:
            if match.lower() in COLOR_MAP:
                colors.add(COLOR_MAP[match.lower()])
    
    if name_lower in TRIGAME_NAMES or "triome" in name_lower:
        colors.add(ManaColor.COLORLESS)
    
    if not colors:
        colors.add(ManaColor.COLORLESS)
    
    return colors


def is_hybrid_land(type_line: Optional[str], name: Optional[str], oracle_text: Optional[str] = None) -> bool:
    """Check if a land is a hybrid land (produces more than one color).
    
    Args:
        type_line: The card's type line
        name: The card's name
        oracle_text: The card's oracle text
    
    Returns:
        True if the land can produce more than one color.
    """
    colors = get_land_colors(type_line, name, oracle_text)
    return len(colors) > 1
