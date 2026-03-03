class GameActionError(Exception):
    """Base exception for game action errors"""
    pass


class InvalidPhaseError(GameActionError):
    """Raised when an action is attempted in an invalid phase"""
    pass


class InvalidCardError(GameActionError):
    """Raised when a card doesn't exist or is in an invalid state"""
    pass


class InvalidPlayerError(GameActionError):
    """Raised when a player doesn't exist or isn't in the game"""
    pass


class InsufficientResourcesError(GameActionError):
    """Raised when a player doesn't have enough resources (mana, cards, etc.)"""
    pass


class InvalidZoneError(GameActionError):
    """Raised when a card is moved to or from an invalid zone"""
    pass


class InvalidTargetError(GameActionError):
    """Raised when a target is invalid"""
    pass


class GameNotInProgressError(GameActionError):
    """Raised when action requires game to be in progress"""
    pass


class NotYourTurnError(GameActionError):
    """Raised when a player tries to act when it's not their turn"""
    pass


class CardNotFoundError(GameActionError):
    """Raised when a card cannot be found"""
    pass


class EmptyLibraryError(GameActionError):
    """Raised when trying to draw from an empty library"""
    pass


class TooManyLandsError(GameActionError):
    """Raised when player tries to play more than 1 land per turn"""
    pass


class InvalidPhaseForLandError(GameActionError):
    """Raised when a land is played in an invalid phase"""
    pass
