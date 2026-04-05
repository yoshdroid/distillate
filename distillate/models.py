from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WaterParticle:
    x: int
    y: int
    horizontal_preference: int = 0

    @property
    def pos(self) -> tuple[int, int]:
        return self.x, self.y


@dataclass
class TempBlock:
    x: int
    y: int
    life: int
    max_life: int

    @property
    def pos(self) -> tuple[int, int]:
        return self.x, self.y

    def tick(self) -> bool:
        self.life -= 1
        return self.life > 0

    def animation_phase(self) -> int:
        if self.life < self.max_life // 8:
            return 2
        if self.life < (self.max_life // 8) * 3:
            return 1
        return 0
