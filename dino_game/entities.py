"""
entities.py

Holds all game entity classes. Each obstacle/power-up type is a
fully separate class with its own draw/update/collision logic - no
shared base class, by design, so each one is easy to tweak in
isolation.
"""

import math
import random

import pygame

# --- Shared layout constants ---
GROUND_Y = 340          # y-coordinate of the ground line

# --- Dino tuning constants ---
DINO_WIDTH = 40
DINO_HEIGHT = 60
DUCK_WIDTH = 50          # wider + shorter while ducking, like a crouch
DUCK_HEIGHT = 30
GRAVITY = 0.8             # pulls the dino down each frame
JUMP_STRENGTH = -15        # negative = upward (pygame y-axis grows downward)
DINO_COLOR = (34, 139, 34)      # forest green
SHIELD_GLOW_COLOR = (255, 221, 120)  # tint while a Shield power-up is active

# --- Cactus tuning constants ---
CACTUS_COLOR = (46, 125, 50)
CACTUS_MIN_WIDTH = 20
CACTUS_MAX_WIDTH = 40
CACTUS_HEIGHT_SMALL = 45
CACTUS_HEIGHT_LARGE = 70

# --- Bird tuning constants ---
BIRD_COLOR = (204, 60, 60)
BIRD_WIDTH = 44
BIRD_HEIGHT = 30
# "high" birds fly at standing-dino head height (must duck under them),
# "low" birds fly near the ground (must jump over them, like a cactus).
BIRD_HIGH_Y = GROUND_Y - DINO_HEIGHT - 10
BIRD_LOW_Y = GROUND_Y - BIRD_HEIGHT - 5

# --- Power-up tuning constants ---
POWERUP_RADIUS = 16
POWERUP_FLOAT_Y = GROUND_Y - DINO_HEIGHT - 30  # floats high enough to require a jump

SHIELD_COLOR = (255, 200, 40)
SLOWMO_COLOR = (60, 140, 230)
BOOST_COLOR = (170, 90, 220)

SHIELD_DURATION_FRAMES = 60 * 8    # 8 seconds @ 60 FPS
SLOWMO_DURATION_FRAMES = 60 * 5    # 5 seconds
BOOST_DURATION_FRAMES = 60 * 6     # 6 seconds
SLOWMO_FACTOR = 0.5
SCORE_BOOST_MULTIPLIER = 2


