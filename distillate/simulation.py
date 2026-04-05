from __future__ import annotations

import random
from dataclasses import dataclass, field

from distillate.models import TempBlock, WaterParticle
from distillate.stage import Stage


@dataclass
class SimulationConfig:
    block_life: int
    water_speed: int
    max_water: int
    reset_cooldown_frames: int
    random_seed: int = 0


@dataclass
class SimulationState:
    stage: Stage
    config: SimulationConfig
    blocks: dict[tuple[int, int], TempBlock] = field(default_factory=dict)
    waters: dict[tuple[int, int], WaterParticle] = field(default_factory=dict)
    frame_count: int = 0
    cooldown_frames: int = 0
    randomizer: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self.randomizer = random.Random(self.config.random_seed)

    def place_block(self, x: int, y: int) -> bool:
        if not self.stage.is_passable(x, y):
            return False
        coord = (x, y)
        if coord in self.blocks or coord in self.waters:
            return False
        self.blocks[coord] = TempBlock(x=x, y=y, life=self.config.block_life, max_life=self.config.block_life)
        return True

    def place_blocks(self, coords: list[tuple[int, int]]) -> None:
        for x, y in coords:
            if self.stage.is_inside(x, y):
                self.place_block(x, y)

    def clear_waters(self) -> None:
        self.waters.clear()

    def trigger_water_reset(self) -> None:
        self.clear_waters()
        self.cooldown_frames = self.config.reset_cooldown_frames

    def tick(self, reset_water: bool = False) -> None:
        self.frame_count += 1
        self._tick_blocks()

        if reset_water:
            self.trigger_water_reset()
            return

        if self.cooldown_frames > 0:
            self.cooldown_frames -= 1
            return

        if self.frame_count % self.config.water_speed != 0:
            return

        self._remove_drained_water()
        self._spawn_water()
        self._move_water()

    def _tick_blocks(self) -> None:
        expired = [coord for coord, block in self.blocks.items() if not block.tick()]
        for coord in expired:
            del self.blocks[coord]

    def _remove_drained_water(self) -> None:
        drained: set[tuple[int, int]] = set()
        for drain_x, drain_y in self.stage.drain_positions():
            for x, y in _neighbors4(drain_x, drain_y):
                if (x, y) in self.waters:
                    drained.add((x, y))
        for coord in drained:
            del self.waters[coord]

    def _spawn_water(self) -> None:
        for source_x, source_y in self.stage.source_positions():
            if len(self.waters) >= self.config.max_water:
                return
            coord = (source_x, source_y)
            if coord in self.waters:
                continue
            self.waters[coord] = WaterParticle(x=source_x, y=source_y)

    def _move_water(self) -> None:
        remaining = dict(sorted(self.waters.items(), key=lambda item: (item[0][1], item[0][0])))
        next_waters: dict[tuple[int, int], WaterParticle] = {}

        while remaining:
            coord = next(iter(remaining))
            particle = remaining.pop(coord)
            target = self._choose_water_target(particle, remaining, next_waters)
            particle.x, particle.y = target
            next_waters[target] = particle

        self.waters = next_waters

    def _choose_water_target(
        self,
        particle: WaterParticle,
        remaining: dict[tuple[int, int], WaterParticle],
        next_waters: dict[tuple[int, int], WaterParticle],
    ) -> tuple[int, int]:
        x, y = particle.pos
        down = (x, y + 1)

        if self._is_open_for_water(down, remaining, next_waters):
            return down

        if particle.horizontal_preference == 0:
            particle.horizontal_preference = self.randomizer.choice((-1, 1))

        sideways = [
            (x + particle.horizontal_preference, y),
            (x - particle.horizontal_preference, y),
        ]
        for target in sideways:
            if self._is_open_for_water(target, remaining, next_waters):
                return target

        return x, y

    def _is_open_for_water(
        self,
        coord: tuple[int, int],
        remaining: dict[tuple[int, int], WaterParticle],
        next_waters: dict[tuple[int, int], WaterParticle],
    ) -> bool:
        x, y = coord
        if not self.stage.is_passable(x, y):
            return False
        if coord in self.blocks:
            return False
        if coord in remaining:
            return False
        if coord in next_waters:
            return False
        return True


def _neighbors4(x: int, y: int) -> tuple[tuple[int, int], ...]:
    return ((x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y))
