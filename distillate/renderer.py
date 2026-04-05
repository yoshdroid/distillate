from __future__ import annotations

import pyxel

from distillate.config import (
    C_BLUE,
    C_BROWN,
    C_GRAY,
    C_GREEN,
    C_PALE,
    C_RED,
    C_WHITE,
    C_YELLOW,
    GRID_HEIGHT,
    GRID_WIDTH,
    SIZE_UNIT,
)
from distillate.simulation import SimulationState
from distillate.stage import Tile


class Renderer:
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode

    def draw(self, state: SimulationState) -> None:
        pyxel.cls(0)
        self._draw_stage(state)
        self._draw_blocks(state)
        self._draw_waters(state)
        if self.debug_mode:
            self._draw_debug(state, 0, 0)

    def _draw_stage(self, state: SimulationState) -> None:
        for x, y, tile in state.stage.iter_tiles():
            dx = x * SIZE_UNIT
            dy = y * SIZE_UNIT
            if tile == Tile.WALL:
                pyxel.rect(dx, dy, SIZE_UNIT, SIZE_UNIT, C_BROWN)
            elif tile == Tile.SOURCE:
                pyxel.tri(dx + 1, dy + 2, dx + SIZE_UNIT - 1, dy + 2, dx + SIZE_UNIT // 2, dy + SIZE_UNIT - 2, C_YELLOW)
            elif tile == Tile.DRAIN:
                pyxel.tri(dx + 1, dy + 2, dx + SIZE_UNIT - 1, dy + 2, dx + SIZE_UNIT // 2, dy + SIZE_UNIT - 2, C_RED)

        for x in range(GRID_WIDTH + 1):
            pyxel.line(x * SIZE_UNIT, 0, x * SIZE_UNIT, GRID_HEIGHT * SIZE_UNIT, C_GREEN)
        for y in range(GRID_HEIGHT + 1):
            pyxel.line(0, y * SIZE_UNIT, GRID_WIDTH * SIZE_UNIT, y * SIZE_UNIT, C_GREEN)

    def _draw_blocks(self, state: SimulationState) -> None:
        for block in sorted(state.blocks.values(), key=lambda item: (item.y, item.x)):
            dx = block.x * SIZE_UNIT
            dy = block.y * SIZE_UNIT
            phase = block.animation_phase()
            color = C_GRAY
            if phase == 1:
                color = C_GRAY if pyxel.frame_count % 4 else C_PALE
            elif phase == 2:
                color = C_GRAY if pyxel.frame_count % 2 else C_WHITE
            pyxel.rect(dx, dy, SIZE_UNIT, SIZE_UNIT, color)

    def _draw_waters(self, state: SimulationState) -> None:
        for water in sorted(state.waters.values(), key=lambda item: (item.y, item.x)):
            dx = water.x * SIZE_UNIT
            dy = water.y * SIZE_UNIT
            pyxel.rect(dx, dy, SIZE_UNIT, SIZE_UNIT, C_BLUE)

    def _draw_debug(self, state: SimulationState, x: int, y: int) -> None:
        text = (
            f"Frame: {state.frame_count}\n"
            f"Mouse: ({pyxel.mouse_x},{pyxel.mouse_y})\n"
            f"Blocks: {len(state.blocks)}\n"
            f"Waters: {len(state.waters)}\n"
            f"Cooldown: {state.cooldown_frames}\n"
        )
        pyxel.text(x + 1, y, text, 4)
        pyxel.text(x, y, text, 9)
