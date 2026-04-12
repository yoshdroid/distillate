from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

from distillate.config import GRID_HEIGHT, GRID_WIDTH


class Tile(IntEnum):
    EMPTY = 0
    WALL = 1
    SOURCE = 2
    DRAIN = 3


@dataclass(frozen=True)
class StageData:
    stage: "Stage"
    overrides: dict[str, int]


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


def load_stage_data(path: Path) -> StageData:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    map_lines = lines[:GRID_HEIGHT]
    if len(map_lines) != GRID_HEIGHT:
        raise ValueError(f"{path} does not contain {GRID_HEIGHT} stage rows")

    layout: list[list[int]] = []
    for line in map_lines:
        layout.append(_parse_stage_row(line, path))

    overrides: dict[str, int] = {}
    for line in lines[GRID_HEIGHT:]:
        parsed = _parse_stage_parameter(line)
        if parsed is None:
            continue
        key, value = parsed
        overrides[key] = value

    return StageData(stage=Stage.from_layout(layout), overrides=overrides)


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


def _parse_stage_row(line: str, path: Path) -> list[int]:
    if " " in line:
        values = [int(value) for value in line.split()]
    else:
        values = [int(char) for char in line]

    if len(values) != GRID_WIDTH:
        raise ValueError(f"{path} row has {len(values)} columns, expected {GRID_WIDTH}")
    return values


def _parse_stage_parameter(line: str) -> tuple[str, int] | None:
    # 将来フォーマットが増えてもよいよう、未解釈行は無視する。
    separators = ("=", ":", " ")
    for separator in separators:
        if separator not in line:
            continue
        key, value = line.split(separator, 1)
        key = key.strip().upper()
        value = value.strip()
        if key in {"MAX_WATER", "MAX_STRESS", "BLOCK_LIFE"} and value.isdecimal():
            return key, int(value)
    return None
