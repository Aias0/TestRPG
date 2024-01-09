from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tile_types import Tile

class TileEffect():
    def __init__(self, tile: Tile) -> None:
        self.tile = tile
        
    def active(self, engine) -> None:
        pass