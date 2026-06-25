import pygame


class Cargo:
    """Represents a cargo item that can be loaded onto the raft."""

    # WEIGHT in kg
    WEIGHTS = {
        "food": 20,
        "cloth": 25,
        "medicine": 30,
        "weapons": 35,
    }

    NAMES = {
        "food":     "Food",
        "cloth":    "Cloth",
        "medicine": "Medicine",
        "weapons":  "Weapons",
    }

    def __init__(self, cargo_type: str, image: pygame.Surface, x: int, y: int):
        self.type    = cargo_type
        self.name    = self.NAMES.get(cargo_type, cargo_type)
        self.weight  = self.WEIGHTS.get(cargo_type, 1)  # NEW: weight property
        self.image   = image
        self.x       = float(x)
        self.y       = float(y)
        self.on_raft   = False
        self.delivered = False
        self.rect    = pygame.Rect(int(x), int(y),
                                   image.get_width(), image.get_height())
        self._bob_timer = 0.0
        self.dragging = False  # NEW: for drag-and-drop
        self.drag_offset_x = 0
        self.drag_offset_y = 0

    def update(self, dt: float):
        """Gentle bobbing animation when idle on the bank."""
        if not self.on_raft and not self.dragging:
            self._bob_timer += dt * 2.0
        self.rect.topleft = (int(self.x), int(self.y))

    def draw(self, screen: pygame.Surface):
        import math

        bob = int(math.sin(self._bob_timer) * 2) if not self.on_raft else 0

        screen.blit(
            self.image,
            (self.rect.x, self.rect.y + bob)
        )

        font = pygame.font.SysFont("monospace", 12)

        name_text = font.render(
            self.name,
            True,
            (255, 255, 255)
        )

        weight_text = font.render(
            f"{self.weight}kg",
            True,
            (255, 215, 0)
        )

        screen.blit(
            name_text,
            (
                self.rect.centerx - name_text.get_width() // 2,
                self.rect.bottom + 5
            )
        )

        screen.blit(
            weight_text,
            (
                self.rect.centerx - weight_text.get_width() // 2,
                self.rect.bottom + 20
            )
        )

    def set_position(self, x: int, y: int):
        self.x, self.y = float(x), float(y)
        self.rect.topleft = (int(x), int(y))

    def start_drag(self, mouse_x: int, mouse_y: int):  # NEW
        """Start dragging this cargo."""
        self.dragging = True
        self.drag_offset_x = int(self.x) - mouse_x
        self.drag_offset_y = int(self.y) - mouse_y

    def update_drag(self, mouse_x: int, mouse_y: int):  # NEW
        """Update position while dragging."""
        if self.dragging:
            self.x = mouse_x + self.drag_offset_x
            self.y = mouse_y + self.drag_offset_y

    def end_drag(self):  # NEW
        """Stop dragging."""
        self.dragging = False