class Dino:
    """
    The player character. Uses velocity + gravity for a natural jump
    arc, plus a duck state that shrinks the hitbox and (while
    airborne) makes the dino fall faster - matching the feel of the
    original web game.
    """

    def __init__(self, x):
        self.x = x
        self.y = GROUND_Y - DINO_HEIGHT  # start standing on the ground
        self.width = DINO_WIDTH
        self.height = DINO_HEIGHT
        self.velocity_y = 0
        self.is_jumping = False
        self.is_ducking = False
        self.shield_active = False  # visual-only flag, set by GameState
        self._leg_timer = 0
        self._leg_up = True

    def jump(self):
        """Start a jump, but only if not already mid-air or ducking."""
        if not self.is_jumping and not self.is_ducking:
            self.velocity_y = JUMP_STRENGTH
            self.is_jumping = True

    def start_duck(self):
        self.is_ducking = True

    def stop_duck(self):
        self.is_ducking = False

    def update(self):
        """
        Apply gravity while airborne; while grounded, snap directly to
        the ground at the current (standing or ducking) height. This
        avoids a one-frame "floating" glitch when the duck height
        changes.
        """
        self.width = DUCK_WIDTH if (self.is_ducking and not self.is_jumping) else DINO_WIDTH
        self.height = DUCK_HEIGHT if (self.is_ducking and not self.is_jumping) else DINO_HEIGHT

        if self.is_jumping:
            gravity = GRAVITY * 2 if self.is_ducking else GRAVITY  # duck = fast-fall
            self.velocity_y += gravity
            self.y += self.velocity_y

            ground_level = GROUND_Y - self.height
            if self.y >= ground_level:
                self.y = ground_level
                self.velocity_y = 0
                self.is_jumping = False
        else:
            self.y = GROUND_Y - self.height

        # leg animation only matters while running on the ground
        if not self.is_jumping:
            self._leg_timer += 1
            if self._leg_timer >= 6:
                self._leg_timer = 0
                self._leg_up = not self._leg_up

    def draw(self, screen):
        color = SHIELD_GLOW_COLOR if self.shield_active else DINO_COLOR
        dark_color = (18, 90, 18) if not self.shield_active else (200, 160, 40)
        x, y, w, h = self.x, self.y, self.width, self.height

        if self.shield_active:
            # soft glow ring behind the whole sprite
            glow_rect = pygame.Rect(x - 6, y - 6, w + 12, h + 12)
            pygame.draw.ellipse(screen, SHIELD_COLOR, glow_rect, 3)

        if self.is_ducking and not self.is_jumping:
            self._draw_ducking(screen, x, y, w, h, color, dark_color)
        else:
            self._draw_standing(screen, x, y, w, h, color, dark_color)

    def _draw_standing(self, screen, x, y, w, h, color, dark_color):
        # tail: a triangle trailing out the back
        tail = [
            (x + w * 0.15, y + h * 0.30),
            (x - w * 0.35, y + h * 0.48),
            (x + w * 0.15, y + h * 0.62),
        ]
        pygame.draw.polygon(screen, color, tail)

        # main body (rounded blob, leaves room at the front-top for the head)
        body_rect = pygame.Rect(x, y + h * 0.18, w * 0.82, h * 0.72)
        pygame.draw.ellipse(screen, color, body_rect)

        # head, tucked up at the front
        head_rect = pygame.Rect(x + w * 0.48, y, w * 0.62, h * 0.5)
        pygame.draw.ellipse(screen, color, head_rect)

        # snout nub at the very front
        snout_rect = pygame.Rect(x + w * 0.92, y + h * 0.18, w * 0.22, h * 0.22)
        pygame.draw.ellipse(screen, color, snout_rect)

        # back spikes along the spine
        for sx in (x + w * 0.18, x + w * 0.34, x + w * 0.50):
            pygame.draw.polygon(screen, dark_color, [
                (sx, y + h * 0.16), (sx + w * 0.05, y - h * 0.08), (sx + w * 0.11, y + h * 0.16),
            ])

        # legs: two simple rounded stubs, alternating length to suggest a run
        leg_w, leg_h = w * 0.16, h * 0.34
        lift = h * 0.1
        ground_bottom = y + h
        front_x, back_x = x + w * 0.52, x + w * 0.14
        front_h = leg_h - lift if self._leg_up else leg_h
        back_h = leg_h if self._leg_up else leg_h - lift
        pygame.draw.rect(screen, color, (back_x, ground_bottom - back_h, leg_w, back_h), border_radius=4)
        pygame.draw.rect(screen, color, (front_x, ground_bottom - front_h, leg_w, front_h), border_radius=4)

        # eye + a subtle lighter-toned belly patch for a hint of depth
        light_color = tuple(min(255, c + 45) for c in color)
        belly_rect = pygame.Rect(x + w * 0.12, y + h * 0.52, w * 0.5, h * 0.3)
        pygame.draw.ellipse(screen, light_color, belly_rect)
        eye_x, eye_y = int(x + w * 0.86), int(y + h * 0.18)
        pygame.draw.circle(screen, (255, 255, 255), (eye_x, eye_y), max(3, int(w * 0.09)))
        pygame.draw.circle(screen, (20, 20, 20), (eye_x + 1, eye_y), max(2, int(w * 0.05)))

    def _draw_ducking(self, screen, x, y, w, h, color, dark_color):
        # low, stretched-out silhouette: head forward, tail back, no visible legs
        tail = [
            (x + w * 0.1, y + h * 0.25),
            (x - w * 0.3, y + h * 0.5),
            (x + w * 0.1, y + h * 0.85),
        ]
        pygame.draw.polygon(screen, color, tail)

        body_rect = pygame.Rect(x, y + h * 0.1, w * 0.85, h * 0.85)
        pygame.draw.ellipse(screen, color, body_rect)

        head_rect = pygame.Rect(x + w * 0.65, y + h * 0.05, w * 0.4, h * 0.6)
        pygame.draw.ellipse(screen, color, head_rect)

        eye_x, eye_y = int(x + w * 0.9), int(y + h * 0.3)
        pygame.draw.circle(screen, (255, 255, 255), (eye_x, eye_y), max(2, int(w * 0.07)))
        pygame.draw.circle(screen, (20, 20, 20), (eye_x + 1, eye_y), max(1, int(w * 0.04)))

    def get_rect(self):
        """Used for collision detection against obstacles/power-ups."""
        return pygame.Rect(self.x, self.y, self.width, self.height)


