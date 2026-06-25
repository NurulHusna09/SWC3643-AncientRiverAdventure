import pygame


class Merchant:
    """Player-controlled merchant character."""

    SPEED    = 200   # pixels per second
    ANIM_FPS = 8

    def __init__(self, images: dict, x: int, y: int):
        # images dict keys: "idle", "walk1", "walk2", "row"
        self.images = images
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.facing_right  = True
        self.weight = 65
        self.state = "idle"
        self._anim_timer   = 0.0
        self._anim_frame   = 0
        self.on_raft       = False
        self.carrying = None
        self.rect = pygame.Rect(int(x), int(y),
                                images["idle"].get_width(),
                                images["idle"].get_height())

    def move_left(self, dt: float):
        self.x -= self.SPEED * dt
        self.facing_right = False
        self._tick_anim(dt)

    def move_right(self, dt: float):
        self.x += self.SPEED * dt
        self.facing_right = True
        self._tick_anim(dt)

    def move_up(self, dt):
        self.y -= self.SPEED * dt
        self._tick_anim(dt)

    def move_down(self, dt):
        self.y += self.SPEED * dt
        self._tick_anim(dt)

    def _tick_anim(self, dt: float):
        self._anim_timer += dt
        if self._anim_timer >= 1.0 / self.ANIM_FPS:
            self._anim_timer = 0
            self._anim_frame ^= 1   # toggle between 0 and 1

    def clamp(self, min_x, max_x, min_y, max_y):
        self.x = max(min_x, min(max_x, self.x))
        self.y = max(min_y, min(max_y, self.y))

    def update(self, dt: float):
        self.rect.topleft = (int(self.x), int(self.y))

    def draw(self, screen: pygame.Surface):
        if self.on_raft:
            surf = self.images["row"]
        elif self.state == "walking":
            surf = self.images["walk1"] if self._anim_frame == 0 \
                   else self.images["walk2"]
        else:
            surf = self.images["idle"]

        if not self.facing_right:
            surf = pygame.transform.flip(surf, True, False)

        screen.blit(surf, (int(self.x), int(self.y)))

    def set_position(self, x: float, y: float):
        self.x, self.y = float(x), float(y)
        self.rect.topleft = (int(x), int(y))

    def walk_to(self, target_x, dt):

        if abs(target_x - self.x) < 5:
            self.state = "idle"
            return True

        self.state = "walking"

        if target_x > self.x:
            self.move_right(dt)
        else:
            self.move_left(dt)

        return False
