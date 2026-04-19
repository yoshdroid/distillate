from __future__ import annotations

import random
from dataclasses import dataclass, field

from distillate.models import TempBlock, WaterParticle
from distillate.stage import Stage, Tile as StageTile


@dataclass
class SimulationConfig:
    block_life: int
    water_speed: int
    max_water: int
    max_stress: int
    lateral_flow_search_depth: int
    enable_diagonal_fall: bool
    upward_splash_chance: float
    initial_red_chance: float
    reset_cooldown_frames: int
    random_seed: int = 0
    stage_goal: int = 0
    clear_rate: float = 0.0


@dataclass
class SimulationState:
    stage: Stage
    config: SimulationConfig
    blocks: dict[tuple[int, int], TempBlock] = field(default_factory=dict)
    waters: dict[tuple[int, int], WaterParticle] = field(default_factory=dict)
    destroyed_walls: set[tuple[int, int]] = field(default_factory=set)
    frame_count: int = 0
    cooldown_frames: int = 0
    goal_removed_blue: int = 0
    goal_removed_red: int = 0
    cleared: bool = False
    sound_events: list[str] = field(default_factory=list)
    randomizer: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self.randomizer = random.Random(self.config.random_seed)

    def place_block(self, x: int, y: int) -> bool:
        x, y = self.normalize_coord((x, y))
        if not self.is_passable_cell((x, y)):
            return False
        coord = (x, y)
        if coord in self.blocks or coord in self.waters:
            return False
        self.blocks[coord] = TempBlock(x=x, y=y, life=self.config.block_life, max_life=self.config.block_life)
        return True

    def place_blocks(self, coords: list[tuple[int, int]]) -> int:
        placed = 0
        for x, y in coords:
            if self.stage.is_inside(x, y):
                placed += int(self.place_block(x, y))
        return placed

    def break_wall_at(self, x: int, y: int) -> bool:
        coord = self.normalize_coord((x, y))
        if coord in self.blocks:
            del self.blocks[coord]
            return True
        if self.has_static_wall(coord):
            self.destroyed_walls.add(coord)
            return True
        return False

    def clear_waters(self) -> None:
        self.waters.clear()

    def trigger_water_reset(self) -> None:
        self.clear_waters()
        self.blocks.clear()
        self.destroyed_walls.clear()
        self.cooldown_frames = self.config.reset_cooldown_frames

    def tick(self, reset_water: bool = False) -> None:
        self.sound_events.clear()
        if self.cleared:
            return

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
        drained: dict[tuple[int, int], bool] = {}
        normal_drain_happened = False
        goal_blue_happened = False
        goal_red_happened = False
        for drain_x, drain_y in self.stage.drain_positions():
            for x, y in self.neighbors4((drain_x, drain_y)):
                if (x, y) in self.waters:
                    drained[(x, y)] = False
        for drain_x, drain_y in self.stage.goal_drain_positions():
            for x, y in self.neighbors4((drain_x, drain_y)):
                if (x, y) in self.waters:
                    drained[(x, y)] = True

        for coord, counted_for_goal in drained.items():
            water = self.waters.get(coord)
            if water is None:
                continue
            if counted_for_goal:
                if water.is_red:
                    self.goal_removed_red += 1
                    goal_red_happened = True
                else:
                    self.goal_removed_blue += 1
                    goal_blue_happened = True
            else:
                normal_drain_happened = True
            del self.waters[coord]

        if goal_red_happened:
            self.sound_events.append("goal_red_drain")
        if goal_blue_happened:
            self.sound_events.append("goal_blue_drain")
        if normal_drain_happened:
            self.sound_events.append("normal_drain")

        if self.config.stage_goal > 0 and self.goal_removed_total >= self.config.stage_goal:
            self.cleared = True

    def consume_sound_events(self) -> list[str]:
        events = list(self.sound_events)
        self.sound_events.clear()
        return events

    def _spawn_water(self) -> None:
        for source_x, source_y in self.stage.source_positions():
            if len(self.waters) >= self.config.max_water:
                return
            coord = self.normalize_coord((source_x, source_y))
            if coord in self.waters:
                continue
            self.waters[coord] = self._create_spawned_water(source_x, source_y)

    def _create_spawned_water(self, x: int, y: int) -> WaterParticle:
        is_red = self.randomizer.random() < self.config.initial_red_chance
        initial_stress = 0
        if not is_red:
            initial_stress_limit = max(0, int(self.config.max_stress * 0.1))
            initial_stress = self.randomizer.randint(0, initial_stress_limit) if initial_stress_limit > 0 else 0
        return WaterParticle(x=x, y=y, stress=initial_stress, is_red=is_red)

    def _move_water(self) -> None:
        remaining = dict(sorted(self.waters.items(), key=lambda item: (item[0][1], item[0][0])))
        next_waters: dict[tuple[int, int], WaterParticle] = {}

        while remaining:
            coord = next(iter(remaining))
            particle = remaining.pop(coord)
            current_pos = particle.pos
            target = self._choose_water_target(particle, remaining, next_waters)
            particle.previous_pos = current_pos
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

        if particle.is_red:
            swapped = self._try_swap_red_water_upward(particle, remaining, next_waters)
            if swapped is not None:
                return swapped

        down = self.normalize_coord((x, y + 1))
        if self._is_open_for_water(down, remaining, next_waters):
            particle.reset_stress()
            return down

        if particle.horizontal_preference == 0:
            particle.horizontal_preference = self.randomizer.choice((-1, 1))

        sideways = self._prioritize_sideways_targets(
            particle,
            [
                self.normalize_coord((x + particle.horizontal_preference, y)),
                self.normalize_coord((x - particle.horizontal_preference, y)),
            ],
        )

        if self.config.enable_diagonal_fall:
            diagonal_target = self._find_diagonal_fall_target(x, y, remaining, next_waters, sideways)
            if diagonal_target is not None:
                particle.reset_stress()
                particle.horizontal_preference = self.horizontal_step(x, diagonal_target[0])
                return diagonal_target

        guided_target = self._find_guided_sideways_target(particle, remaining, next_waters, sideways)
        if guided_target is not None:
            particle.reset_stress()
            particle.horizontal_preference = self.horizontal_step(x, guided_target[0])
            return guided_target

        splash_target = self._find_upward_splash_target(x, y, remaining, next_waters, sideways)
        if splash_target is not None:
            particle.reset_stress()
            particle.horizontal_preference = self.horizontal_step(x, splash_target[0])
            return splash_target

        for target in sideways:
            if self._is_open_for_water(target, remaining, next_waters):
                particle.reset_stress()
                return target

        if not particle.is_red and all(not self._is_open_for_water(target, remaining, next_waters) for target in sideways):
            particle.add_stress(self.config.max_stress)

        return x, y

    def _prioritize_sideways_targets(
        self,
        particle: WaterParticle,
        targets: list[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        if particle.previous_pos is None:
            return targets

        forward_targets = [target for target in targets if target != particle.previous_pos]
        backtrack_targets = [target for target in targets if target == particle.previous_pos]
        return forward_targets + backtrack_targets

    def _find_diagonal_fall_target(
        self,
        x: int,
        y: int,
        remaining: dict[tuple[int, int], WaterParticle],
        next_waters: dict[tuple[int, int], WaterParticle],
        sideways: list[tuple[int, int]],
    ) -> tuple[int, int] | None:
        for side_x, side_y in sideways:
            diagonal = self.normalize_coord((side_x, side_y + 1))
            if self._is_open_for_water((side_x, side_y), remaining, next_waters) and self._is_open_for_water(
                diagonal,
                remaining,
                next_waters,
            ):
                return diagonal
        return None

    def _find_upward_splash_target(
        self,
        x: int,
        y: int,
        remaining: dict[tuple[int, int], WaterParticle],
        next_waters: dict[tuple[int, int], WaterParticle],
        sideways: list[tuple[int, int]],
    ) -> tuple[int, int] | None:
        if self.config.upward_splash_chance <= 0:
            return None

        for side_x, side_y in sideways:
            upward = self.normalize_coord((side_x, side_y - 1))
            if not self._is_open_for_water((side_x, side_y), remaining, next_waters):
                continue
            if not self._is_open_for_water(upward, remaining, next_waters):
                continue
            if self.randomizer.random() < self.config.upward_splash_chance:
                return upward
        return None

    def _find_guided_sideways_target(
        self,
        particle: WaterParticle,
        remaining: dict[tuple[int, int], WaterParticle],
        next_waters: dict[tuple[int, int], WaterParticle],
        sideways: list[tuple[int, int]],
    ) -> tuple[int, int] | None:
        x, y = particle.pos
        for target_x, target_y in sideways:
            direction = self.horizontal_step(x, target_x)
            if direction == 0:
                continue
            if self._find_drop_distance(x, y, direction, remaining, next_waters) is not None and self._is_open_for_water(
                (target_x, target_y),
                remaining,
                next_waters,
            ):
                return target_x, target_y
        return None

    def _find_drop_distance(
        self,
        x: int,
        y: int,
        direction: int,
        remaining: dict[tuple[int, int], WaterParticle],
        next_waters: dict[tuple[int, int], WaterParticle],
    ) -> int | None:
        for distance in range(1, self.config.lateral_flow_search_depth + 1):
            cell = self.normalize_coord((x + direction * distance, y))
            below = self.normalize_coord((cell[0], y + 1))
            if not self._is_open_for_water(cell, remaining, next_waters):
                return None
            if self._is_open_for_water(below, remaining, next_waters):
                return distance
        return None

    def _try_swap_red_water_upward(
        self,
        particle: WaterParticle,
        remaining: dict[tuple[int, int], WaterParticle],
        next_waters: dict[tuple[int, int], WaterParticle],
    ) -> tuple[int, int] | None:
        x, y = particle.pos
        above = self.normalize_coord((x, y - 1))
        if self._swap_with_blue_water(above, (x, y), remaining, next_waters):
            return above

        lateral_targets = self._prioritize_sideways_targets(
            particle,
            [
                self.normalize_coord((x + particle.horizontal_preference, y)),
                self.normalize_coord((x - particle.horizontal_preference, y)),
            ],
        )
        if particle.previous_pos is not None:
            # 直前に左右交換で移ってきた位置へ即座に戻すと、
            # 壁際で赤水と青水が永遠に入れ替わり続けてしまう。
            # ここでは「直前いたマス」への左右交換だけを 1 フレーム禁止し、
            # 真上交換や通常移動には影響させない。
            lateral_targets = [target for target in lateral_targets if target != particle.previous_pos]
        for target in lateral_targets:
            if self._swap_with_blue_water(target, (x, y), remaining, next_waters):
                return target

        blocking_above = self._get_water_at(above, remaining, next_waters)
        if blocking_above is None or not blocking_above.is_red:
            return None

        diagonal_targets = [
            self.normalize_coord((x - 1, y - 1)),
            self.normalize_coord((x + 1, y - 1)),
        ]
        for target in diagonal_targets:
            if self._swap_with_blue_water(target, (x, y), remaining, next_waters):
                return target

        return None

    def _swap_with_blue_water(
        self,
        source: tuple[int, int],
        destination: tuple[int, int],
        remaining: dict[tuple[int, int], WaterParticle],
        next_waters: dict[tuple[int, int], WaterParticle],
    ) -> bool:
        source = self.normalize_coord(source)
        destination = self.normalize_coord(destination)
        candidate = self._get_water_at(source, remaining, next_waters)
        if candidate is None or candidate.is_red:
            return False

        candidate.x, candidate.y = destination
        if source in next_waters:
            del next_waters[source]
            next_waters[destination] = candidate
        else:
            remaining[destination] = remaining.pop(source)
        return True

    def _get_water_at(
        self,
        coord: tuple[int, int],
        remaining: dict[tuple[int, int], WaterParticle],
        next_waters: dict[tuple[int, int], WaterParticle],
    ) -> WaterParticle | None:
        coord = self.normalize_coord(coord)
        if coord in next_waters:
            return next_waters[coord]
        return remaining.get(coord)

    def _is_open_for_water(
        self,
        coord: tuple[int, int],
        remaining: dict[tuple[int, int], WaterParticle],
        next_waters: dict[tuple[int, int], WaterParticle],
    ) -> bool:
        coord = self.normalize_coord(coord)
        if not self.is_passable_cell(coord):
            return False
        if coord in self.blocks:
            return False
        if coord in remaining:
            return False
        if coord in next_waters:
            return False
        return True

    def normalize_coord(self, coord: tuple[int, int]) -> tuple[int, int]:
        return self.stage.normalize_coord(*coord)

    def neighbors4(self, coord: tuple[int, int]) -> tuple[tuple[int, int], ...]:
        x, y = coord
        return (
            self.normalize_coord((x, y - 1)),
            self.normalize_coord((x, y + 1)),
            self.normalize_coord((x - 1, y)),
            self.normalize_coord((x + 1, y)),
        )

    def horizontal_step(self, current_x: int, target_x: int) -> int:
        if target_x == (current_x + 1) % self.stage.width:
            return 1
        if target_x == (current_x - 1) % self.stage.width:
            return -1
        if target_x == current_x:
            return 0
        return 1 if target_x > current_x else -1

    def has_static_wall(self, coord: tuple[int, int]) -> bool:
        x, y = self.normalize_coord(coord)
        return self.stage.tile_at(x, y) == StageTile.WALL and (x, y) not in self.destroyed_walls

    def is_passable_cell(self, coord: tuple[int, int]) -> bool:
        x, y = self.normalize_coord(coord)
        tile = self.stage.tile_at(x, y)
        if tile == StageTile.EMPTY:
            return True
        return tile == StageTile.WALL and (x, y) in self.destroyed_walls

    @property
    def goal_removed_total(self) -> int:
        return self.goal_removed_blue + self.goal_removed_red

    @property
    def clear_ratio(self) -> float:
        if self.config.stage_goal <= 0:
            return 0.0
        return self.goal_removed_blue / self.config.stage_goal

    @property
    def clear_percentage(self) -> float:
        return self.clear_ratio * 100.0

    @property
    def is_true_clear(self) -> bool:
        if not self.cleared:
            return False
        return self.clear_ratio >= self.config.clear_rate