class Cactus:
    """
    Ground obstacle - the dino must jump over it. Fully separate class
    from Bird and the power-ups by design.
    """

    def __init__(self, x, speed, size="small"):
        self.x = x
        self.speed = speed
        self.width = random.randint(CACTUS_MIN_WIDTH, CACTUS_MAX_WIDTH)
        self.height = CACTUS_HEIGHT_LARGE if size == "large" else CACTUS_HEIGHT_SMALL
        self.y = GROUND_Y - self.height

    def update(self):
        self.x -= self.speed

    def is_off_screen(self):
        return self.x + self.width < 0

    def draw(self, screen):
        x, y, w, h = self.x, self.y, self.width, self.height
        dark = (25, 90, 30)

        # central trunk, fully rounded like a saguaro
        trunk_w = w * 0.55
        trunk_x = x + (w - trunk_w) / 2
        trunk_rect = pygame.Rect(trunk_x, y, trunk_w, h)
        pygame.draw.rect(screen, CACTUS_COLOR, trunk_rect, border_radius=int(trunk_w / 2))

        # left arm: a rounded stub out + a rounded stub up (like a bent elbow)
        arm_w = max(8, w * 0.28)
        arm_y = y + h * 0.35
        pygame.draw.rect(screen, CACTUS_COLOR, (trunk_x - arm_w * 0.75, arm_y, arm_w * 0.9, arm_w * 0.55), border_radius=6)
        pygame.draw.rect(screen, CACTUS_COLOR, (trunk_x - arm_w * 0.75, arm_y - arm_w * 0.7, arm_w * 0.55, arm_w * 0.75), border_radius=6)

        # right arm, positioned a little higher for visual variety
        arm_y2 = y + h * 0.2
        pygame.draw.rect(screen, CACTUS_COLOR, (trunk_x + trunk_w - arm_w * 0.15, arm_y2, arm_w * 0.9, arm_w * 0.55), border_radius=6)
        pygame.draw.rect(screen, CACTUS_COLOR, (trunk_x + trunk_w + arm_w * 0.55, arm_y2 - arm_w * 0.7, arm_w * 0.55, arm_w * 0.75), border_radius=6)

        # a few vertical rib lines for texture
        for i in range(1, 3):
            rib_x = trunk_x + trunk_w * (i / 3)
            pygame.draw.line(screen, dark, (rib_x, y + 6), (rib_x, y + h - 6), 2)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


class Bird:
    """
    Flying obstacle with two height variants: "high" (must duck under)
    and "low" (must jump over, like a cactus). Fully separate class
    from Cactus and the power-ups by design.
    """

    def __init__(self, x, speed, variant="high"):
        self.x = x
        self.speed = speed
        self.width = BIRD_WIDTH
        self.height = BIRD_HEIGHT
        self.variant = variant
        self.y = BIRD_HIGH_Y if variant == "high" else BIRD_LOW_Y
        self._wing_timer = 0
        self._wing_up = True

    def update(self):
        self.x -= self.speed
        self._wing_timer += 1
        if self._wing_timer >= 8:
            self._wing_timer = 0
            self._wing_up = not self._wing_up

    def is_off_screen(self):
        return self.x + self.width < 0

    def draw(self, screen):
        x, y, w, h = self.x, self.y, self.width, self.height
        dark = (140, 30, 30)

        # body: teardrop-ish, narrower at the tail
        body_rect = pygame.Rect(x + w * 0.15, y + h * 0.15, w * 0.7, h * 0.7)
        pygame.draw.ellipse(screen, BIRD_COLOR, body_rect)

        # tail feathers, fanned out at the back
        pygame.draw.polygon(screen, dark, [
            (x + w * 0.2, y + h * 0.5),
            (x - w * 0.08, y + h * 0.28),
            (x - w * 0.08, y + h * 0.72),
        ])

        # head + beak at the front
        head_center = (int(x + w * 0.82), int(y + h * 0.35))
        pygame.draw.circle(screen, BIRD_COLOR, head_center, int(h * 0.28))
        pygame.draw.polygon(screen, (230, 170, 40), [
            (head_center[0] + h * 0.2, head_center[1]),
            (head_center[0] + h * 0.45, head_center[1] - h * 0.08),
            (head_center[0] + h * 0.2, head_center[1] + h * 0.12),
        ])
        pygame.draw.circle(screen, (20, 20, 20), (head_center[0] + 2, head_center[1] - 2), max(2, int(h * 0.06)))

        # wings: two flapping strokes layered for a bit of thickness
        wing_y = y + h * 0.15 if self._wing_up else y + h * 0.55
        wing_tip = wing_y - h * 0.55 if self._wing_up else wing_y + h * 0.4
        wing_root = (x + w * 0.5, y + h * 0.45)
        pygame.draw.polygon(screen, dark, [
            wing_root,
            (x + w * 0.15, wing_tip),
            (x + w * 0.55, wing_y),
        ])

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


