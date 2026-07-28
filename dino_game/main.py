"""
Dino Game - main.py

Wires together entities.py, spawner.py, score.py and game_state.py
into a full playable game: colorful visuals (same layout/feel as the
original web dino game), duck/jump controls, three power-up types,
procedural sound effects, levels that ramp up speed, and a
persisted high score.

Controls:
    SPACE / UP    -> jump (also restarts after game over)
    DOWN          -> duck (hold)
    ESC           -> quit

The Pygame game loop, every frame:
    1. handle_input()  -> read events (keyboard, quit)
    2. update()          -> advance game state
    3. draw()             -> render everything
Frame rate is capped with a Clock so the game runs at a consistent
speed on any machine.
"""

import sys

import pygame

from entities import GROUND_Y
from game_state import GameState

# --- Config constants (kept at the top so they're easy to tune) ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
FPS = 60

SKY_TOP_COLOR = (135, 206, 235)     # sky blue
SKY_BAND_COLOR = (200, 235, 250)    # lighter band just above the ground
GROUND_COLOR = (150, 111, 51)       # sandy brown
GROUND_LINE_COLOR = (90, 60, 20)
CLOUD_COLOR = (255, 255, 255)
TEXT_COLOR = (40, 40, 40)
GAMEOVER_COLOR = (180, 30, 30)

FONT_NAME = None  # default pygame font


class Cloud:
    """Purely decorative background element - drifts slowly at a fixed
    rate regardless of game speed, so it reads as distant/parallax."""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def update(self):
        self.x -= 0.6

    def is_off_screen(self):
        return self.x < -60

    def draw(self, screen):
        pygame.draw.ellipse(screen, CLOUD_COLOR, (self.x, self.y, 50, 18))
        pygame.draw.ellipse(screen, CLOUD_COLOR, (self.x + 15, self.y - 8, 35, 18))


def draw_background(screen, ground_scroll):
    screen.fill(SKY_TOP_COLOR)

    # sun, tucked in the top corner
    pygame.draw.circle(screen, (255, 235, 140), (SCREEN_WIDTH - 70, 60), 30)
    pygame.draw.circle(screen, (255, 245, 190), (SCREEN_WIDTH - 70, 60), 30, 4)

    pygame.draw.rect(screen, SKY_BAND_COLOR, (0, GROUND_Y - 60, SCREEN_WIDTH, 60))
    pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))
    pygame.draw.line(screen, GROUND_LINE_COLOR, (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 3)

    # scrolling dashes just under the ground line, for a sense of motion
    dash_w, gap = 20, 20
    offset = int(ground_scroll) % (dash_w + gap)
    x = -offset
    while x < SCREEN_WIDTH:
        pygame.draw.line(screen, GROUND_LINE_COLOR, (x, GROUND_Y + 10), (x + dash_w, GROUND_Y + 10), 2)
        x += dash_w + gap

    # small scrolling grass tufts scattered a bit deeper in the ground band
    tuft_gap = 70
    offset2 = int(ground_scroll * 0.8) % tuft_gap
    x = -offset2
    while x < SCREEN_WIDTH:
        base = (x, GROUND_Y + 26)
        pygame.draw.polygon(screen, (90, 150, 60), [
            (base[0] - 5, base[1] + 8), (base[0], base[1] - 6), (base[0] + 2, base[1] + 8),
        ])
        pygame.draw.polygon(screen, (90, 150, 60), [
            (base[0] + 3, base[1] + 8), (base[0] + 8, base[1] - 3), (base[0] + 9, base[1] + 8),
        ])
        x += tuft_gap


def _panel(screen, rect, color=(255, 255, 255), alpha=160):
    """Small translucent rounded panel so HUD text doesn't float bare on the sky."""
    surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (*color, alpha), surf.get_rect(), border_radius=10)
    screen.blit(surf, rect.topleft)


def draw_hud(screen, font, small_font, state):
    score_str = f"{state.score.get_current_int():05d}"
    hi_str = f"HI {int(state.score.high_score):05d}"
    score_text = font.render(score_str, True, TEXT_COLOR)
    hi_text = small_font.render(hi_str, True, TEXT_COLOR)

    panel_w = score_text.get_width() + hi_text.get_width() + 40
    _panel(screen, pygame.Rect(SCREEN_WIDTH - panel_w - 15, 10, panel_w, 36))
    screen.blit(hi_text, (SCREEN_WIDTH - panel_w - 5 + 15, 20))
    screen.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 25, 14))

    level_text = small_font.render(f"Level {state.level}", True, TEXT_COLOR)
    _panel(screen, pygame.Rect(15, 10, level_text.get_width() + 20, 30))
    screen.blit(level_text, (25, 15))

    # active power-up indicators, stacked as their own small badges
    badge_y = 46
    badges = []
    if state.shield_frames > 0:
        badges.append(("SHIELD", (180, 130, 0)))
    if state.slowmo_frames > 0:
        badges.append(("SLOW-MO", (20, 80, 160)))
    if state.boost_frames > 0:
        badges.append(("2X SCORE", (110, 40, 150)))

    for label, color in badges:
        badge_text = small_font.render(label, True, color)
        _panel(screen, pygame.Rect(15, badge_y, badge_text.get_width() + 20, 26), color=(255, 255, 255), alpha=190)
        screen.blit(badge_text, (25, badge_y + 4))
        badge_y += 30


def draw_game_over(screen, font, small_font):
    msg = font.render("GAME OVER", True, GAMEOVER_COLOR)
    screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2 - 40))
    hint = small_font.render("Press SPACE / UP to restart", True, TEXT_COLOR)
    screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT // 2))


def handle_input(state):
    """
    Poll all pending events. Returns False if the game should quit.
    Jump / duck / restart are applied directly to the game state.
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            if event.key in (pygame.K_UP, pygame.K_SPACE):
                if state.game_over:
                    state.reset()
                else:
                    state.jump()
            if event.key == pygame.K_DOWN:
                state.start_duck()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                state.stop_duck()
    return True


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dino Game")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(FONT_NAME, 28, bold=True)
    small_font = pygame.font.SysFont(FONT_NAME, 18, bold=True)

    state = GameState()
    ground_scroll = 0.0
    clouds = [Cloud(x, y) for x, y in ((100, 60), (350, 90), (600, 50))]

    running = True
    while running:
        running = handle_input(state)

        state.update()
        if not state.game_over:
            ground_scroll += state.effective_speed

        for cloud in clouds:
            cloud.update()
        clouds = [c for c in clouds if not c.is_off_screen()]
        while len(clouds) < 3:
            clouds.append(Cloud(SCREEN_WIDTH + 20, 40 + 20 * len(clouds)))

        draw_background(screen, ground_scroll)
        for cloud in clouds:
            cloud.draw(screen)
        state.draw(screen)
        draw_hud(screen, font, small_font, state)
        if state.game_over:
            draw_game_over(screen, font, small_font)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
