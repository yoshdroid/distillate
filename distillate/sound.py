from __future__ import annotations

from dataclasses import dataclass

import pyxel


EFFECT_CHANNEL = 0
BGM_CHANNELS = (1, 2, 3)
DEFAULT_TEMPO = 240


@dataclass(frozen=True)
class SoundEffect:
    sound_id: int
    priority: int


@dataclass(frozen=True)
class BgmTrack:
    name: str
    channel_sounds: tuple[int | None, int | None, int | None]


class EffectName:
    SYSTEM = "system"
    BLOCK_PLACE = "block_place"
    BLOCK_BREAK = "block_break"
    GOAL_RED_DRAIN = "goal_red_drain"
    GOAL_BLUE_DRAIN = "goal_blue_drain"
    NORMAL_DRAIN = "normal_drain"


class SoundManager:
    def __init__(self) -> None:
        self.effects: dict[str, SoundEffect] = {
            EffectName.SYSTEM: SoundEffect(sound_id=0, priority=0),
            EffectName.BLOCK_PLACE: SoundEffect(sound_id=1, priority=1),
            EffectName.BLOCK_BREAK: SoundEffect(sound_id=2, priority=1),
            EffectName.GOAL_RED_DRAIN: SoundEffect(sound_id=3, priority=2),
            EffectName.GOAL_BLUE_DRAIN: SoundEffect(sound_id=4, priority=3),
            EffectName.NORMAL_DRAIN: SoundEffect(sound_id=5, priority=4),
        }
        self.bgm_tracks: dict[str, BgmTrack] = {
            "stage": BgmTrack(name="stage", channel_sounds=(8, 9, 10)),
            "clear": BgmTrack(name="clear", channel_sounds=(11, 12, None)),
        }
        self.pending_effect: str | None = None
        self.current_bgm: str | None = None

    def setup(self) -> None:
        self._set_sound(0, "c3g3", "p", "7", "n", DEFAULT_TEMPO)
        self._set_sound(1, "f3", "n", "7", "n", DEFAULT_TEMPO)
        self._set_sound(2, "c2c2", "n", "7", "n", DEFAULT_TEMPO)
        self._set_sound(3, "c2c#2", "p", "7", "f", DEFAULT_TEMPO)
        self._set_sound(4, "d4", "p", "6", "f", DEFAULT_TEMPO)
        self._set_sound(5, "c3", "p", "5", "f", DEFAULT_TEMPO)

        # BGM は後から MML を差し替えやすいよう、チャンネルごとに独立定義する。
        self._set_sound(8, "c3e3g3c4", "t", "4", "f", 24)
        self._set_sound(9, "c2g2c2g2", "s", "3", "f", 24)
        self._set_sound(10, "c1c1", "p", "2", "f", 24)
        self._set_sound(11, "c4e4g4c4", "t", "5", "f", 18)
        self._set_sound(12, "c3g3c4g3", "p", "4", "f", 18)

    def request_effect(self, effect_name: str) -> None:
        if effect_name not in self.effects:
            return
        if self.pending_effect is None:
            self.pending_effect = effect_name
            return

        current = self.effects[self.pending_effect]
        candidate = self.effects[effect_name]
        if candidate.priority < current.priority:
            self.pending_effect = effect_name

    def flush_effects(self) -> None:
        if self.pending_effect is None:
            return
        effect = self.effects[self.pending_effect]
        pyxel.play(EFFECT_CHANNEL, effect.sound_id)
        self.pending_effect = None

    def play_bgm(self, track_name: str) -> None:
        track = self.bgm_tracks.get(track_name)
        if track is None:
            return
        self.stop_bgm()
        for channel, sound_id in zip(BGM_CHANNELS, track.channel_sounds):
            if sound_id is None:
                continue
            pyxel.play(channel, sound_id, loop=True)
        self.current_bgm = track_name

    def stop_bgm(self) -> None:
        for channel in BGM_CHANNELS:
            pyxel.stop(channel)
        self.current_bgm = None

    def _set_sound(self, sound_id: int, notes: str, tones: str, volumes: str, effects: str, speed: int) -> None:
        pyxel.sounds[sound_id].set(notes, tones, volumes, effects, speed)
