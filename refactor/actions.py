from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sprite import Actor
    from engine import Engine


class Action:
    def __init__(self, actor: Actor, cost: int = 5) -> None:
        self.actor = actor
        self.cost = cost
        
    @property
    def engine(self) -> Engine:
        """ Return the engine this action belongs to. """
        return self.actor.gamemap.engine
    
    def perform(self) -> None:
        """Perform this action with the objects needed to determine its scope.

        `self.engine` is the scope this action is being performed in.

        `self.entity` is the object performing the action.

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()
    
    
class WaitAction(Action):
    def __init__(self, actor: Actor) -> None:
        super().__init__(actor, 0)
        
    def perform(self) -> None:
        pass