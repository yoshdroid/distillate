from __future__ import annotations

import pyxel

from distillate.config import (
    DEBUG_MODE,
    GRID_HEIGHT,
    GRID_WIDTH,
    MAX_WATER,
    RANDOM_SEED,
    RESET_COOLDOWN_FRAMES,
    SIZE_UNIT,
    STAGE_LAYOUT,
    WATER_SPEED,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    BLOCK_LIFE,
)
from distillate.input import bresenham_line
from distillate.renderer import Renderer
from distillate.simulation import SimulationConfig, SimulationState
from distillate.stage import Stage


class DistillateApp:
    def __init__(self) -> None:
        stage = Stage.from_layout(STAGE_LAYOUT)
        config = SimulationConfig(
            block_life=BLOCK_LIFE,
            water_speed=WATER_SPEED,
            max_water=MAX_WATER,
            reset_cooldown_frames=RESET_COOLDOWN_FRAMES,
            random_seed=RANDOM_SEED,
        )
        self.state = SimulationState(stage=stage, config=config)
        self.renderer = Renderer(debug_mode=DEBUG_MODE)
        self.dragging = False
        self.previous_cell = (0, 0)

    def run(self) -> None:
        pyxel.init(WINDOW_WIDTH, WINDOW_HEIGHT, title="Distillate")
        pyxel.mouse(True)
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        current_cell = self._mouse_to_grid(pyxel.mouse_x, pyxel.mouse_y)
        if current_cell is None:
            self.dragging = False
        else:
            self._handle_block_input(current_cell)

        reset_water = pyxel.btnp(pyxel.KEY_W)
        self.state.tick(reset_water=reset_water)

        if current_cell is not None:
            self.previous_cell = current_cell

    def draw(self) -> None:
        self.renderer.draw(self.state)

    def _handle_block_input(self, current_cell: tuple[int, int]) -> None:
        if self.dragging and pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT):
            self.dragging = False

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.state.place_blocks([current_cell])
            self.dragging = True
        elif self.dragging and pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            self.state.place_blocks(bresenham_line(self.previous_cell, current_cell))
        elif not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            self.dragging = False

    def _mouse_to_grid(self, mouse_x: int, mouse_y: int) -> tuple[int, int] | None:
        grid_x = mouse_x // SIZE_UNIT
        grid_y = mouse_y // SIZE_UNIT
        if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
            return grid_x, grid_y
        return None
