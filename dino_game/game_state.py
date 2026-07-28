"""
game_state.py

The central orchestrator. Owns the dino, the live obstacle/power-up
lists, the spawner, and the score tracker. main.py just calls
handle-input methods, update(), and draw() on this each frame - all
the "what happens when things collide / level up / power-up" logic
lives here.
"""

import math
import struct

import pygame

from entities import (
    Dino,
    ShieldPowerUp, SlowMoPowerUp, ScoreBoostPowerUp,
    SHIELD_DURATION_FRAMES, SLOWMO_DURATION_FRAMES, BOOST_DURATION_FRAMES,
    SLOWMO_FACTOR, SCORE_BOOST_MULTIPLIER,
)
from spawner import Spawner
from score import Score

BASE_SPEED = 6.0
MAX_SPEED = 16.0
SPEED_PER_LEVEL = 0.6
POINTS_PER_LEVEL = 300


def _make_tone(frequency=440, duration_ms=120, volume=0.25, sample_rate=44100):
    """
    Builds a short sine-wave beep as raw 16-bit PCM bytes, so the game
    has sound effects without needing any external audio files.
    """
    n_samples = int(sample_rate * duration_ms / 1000)
    amplitude = int(32767 * volume)
    buf = bytearray()
    for i in range(n_samples):
        t = i / sample_rate
        fade = 1 - (i / n_samples)  # fade out to avoid a clicky end
        sample = int(amplitude * fade * math.sin(2 * math.pi * frequency * t))
        buf += struct.pack('<h', sample)
    return pygame.mixer.Sound(buffer=bytes(buf))


class SoundManager:
    """
    Small self-contained sound bank - every effect is a procedurally
    generated tone, so there are no audio asset files to ship or go
    missing. Fails silently if no audio device is available.
    """

    def __init__(self):
        self.enabled = True
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
            self.jump = _make_tone(600, 80, 0.2)
            self.game_over = _make_tone(150, 400, 0.3)
            self.level_up = _make_tone(900, 150, 0.25)
            self.powerup = {
                "shield": _make_tone(500, 150, 0.25),
                "slowmo": _make_tone(350, 150, 0.25),
                "boost": _make_tone(750, 150, 0.25),
            }
        except pygame.error:
            self.enabled = False

    def play(self, sound):
        if self.enabled and sound is not None:
            sound.play()


class GameState:
    def __init__(self):
        self.sound = SoundManager()
        self.score = Score()
        self.reset()

    def reset(self):
        self.dino = Dino(x=80)
        self.obstacles = []
        self.powerups = []
        self.spawner = Spawner()
        self.score.reset()
        self.speed = BASE_SPEED
        self.effective_speed = BASE_SPEED
        self.level = 1
        self.game_over = False

        # active power-up effect timers (frames remaining); 0 = inactive
        self.shield_frames = 0
        self.slowmo_frames = 0
        self.boost_frames = 0

    # ---- input-driven actions ------------------------------------
    def jump(self):
        if not self.game_over:
            was_jumping = self.dino.is_jumping
            self.dino.jump()
            if self.dino.is_jumping and not was_jumping:
                self.sound.play(self.sound.jump)

    def start_duck(self):
        if not self.game_over:
            self.dino.start_duck()

    def stop_duck(self):
        self.dino.stop_duck()

    # ---- per-frame update ------------------------------------------
    def update(self):
        if self.game_over:
            return

        self.dino.update()
        self._update_effects()

        self.effective_speed = self.speed * (SLOWMO_FACTOR if self.slowmo_frames > 0 else 1.0)
        for obstacle in self.obstacles:
            obstacle.speed = self.effective_speed
            obstacle.update()
        for powerup in self.powerups:
            powerup.speed = self.effective_speed
            powerup.update()

        self.obstacles = [o for o in self.obstacles if not o.is_off_screen()]
        self.powerups = [p for p in self.powerups if not p.is_off_screen()]

        self.spawner.update(self.level, self.effective_speed, self.obstacles, self.powerups)

        self._check_collisions()
        if not self.game_over:
            self.score.update()
            self._check_level_up()

    def _update_effects(self):
        if self.shield_frames > 0:
            self.shield_frames -= 1
        self.dino.shield_active = self.shield_frames > 0

        if self.slowmo_frames > 0:
            self.slowmo_frames -= 1

        if self.boost_frames > 0:
            self.boost_frames -= 1
            self.score.multiplier = SCORE_BOOST_MULTIPLIER
        else:
            self.score.multiplier = 1

    def _check_level_up(self):
        target_level = 1 + self.score.get_current_int() // POINTS_PER_LEVEL
        if target_level > self.level:
            self.level = target_level
            self.speed = min(MAX_SPEED, BASE_SPEED + (self.level - 1) * SPEED_PER_LEVEL)
            self.sound.play(self.sound.level_up)

    def _check_collisions(self):
        dino_rect = self.dino.get_rect()

        for obstacle in self.obstacles:
            if dino_rect.colliderect(obstacle.get_rect()):
                if self.shield_frames > 0:
                    # Shield absorbs the hit: consume it and remove the
                    # obstacle instead of ending the run.
                    self.shield_frames = 0
                    self.obstacles.remove(obstacle)
                else:
                    self._end_game()
                break

        for powerup in self.powerups[:]:
            if dino_rect.colliderect(powerup.get_rect()):
                self._collect_powerup(powerup)
                self.powerups.remove(powerup)

    def _collect_powerup(self, powerup):
        if isinstance(powerup, ShieldPowerUp):
            self.shield_frames = SHIELD_DURATION_FRAMES
            self.sound.play(self.sound.powerup["shield"])
        elif isinstance(powerup, SlowMoPowerUp):
            self.slowmo_frames = SLOWMO_DURATION_FRAMES
            self.sound.play(self.sound.powerup["slowmo"])
        elif isinstance(powerup, ScoreBoostPowerUp):
            self.boost_frames = BOOST_DURATION_FRAMES
            self.sound.play(self.sound.powerup["boost"])

    def _end_game(self):
        self.game_over = True
        self.score.save_high_score()
        self.sound.play(self.sound.game_over)

    # ---- drawing --------------------------------------------------
    def draw(self, screen):
        for obstacle in self.obstacles:
            obstacle.draw(screen)
        for powerup in self.powerups:
            powerup.draw(screen)
        self.dino.draw(screen)
