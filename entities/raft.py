import pygame
import math


class Raft:
    """Bamboo raft with 4 slots for balanced cargo loading."""

    SPEED = 120  # pixels per second

    def __init__(self, image: pygame.Surface, x: int, y: int):
        self.image = image
        self.x = float(x)
        self.y = float(y)
        self.target_x = None
        self.next_side = "left"
        self.moving = False
        self.side = "left"
        self.cargo_on_raft = []
        self.rect = pygame.Rect(int(x), int(y),
                                image.get_width(), image.get_height())

        # NEW: 4 slots for cargo
        from entities.slot import Slot
        self.slots = [
            Slot(x + 15, y + 10, 0, "left"),
            Slot(x + 15, y + 50, 1, "left"),

            Slot(x + 80, y + 10, 2, "right"),
            Slot(x + 80, y + 50, 3, "right"),
        ]

        # Tilt/balance system
        self.tilt_angle = 0.0  # degrees
        self.is_balanced = False
        self.tilt_speed = 0.0  # degrees per second
        self.is_drowning = False
        self._timer = 0.0
        self._bob = 0


    # ── BALANCE LOGIC ───────────────────────────────────────────
    def check_balance(self) -> bool:
        """Calculate balance. Returns True if balanced."""
        left_weight = sum(slot.get_weight() for slot in self.slots[:2])
        right_weight = sum(slot.get_weight() for slot in self.slots[2:])

        self.left_weight = left_weight
        self.right_weight = right_weight

        difference = abs(left_weight - right_weight)
        self.is_balanced = (difference <= 1)  # Allow 1kg tolerance
        return self.is_balanced

    def get_left_weight(self) -> int:
        """Get total weight on left side."""
        return sum(slot.get_weight() for slot in self.slots[:2])

    def get_right_weight(self) -> int:
        """Get total weight on right side."""
        return sum(slot.get_weight() for slot in self.slots[2:])

    def get_total_weight(self, merchant_on_raft=False):

        total = 0

        if merchant_on_raft:
            total += 50

        for slot in self.slots:

            if slot.item:
                total += slot.item.weight

        return total

    def add_cargo_to_slot(self, slot_id: int, cargo) -> bool:
        """Add cargo to specific slot."""
        if slot_id < 0 or slot_id >= len(self.slots):
            return False
        return self.slots[slot_id].add_item(cargo)

    def remove_cargo_from_slot(self, slot_id: int):
        """Remove cargo from specific slot."""
        if slot_id < 0 or slot_id >= len(self.slots):
            return None
        return self.slots[slot_id].remove_item()

    # ── CROSSING LOGIC ──────────────────────────────────────────
    def start_crossing(self, target_x: float, new_side: str):
        """Start crossing the river."""
        self.target_x = target_x
        self.next_side = new_side
        self.moving = True
        self.tilt_angle = 0.0
        self.is_drowning = False
        self.check_balance()

    def update(self, dt: float):
        """
        Update raft crossing and tilt.
        Returns: None, "success", or "drowned"
        """
        self._timer += dt

        # Update cargo positions even when the raft is parked
        self.update_slot_positions(
            int(self.x),
            int(self.y + self._bob)
        )


        if not self.moving:
            self.rect.topleft = (int(self.x), int(self.y))
            return None

        total_load = self.get_total_weight(True)

        if total_load > 100:

            self.is_drowning = True

            self.tilt_angle += 120 * dt

            if self.tilt_angle >= 90:
                self.moving = False

                return "drowned"

        # Normal movement across river
        if self.target_x is not None:
            dx = self.target_x - self.x
            step = self.SPEED * dt

            if abs(dx) <= step:
                self.x = self.target_x
                self.moving = False
                self.side = self.next_side
                self.target_x = None
                self.rect.topleft = (int(self.x), int(self.y))

                return "success"
            else:
                self.x += step * (1 if dx > 0 else -1)

                self.update_slot_positions(
                    int(self.x),
                    int(self.y)
                )

        self.rect.topleft = (int(self.x), int(self.y))
        return None

    def unload_cargo(self) -> list:
        """Remove all cargo from raft."""
        items = []
        for slot in self.slots:
            if slot.item:
                items.append(slot.remove_item())
                slot.item.on_raft = False
        self.tilt_angle = 0.0
        return items

    # ── DRAWING ────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface):
        """Draw raft with tilt animation."""
        # Calculate bob for water
        self._bob = int(4 * math.sin(self._timer * 2.5))

        # Draw raft with rotation
        if self.tilt_angle != 0:
            rotated_img = pygame.transform.rotate(self.image, self.tilt_angle)
            rotated_rect = rotated_img.get_rect(
                center=(int(self.x) + self.image.get_width() // 2,
                        int(self.y) + self._bob + self.image.get_height() // 2)
            )
            screen.blit(rotated_img, rotated_rect)
        else:
            screen.blit(self.image, (int(self.x), int(self.y) + self._bob))


    @property
    def top_y(self) -> int:
        return int(self.y) + self._bob

    def update_slot_positions(self, raft_x, raft_y):

        self.slots[0].x = raft_x + 25
        self.slots[0].y = raft_y + 12

        self.slots[1].x = raft_x + 25
        self.slots[1].y = raft_y + 42

        self.slots[2].x = raft_x + 88
        self.slots[2].y = raft_y + 12

        self.slots[3].x = raft_x + 88
        self.slots[3].y = raft_y + 42

        for slot in self.slots:
            slot.rect.topleft = (slot.x, slot.y)

        for slot in self.slots:

            if slot.item:
                slot.item.set_position(
                    slot.x + 15,
                    slot.y + 15
                )

