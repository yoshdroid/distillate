from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class Tile(IntEnum):
    EMPTY = 0
    WALL = 1
    SOURCE = 2
    DRAIN = 3


@dataclass(frozen=True)
class Stage:
    tiles: tuple[tuple[Tile, ...], ...]

    @classmethod
    def from_layout(cls, layout: list[list[int]]) -> "Stage":
        rows = tuple(tuple(Tile(value) for value in row) for row in layout)
        return cls(tiles=rows)

    @property
    def width(self) -> int:
        return len(self.tiles[0])

    @property
    def height(self) -> int:
        return len(self.tiles)

    def is_inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def tile_at(self, x: int, y: int) -> Tile:
        return self.tiles[y][x]

    def is_passable(self, x: int, y: int) -> bool:
        return self.is_inside(x, y) and self.tile_at(x, y) == Tile.EMPTY

    def source_positions(self) -> list[tuple[int, int]]:
        return self._positions_for(Tile.SOURCE)

    def drain_positions(self) -> list[tuple[int, int]]:
        return self._positions_for(Tile.DRAIN)

    def iter_tiles(self):
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                yield x, y, tile

    def _positions_for(self, target: Tile) -> list[tuple[int, int]]:
        positions: list[tuple[int, int]] = []
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                if tile == target:
                    positions.append((x, y))
        return positions