class ShieldPowerUp:
    """
    Grants one hit of protection - absorbs the next collision instead
    of ending the run. Fully separate class from Bird/Cactus and the
    other power-ups by design.
    """

    def __init__(self, x, speed):
        self.x = x
        self.y = POWERUP_FLOAT_Y
        self.speed = speed
        self.radius = POWERUP_RADIUS
        self._bob = 0.0

    def update(self):
        self.x -= self.speed
        self._bob += 0.1

    def is_off_screen(self):
        return self.x + self.radius < 0

    def draw(self, screen):
        offset = int(math.sin(self._bob) * 5)
        cx, cy = int(self.x), int(self.y + offset)
        pygame.draw.circle(screen, SHIELD_COLOR, (cx, cy), self.radius)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), self.radius, 2)
        # small shield glyph: a rounded badge shape
        r = self.radius * 0.55
        pygame.draw.polygon(screen, (255, 255, 255), [
            (cx, cy - r), (cx + r * 0.8, cy - r * 0.4), (cx + r * 0.6, cy + r * 0.7),
            (cx, cy + r), (cx - r * 0.6, cy + r * 0.7), (cx - r * 0.8, cy - r * 0.4),
        ])

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class SlowMoPowerUp:
    """
    Temporarily slows the whole game down, making obstacles easier to
    react to. Fully separate class from Bird/Cactus and the other
    power-ups by design.
    """

    def __init__(self, x, speed):
        self.x = x
        self.y = POWERUP_FLOAT_Y
        self.speed = speed
        self.radius = POWERUP_RADIUS
        self._bob = 0.0

    def update(self):
        self.x -= self.speed
        self._bob += 0.1

    def is_off_screen(self):
        return self.x + self.radius < 0

    def draw(self, screen):
        offset = int(math.sin(self._bob) * 5)
        cx, cy = int(self.x), int(self.y + offset)
        pygame.draw.circle(screen, SLOWMO_COLOR, (cx, cy), self.radius)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), self.radius, 2)
        # small spiral (snail-shell style) glyph to read as "slow"
        points = []
        for i in range(24):
            angle = i * 0.5
            r = self.radius * 0.65 * (i / 24)
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        if len(points) > 1:
            pygame.draw.lines(screen, (255, 255, 255), False, points, 2)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class ScoreBoostPowerUp:
    """
    Doubles points earned for its duration. Fully separate class from
    Bird/Cactus and the other power-ups by design.
    """

    def __init__(self, x, speed):
        self.x = x
        self.y = POWERUP_FLOAT_Y
        self.speed = speed
        self.radius = POWERUP_RADIUS
        self._bob = 0.0

    def update(self):
        self.x -= self.speed
        self._bob += 0.1

    def is_off_screen(self):
        return self.x + self.radius < 0

    def draw(self, screen):
        offset = int(math.sin(self._bob) * 5)
        cx, cy = int(self.x), int(self.y + offset)
        pygame.draw.circle(screen, BOOST_COLOR, (cx, cy), self.radius)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), self.radius, 2)
        # 5-point star glyph
        r_out, r_in = self.radius * 0.75, self.radius * 0.32
        star_points = []
        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            r = r_out if i % 2 == 0 else r_in
            star_points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        pygame.draw.polygon(screen, (255, 255, 255), star_points)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
