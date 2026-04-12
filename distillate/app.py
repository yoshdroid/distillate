from __future__ import annotations

from pathlib import Path

import pyxel

from distillate.config import (
    DEBUG_MODE,
    CLEAR_RATE,
    DEFAULT_STAGE_NUMBER,
    ENABLE_DIAGONAL_FALL,
    GRID_HEIGHT,
    GRID_WIDTH,
    LATERAL_FLOW_SEARCH_DEPTH,
    MAX_WATER,
    MAX_STRESS,
    RANDOM_SEED,
    RESET_COOLDOWN_FRAMES,
    SIZE_UNIT,
    STAGE_DIRECTORY,
    STAGE_FILE_GLOB,
    STAGE_GOAL,
    UPWARD_SPLASH_CHANCE,
    WATER_SPEED,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    BLOCK_LIFE,
)
from distillate.input import bresenham_line
from distillate.renderer import Renderer
from distillate.simulation import SimulationConfig, SimulationState
from distillate.stage import find_stage_files, load_stage_data


class Scene:
    TITLE = "title"
    GAME = "game"


class DistillateApp:
    def __init__(self) -> None:
        self.base_dir = Path.cwd()
        self.stage_dir = self.base_dir / STAGE_DIRECTORY
        self.stage_files = find_stage_files(self.stage_dir, STAGE_FILE_GLOB)
        if not self.stage_files:
            raise FileNotFoundError(f"No stage files matched {STAGE_FILE_GLOB!r} in {self.stage_dir}")

        self.simulation_config = SimulationConfig(
            block_life=BLOCK_LIFE,
            water_speed=WATER_SPEED,
            max_water=MAX_WATER,
            max_stress=MAX_STRESS,
            lateral_flow_search_depth=LATERAL_FLOW_SEARCH_DEPTH,
            enable_diagonal_fall=ENABLE_DIAGONAL_FALL,
            upward_splash_chance=UPWARD_SPLASH_CHANCE,
            reset_cooldown_frames=RESET_COOLDOWN_FRAMES,
            random_seed=RANDOM_SEED,
            stage_goal=STAGE_GOAL,
            clear_rate=CLEAR_RATE,
        )
        self.available_stages = sorted(self.stage_files)
        self.selected_stage = DEFAULT_STAGE_NUMBER if DEFAULT_STAGE_NUMBER in self.stage_files else self.available_stages[0]
        self.current_stage_number = self.selected_stage
        self.scene = Scene.TITLE
        self.state: SimulationState | None = None
        self.renderer = Renderer(debug_mode=DEBUG_MODE)
        self.dragging = False
        self.previous_cell = (0, 0)

    def run(self) -> None:
        pyxel.init(WINDOW_WIDTH, WINDOW_HEIGHT, title="Distillate")
        pyxel.mouse(True)
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        if self.scene == Scene.TITLE:
            self._update_title()
        else:
            self._update_game()

    def draw(self) -> None:
        if self.scene == Scene.TITLE:
            self.renderer.draw_title(self.selected_stage, self.available_stages)
            return

        if self.state is not None:
            self.renderer.draw_game(self.state, self.current_stage_number)

    def _update_title(self) -> None:
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        if pyxel.btnp(pyxel.KEY_LEFT):
            self._select_adjacent_stage(-1)
        elif pyxel.btnp(pyxel.KEY_RIGHT):
            self._select_adjacent_stage(1)

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self._start_game(self.selected_stage)

    def _update_game(self) -> None:
        if pyxel.btnp(pyxel.KEY_Q):
            self.scene = Scene.TITLE
            self.dragging = False
            return

        if self.state is not None and self.state.cleared:
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.scene = Scene.TITLE
                self.dragging = False
            return

        current_cell = self._mouse_to_grid(pyxel.mouse_x, pyxel.mouse_y)
        if current_cell is None:
            self.dragging = False
        else:
            self._handle_block_input(current_cell)

        if self.state is not None:
            reset_water = pyxel.btnp(pyxel.KEY_W)
            self.state.tick(reset_water=reset_water)

        if current_cell is not None:
            self.previous_cell = current_cell

    def _start_game(self, stage_number: int) -> None:
        stage_path = self.stage_files[stage_number]
        stage_data = load_stage_data(stage_path)
        stage_config = SimulationConfig(
            block_life=stage_data.overrides.get("BLOCK_LIFE", self.simulation_config.block_life),
            water_speed=self.simulation_config.water_speed,
            max_water=stage_data.overrides.get("MAX_WATER", self.simulation_config.max_water),
            max_stress=stage_data.overrides.get("MAX_STRESS", self.simulation_config.max_stress),
            lateral_flow_search_depth=self.simulation_config.lateral_flow_search_depth,
            enable_diagonal_fall=self.simulation_config.enable_diagonal_fall,
            upward_splash_chance=self.simulation_config.upward_splash_chance,
            reset_cooldown_frames=self.simulation_config.reset_cooldown_frames,
            random_seed=self.simulation_config.random_seed,
            stage_goal=stage_data.overrides.get("STAGE_GOAL", self.simulation_config.stage_goal),
            clear_rate=stage_data.overrides.get("CLEAR_RATE", self.simulation_config.clear_rate),
        )
        self.state = SimulationState(stage=stage_data.stage, config=stage_config)
        self.current_stage_number = stage_number
        self.scene = Scene.GAME
        self.dragging = False
        self.previous_cell = (0, 0)

    def _select_adjacent_stage(self, direction: int) -> None:
        current_index = self.available_stages.index(self.selected_stage)
        next_index = (current_index + direction) % len(self.available_stages)
        self.selected_stage = self.available_stages[next_index]

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
