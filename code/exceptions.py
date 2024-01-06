class Impossible(Exception):
    """Exception raised when an action is impossible to be performed.

    The reason is given as the exception message.
    """
    
class ExitToMainMenu(Exception):
    """Can be raised to go back to main menu."""

class QuitWithoutSaving(SystemExit):
    """Can be raised to exit the game without automatically saving."""
    
class GameSystemError(Exception):
    """ Exception raised when something unexpected happens and the game system breaks. """