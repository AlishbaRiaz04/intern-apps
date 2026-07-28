"""
spawner.py

Decides *when* and *what* to spawn - obstacles (cacti / birds) and
power-ups. All the randomness and timing logic lives here, so
game_state.py just calls update() each frame and gets new entities
appended to the lists it passes in.
"""

import random

from entities import (
    Cactus, Bird,
    ShieldPowerUp, SlowMoPowerUp, ScoreBoostPowerUp,
)

SCREEN_WIDTH = 800

# Obstacle spawn gap, in frames. Shrinks slightly as level rises (see
# game_state.py) but never goes below MIN_OBSTACLE_GAP, so the game
# never becomes unfairly dense.
BASE_OBSTACLE_GAP_MIN = 70
BASE_OBSTACLE_GAP_MAX = 130
MIN_OBSTACLE_GAP = 45

# Power-ups are rarer than obstacles by design - they're a bonus, not
# the main challenge.
POWERUP_GAP_MIN = 400
POWERUP_GAP_MAX = 700


class Spawner:
    def __init__(self):
        self._obstacle_timer = random.randint(BASE_OBSTACLE_GAP_MIN, BASE_OBSTACLE_GAP_MAX)
        self._powerup_timer = random.randint(POWERUP_GAP_MIN, POWERUP_GAP_MAX)

    def update(self, level, speed, obstacles, powerups):
        """
        Called once per frame. Counts down internal timers and, when
        one hits zero, appends a freshly spawned entity to the given
        list and resets that timer.
        """
        self._obstacle_timer -= 1
        if self._obstacle_timer <= 0:
            obstacles.append(self._spawn_obstacle(speed))
            gap_min = max(MIN_OBSTACLE_GAP, BASE_OBSTACLE_GAP_MIN - level * 4)
            gap_max = max(gap_min + 20, BASE_OBSTACLE_GAP_MAX - level * 6)
            self._obstacle_timer = random.randint(gap_min, gap_max)

        self._powerup_timer -= 1
        if self._powerup_timer <= 0:
            powerups.append(self._spawn_powerup(speed))
            self._powerup_timer = random.randint(POWERUP_GAP_MIN, POWERUP_GAP_MAX)

    def _spawn_obstacle(self, speed):
        if random.random() < 0.65:
            size = random.choice(["small", "small", "large"])
            return Cactus(x=SCREEN_WIDTH + 20, speed=speed, size=size)
        else:
            variant = random.choice(["high", "low"])
            return Bird(x=SCREEN_WIDTH + 20, speed=speed, variant=variant)

    def _spawn_powerup(self, speed):
        kind = random.choice(["shield", "slowmo", "boost"])
        if kind == "shield":
            return ShieldPowerUp(x=SCREEN_WIDTH + 20, speed=speed)
        elif kind == "slowmo":
            return SlowMoPowerUp(x=SCREEN_WIDTH + 20, speed=speed)
        else:
            return ScoreBoostPowerUp(x=SCREEN_WIDTH + 20, speed=speed)
