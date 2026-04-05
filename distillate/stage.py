from __future__ import annotations

from pathlib import Path
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

    @classmethod
    def from_file(cls, path: Path) -> "Stage":
        rows: list[list[int]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if " " in stripped:
                rows.append([int(value) for value in stripped.split()])
            else:
                rows.append([int(char) for char in stripped])
        return cls.from_layout(rows)

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


def find_stage_files(base_dir: Path, pattern: str) -> dict[int, Path]:
    stage_files: dict[int, Path] = {}
    for path in sorted(base_dir.glob(pattern)):
        stem = path.stem
        _, _, suffix = stem.partition("_")
        if not suffix.isdecimal():
            continue
        stage_number = int(suffix)
        if 1 <= stage_number <= 99:
            stage_files[stage_number] = path
    return stage_files
