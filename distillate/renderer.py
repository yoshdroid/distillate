from __future__ import annotations

import pyxel

from distillate.config import (
    C_BLACK,
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

    def draw_game(self, state: SimulationState, stage_number: int) -> None:
        pyxel.cls(0)
        self._draw_stage(state)
        self._draw_blocks(state)
        self._draw_waters(state)
        pyxel.text(4, 4, f"STAGE {stage_number}", C_WHITE)
        if state.config.stage_goal > 0:
            pyxel.text(64, 4, f"GOAL {state.goal_removed_total}/{state.config.stage_goal}", C_WHITE)
        if state.cleared:
            self._draw_clear_overlay(state)
        if self.debug_mode:
            self._draw_debug(state, 0, 10)

    def draw_title(self, selected_stage: int, available_stages: list[int]) -> None:
        pyxel.cls(C_BLACK)
        center_x = GRID_WIDTH * SIZE_UNIT // 2
        pyxel.text(center_x - 30, 28, "DISTILLATE", C_WHITE)
        pyxel.text(center_x - 54, 60, "LEFT/RIGHT: SELECT STAGE", C_YELLOW)
        pyxel.text(center_x - 47, 76, "LEFT CLICK: START GAME", C_YELLOW)
        pyxel.text(center_x - 46, 92, "S: SOUND TEST MODE", C_YELLOW)
        pyxel.text(center_x - 32, 108, "Q: QUIT PROGRAM", C_YELLOW)
        pyxel.text(center_x - 28, 126, f"SELECTED STAGE {selected_stage:02d}", C_WHITE)
        if available_stages:
            available = ", ".join(f"{stage:02d}" for stage in available_stages)
            pyxel.text(12, 154, f"AVAILABLE: {available}", C_GRAY)
        else:
            pyxel.text(12, 154, "AVAILABLE: NONE", C_RED)

    def draw_sound_test(
        self,
        effect_names: list[str],
        selected_effect: int,
        bgm_names: list[str],
        selected_bgm: int,
        bgm_enabled: bool,
        current_bgm: str | None,
    ) -> None:
        pyxel.cls(C_BLACK)
        self._draw_grid()
        pyxel.text(82, 14, "SOUND TEST", C_WHITE)
        pyxel.text(18, 34, "UP/DOWN: SELECT EFFECT", C_YELLOW)
        pyxel.text(18, 44, "ENTER/SPACE: PLAY EFFECT", C_YELLOW)
        pyxel.text(18, 58, "LEFT/RIGHT: SELECT BGM", C_YELLOW)
        pyxel.text(18, 68, "B: BGM ON/OFF", C_YELLOW)
        pyxel.text(18, 82, "Q: RETURN TITLE", C_YELLOW)

        pyxel.text(18, 104, "EFFECTS", C_WHITE)
        for index, name in enumerate(effect_names):
            color = C_BLUE if index == selected_effect else C_GRAY
            pyxel.text(28, 116 + index * 10, name.upper(), color)

        pyxel.text(140, 104, "BGM", C_WHITE)
        for index, name in enumerate(bgm_names):
            color = C_BLUE if index == selected_bgm else C_GRAY
            pyxel.text(150, 116 + index * 10, name.upper(), color)

        bgm_status = "ON" if bgm_enabled else "OFF"
        bgm_color = C_BLUE if bgm_enabled else C_RED
        pyxel.text(140, 160, f"BGM SWITCH: {bgm_status}", bgm_color)
        now_playing = current_bgm.upper() if current_bgm is not None else "NONE"
        pyxel.text(18, 180, f"NOW PLAYING: {now_playing}", C_WHITE)

    def _draw_stage(self, state: SimulationState) -> None:
        for x, y, tile in state.stage.iter_tiles():
            dx = x * SIZE_UNIT
            dy = y * SIZE_UNIT
            if tile == Tile.WALL and state.has_static_wall((x, y)):
                pyxel.rect(dx, dy, SIZE_UNIT, SIZE_UNIT, C_BROWN)
            elif tile == Tile.SOURCE:
                pyxel.tri(dx + 1, dy + 2, dx + SIZE_UNIT - 1, dy + 2, dx + SIZE_UNIT // 2, dy + SIZE_UNIT - 2, C_YELLOW)
            elif tile == Tile.DRAIN:
                pyxel.tri(dx + 1, dy + 2, dx + SIZE_UNIT - 1, dy + 2, dx + SIZE_UNIT // 2, dy + SIZE_UNIT - 2, C_RED)
            elif tile == Tile.GOAL_DRAIN:
                pyxel.tri(dx + 1, dy + 2, dx + SIZE_UNIT - 1, dy + 2, dx + SIZE_UNIT // 2, dy + SIZE_UNIT - 2, C_BLUE)

        for x in range(GRID_WIDTH + 1):
            pyxel.line(x * SIZE_UNIT, 0, x * SIZE_UNIT, GRID_HEIGHT * SIZE_UNIT, C_GREEN)
        for y in range(GRID_HEIGHT + 1):
            pyxel.line(0, y * SIZE_UNIT, GRID_WIDTH * SIZE_UNIT, y * SIZE_UNIT, C_GREEN)

    def _draw_grid(self) -> None:
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
            pyxel.rect(dx, dy, SIZE_UNIT, SIZE_UNIT, C_RED if water.is_red else C_BLUE)

    def _draw_debug(self, state: SimulationState, x: int, y: int) -> None:
        text = (
            f"Frame: {state.frame_count}\n"
            f"Mouse: ({pyxel.mouse_x},{pyxel.mouse_y})\n"
            f"Blocks: {len(state.blocks)}\n"
            f"Waters: {len(state.waters)}\n"
            f"Red: {sum(1 for water in state.waters.values() if water.is_red)}\n"
            f"Goal Blue: {state.goal_removed_blue}\n"
            f"Goal Red: {state.goal_removed_red}\n"
            f"Cooldown: {state.cooldown_frames}\n"
        )
        pyxel.text(x + 1, y, text, 4)
        pyxel.text(x, y, text, 9)

    def _draw_clear_overlay(self, state: SimulationState) -> None:
        width = GRID_WIDTH * SIZE_UNIT
        height = GRID_HEIGHT * SIZE_UNIT
        box_x = 20
        box_y = 52
        box_w = width - 40
        box_h = 84
        pyxel.rect(box_x, box_y, box_w, box_h, C_BLACK)
        pyxel.rectb(box_x, box_y, box_w, box_h, C_WHITE)
        pyxel.text(box_x + 58, box_y + 12, "STAGE CLEAR", C_YELLOW)
        pyxel.text(box_x + 24, box_y + 30, f"GOAL DRAINED: {state.goal_removed_total}/{state.config.stage_goal}", C_WHITE)
        pyxel.text(box_x + 24, box_y + 44, f"BLUE RATE: {state.clear_percentage:.1f}%", C_WHITE)
        if state.is_true_clear:
            pyxel.text(box_x + 24, box_y + 58, "TRUE CLEAR", C_BLUE)
        else:
            pyxel.text(box_x + 24, box_y + 58, "CLEAR", C_RED)
        pyxel.text(box_x + 24, box_y + 72, "LEFT CLICK: RETURN TITLE", C_WHITE)
