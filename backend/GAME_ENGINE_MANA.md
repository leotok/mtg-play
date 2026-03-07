# Game Engine Mana Rules

## Critical Distinction: Generic vs Colorless Mana

### Generic Mana (`{X}` where X is a number)
- Examples: `{1}`, `{2}`, `{3}`, `{4}`
- **Can be paid with ANY color of mana**: White, Blue, Black, Red, Green, OR Colorless
- Example: A spell costing `{1}{R}` means you need 1 red + 1 of any color

### Colorless Mana (`{C}`)
- Examples: `{C}`, `{C}{C}`
- **Can ONLY be paid by actual colorless-producing sources**
- In Magic, this is rare - primarily from:
  - Wastes (Basic Land - produces `{C}`)
  - Eldrazi landmarks
  - Some special cards

## Mana Cost Parsing

### Implementation
The `parse_mana_cost` function in `app/engine/models.py` parses MTG mana strings:

| Input | Output | Notes |
|-------|--------|-------|
| `{W}{W}{3}` | `WHITE: 2, generic: 3` | 2 white + 3 generic |
| `{1}{R}` | `generic: 1, RED: 1` | 1 generic + 1 red |
| `{C}` | `COLORLESS: 1` | 1 colorless (explicit) |
| `{3}{R}{R}` | `generic: 3, RED: 2` | 3 generic + 2 red |
| `{B/R}` | `([], [{BLACK, RED}])` | Hybrid - black OR red |

**Key**: The `generic` key represents numeric mana costs that can be paid with ANY color. The `ManaColor.COLORLESS` is only used for explicit `{C}` costs.

## Land Color Detection

### Basic Lands
- Plains → WHITE
- Island → BLUE  
- Swamp → BLACK
- Mountain → RED
- Forest → GREEN
- Wastes → COLORLESS (explicit)

### Dual Lands (Hybrid)
- Produce multiple colors (e.g., Black/Red from Blood Crypt)
- Do NOT produce colorless (unless they have explicit oracle text)

### Triomes
- Produce 3 colors + COLORLESS (e.g., Rau Triome produces W/U/R + C)

### Generic Lands
- Lands without basic types → Produce COLORLESS only (for explicit {C} costs)

## Mana Payment Logic

### For Colored Mana (`{W}`, `{U}`, `{B}`, `{R}`, `{G}`)
1. First, pay from player's mana pool
2. If insufficient, tap lands that PRODUCE that specific color
3. Only lands with that color in their production can be used

### For Generic Mana (`{1}`, `{2}`, etc.)
1. First, pay from player's mana pool (ANY color)
2. If insufficient, tap ANY untapped land (regardless of what colors it produces)
3. Generic can be paid with colored OR colorless mana

### For Colorless Mana (`{C}`)
1. First, pay from player's mana pool (must be colorless)
2. If insufficient, tap lands that PRODUCE COLORLESS specifically:
   - Wastes (Basic)
   - Triomes
   - Generic lands (no basic type)

## Code References

### Key Files
- `app/engine/models.py` - `parse_mana_cost()` function, `GENERIC_KEY` constant
- `app/engine/game_engine.py` - `_can_afford_mana()` method
- `app/engine/actions.py` - `tap_lands_for_mana()`, `can_produce_mana()`, `tap_lands_for_generic()`, `can_produce_generic()`

### Key Functions
| Function | Purpose |
|----------|---------|
| `parse_mana_cost()` | Parse mana cost string into components |
| `_can_afford_mana()` | Check if player can afford a spell |
| `can_produce_mana()` | Check if colored/colorless can be produced |
| `can_produce_generic()` | Check if generic can be produced (any land) |
| `tap_lands_for_mana()` | Actually tap lands for colored/colorless |
| `tap_lands_for_generic()` | Actually tap lands for generic mana |
| `get_land_colors()` | Determine what colors a land can produce |

## Common Mistakes to Avoid

1. **Treating generic as colorless**: Numbers in mana costs (`{1}`, `{2}`) are GENERIC, not COLORLESS
2. **Only using colorless-producing lands for generic**: Any land can produce generic mana
3. **Confusing `{C}` with numbers**: Only `{C}` produces colorless, not `{1}`, `{2}`, etc.
