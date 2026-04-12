from __future__ import annotations

import random
from dataclasses import dataclass, field

from distillate.models import TempBlock, WaterParticle
from distillate.stage import Stage


@dataclass
class SimulationConfig:
    # 一時ブロックの寿命。
    block_life: int
    # 水更新を何フレームに一度行うか。
    water_speed: int
    # 同時に存在できる水の最大数。
    max_water: int
    # 青い水が赤い水へ変化するまでに必要な停滞回数。
    max_stress: int
    # W キーなどで全水削除した後の再生成停止フレーム数。
    reset_cooldown_frames: int
    # 水の左右選択を再現可能にするための乱数シード。
    random_seed: int = 0
    # ゴール排水で除去すべき水の総数。0 以下ならクリア判定なし。
    stage_goal: int = 0
    # True Clear 判定に使う青水比率の閾値。
    clear_rate: float = 0.0


@dataclass
class SimulationState:
    # ステージ本体。固定壁・水源・排水口を参照する。
    stage: Stage
    # シミュレーション全体の定数設定。
    config: SimulationConfig
    # 一時ブロックは座標をキーに辞書で保持する。
    blocks: dict[tuple[int, int], TempBlock] = field(default_factory=dict)
    # 水も座標をキーに辞書で保持する。
    # 同一座標への重複配置を防ぎやすく、入れ替え処理も追いやすい。
    waters: dict[tuple[int, int], WaterParticle] = field(default_factory=dict)
    frame_count: int = 0
    cooldown_frames: int = 0
    goal_removed_blue: int = 0
    goal_removed_red: int = 0
    cleared: bool = False
    randomizer: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self.randomizer = random.Random(self.config.random_seed)

    def place_block(self, x: int, y: int) -> bool:
        # ブロックは「空きタイル」で、かつ既存のブロックや水がいない場所にのみ置ける。
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
        if self.cleared:
            return

        # 毎フレームの更新順序。
        # 1. フレーム加算
        # 2. 一時ブロック寿命更新
        # 3. 全水削除要求があれば処理して終了
        # 4. クールダウン中なら水更新を止める
        # 5. 指定間隔のフレームでのみ水処理を進める
        # 6. 排水 -> 生成 -> 移動 の順で適用
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
        # 走査中削除を避けるため、先に寿命切れ座標を集めてから削除する。
        expired = [coord for coord, block in self.blocks.items() if not block.tick()]
        for coord in expired:
            del self.blocks[coord]

    def _remove_drained_water(self) -> None:
        # 排水口の上下左右にいる水を除去する。
        # ここも削除対象をいったん集めてから消す。
        drained: dict[tuple[int, int], bool] = {}
        for drain_x, drain_y in self.stage.drain_positions():
            for x, y in _neighbors4(drain_x, drain_y):
                if (x, y) in self.waters:
                    drained[(x, y)] = False
        for drain_x, drain_y in self.stage.goal_drain_positions():
            for x, y in _neighbors4(drain_x, drain_y):
                if (x, y) in self.waters:
                    drained[(x, y)] = True

        for coord, counted_for_goal in drained.items():
            water = self.waters.get(coord)
            if water is None:
                continue
            if counted_for_goal:
                if water.is_red:
                    self.goal_removed_red += 1
                else:
                    self.goal_removed_blue += 1
            del self.waters[coord]

        if self.config.stage_goal > 0 and self.goal_removed_total >= self.config.stage_goal:
            self.cleared = True

    def _spawn_water(self) -> None:
        # 各水源は、総数制限に引っかからない限り、自分の位置に水を1個だけ維持しようとする。
        for source_x, source_y in self.stage.source_positions():
            if len(self.waters) >= self.config.max_water:
                return
            coord = (source_x, source_y)
            if coord in self.waters:
                continue
            self.waters[coord] = WaterParticle(x=source_x, y=source_y)

    def _move_water(self) -> None:
        # 水の更新順は y, x 昇順で固定する。
        # これにより「どちらが先着か」が毎回安定し、挙動の再現性が上がる。
        remaining = dict(sorted(self.waters.items(), key=lambda item: (item[0][1], item[0][0])))
        # next_waters は「このフレームの移動後に確定した水配置」。
        # remaining は「まだこれから更新する水配置」。
        # 2つに分けることで、同一フレーム中の衝突や入れ替えを安全に扱う。
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
        # 水の移動優先順位はここで定義している。
        #
        # 青い水:
        # 1. 下へ進む
        # 2. 左右の優先方向へ進む
        # 3. 逆側へ進む
        # 4. どこにも行けなければその場に留まり、stress を加算
        #
        # 赤い水:
        # 0. まず「上方向への入れ替え」ができるか試す
        # 1. 以降は青い水と同じく下・左右を試す
        x, y = particle.pos
        if particle.is_red:
            # 赤い水は上に抜ける性質を持つ。
            # ここで交換成立した場合は、そのフレームの移動先が確定する。
            swapped = self._try_swap_red_water_upward(particle, remaining, next_waters)
            if swapped is not None:
                return swapped

        down = (x, y + 1)
        if self._is_open_for_water(down, remaining, next_waters):
            # どこかに動けた青い水は停滞状態を解除する。
            particle.reset_stress()
            return down

        if particle.horizontal_preference == 0:
            # 左右どちらを優先するかは最初に一度だけ決める。
            # ここを毎回ランダムにすると、流れが不安定で読みにくくなる。
            particle.horizontal_preference = self.randomizer.choice((-1, 1))

        # 直前いた場所へ戻る候補は後回しにする。
        # これにより、最上部や狭い横通路での「左右に1マスずつ往復する」現象を抑える。
        sideways = self._prioritize_sideways_targets(
            particle,
            [
                (x + particle.horizontal_preference, y),
                (x - particle.horizontal_preference, y),
            ],
        )
        for target in sideways:
            if self._is_open_for_water(target, remaining, next_waters):
                particle.reset_stress()
                return target

        # 青い水だけが停滞で stress を溜める。
        # 赤い水はすでに変質済みなので、これ以上 stress を増やさない。
        if not particle.is_red and all(not self._is_open_for_water(target, remaining, next_waters) for target in sideways):
            particle.add_stress(self.config.max_stress)

        # 下にも左右にも行けない場合は現在位置に留まる。
        return x, y

    def _prioritize_sideways_targets(
        self,
        particle: WaterParticle,
        targets: list[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        # 直前位置が候補に含まれる場合は、その候補を末尾に回す。
        # これにより「左へ行った次のフレームで即右へ戻る」といった振動を減らす。
        if particle.previous_pos is None:
            return targets

        forward_targets = [target for target in targets if target != particle.previous_pos]
        backtrack_targets = [target for target in targets if target == particle.previous_pos]
        return forward_targets + backtrack_targets

    def _try_swap_red_water_upward(
        self,
        particle: WaterParticle,
        remaining: dict[tuple[int, int], WaterParticle],
        next_waters: dict[tuple[int, int], WaterParticle],
    ) -> tuple[int, int] | None:
        # 赤い水の「上へ抜ける」ルールをまとめた関数。
        #
        # 優先順位:
        # 1. 真上が青い水なら、その青い水と入れ替える
        # 2. 真上が赤い水で塞がっているなら、左上・右上の青い水との入れ替えを試す
        # 3. どれも無理なら通常移動へ戻る
        x, y = particle.pos
        above = (x, y - 1)
        if self._swap_with_blue_water(above, (x, y), remaining, next_waters):
            return above

        blocking_above = self._get_water_at(above, remaining, next_waters)
        if blocking_above is None or not blocking_above.is_red:
            return None

        diagonal_targets = [(x - 1, y - 1), (x + 1, y - 1)]
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
        # source にある青い水を destination へ押し下げ、
        # 呼び出し元の赤い水が source へ上がるための「交換」を成立させる。
        #
        # ここで動かしているのは青い水だけで、赤い水自身の座標更新は呼び出し元で行う。
        # そのため、この関数の成功時は「source に赤い水が入れる」と解釈する。
        candidate = self._get_water_at(source, remaining, next_waters)
        if candidate is None or candidate.is_red:
            return False

        candidate.x, candidate.y = destination
        if source in next_waters:
            # すでに更新済みの青い水と交換する場合。
            del next_waters[source]
            next_waters[destination] = candidate
        else:
            # まだ未更新の青い水と交換する場合。
            # remaining 側のキーを destination に差し替えておく。
            remaining[destination] = remaining.pop(source)
        return True

    def _get_water_at(
        self,
        coord: tuple[int, int],
        remaining: dict[tuple[int, int], WaterParticle],
        next_waters: dict[tuple[int, int], WaterParticle],
    ) -> WaterParticle | None:
        # 同一フレーム中は「更新済み配置」と「未更新配置」に水が分かれている。
        # そのため、水の有無を確認するときは必ず両方を見る必要がある。
        if coord in next_waters:
            return next_waters[coord]
        return remaining.get(coord)

    def _is_open_for_water(
        self,
        coord: tuple[int, int],
        remaining: dict[tuple[int, int], WaterParticle],
        next_waters: dict[tuple[int, int], WaterParticle],
    ) -> bool:
        # 水が入れる「空き」とは:
        # - ステージ上で通行可能
        # - 一時ブロックがない
        # - 未更新の水がいない
        # - 更新済みの水もいない
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


def _neighbors4(x: int, y: int) -> tuple[tuple[int, int], ...]:
    # 排水判定などで使う4近傍。
    return ((x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y))
