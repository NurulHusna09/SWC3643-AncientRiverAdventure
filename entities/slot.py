import pygame


class Slot:
    """A slot on the raft where cargo can be placed."""

    def __init__(self, x: int, y: int, slot_id: int, side: str):
        """
        Args:
            x, y: Position on screen
            slot_id: 0-3 (raft has 4 slots)
            side: "left" or "right" (which side of raft balance)
        """
        self.x = x
        self.y = y
        self.slot_id = slot_id
        self.side = side  # "left" or "right"
        self.width = 80
        self.height = 80
        self.item = None  # Cargo object or None
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.highlighted = False

    def contains_point(self, px: int, py: int) -> bool:
        """Check if point is inside this slot."""
        return self.rect.collidepoint(px, py)

    def add_item(self, cargo) -> bool:
        """Try to add cargo to this slot."""
        if self.item is None:
            self.item = cargo
            return True
        return False

    def remove_item(self) -> object:
        """Remove and return cargo from this slot."""
        item = self.item
        self.item = None
        return item

    def get_weight(self) -> int:
        """Get weight of item in this slot."""
        return self.item.weight if self.item else 0

    def draw(self, screen: pygame.Surface, slot_image: pygame.Surface):
        """Draw the slot and its contents."""
        # Draw slot background
        if self.highlighted:
            # Draw highlight glow
            pygame.draw.rect(screen, (255, 200, 0), self.rect, 3, border_radius=5)
        else:
            pygame.draw.rect(screen, (150, 120, 80), self.rect, 2, border_radius=5)

        # Draw item if present
        if self.item:
            # Center item in slot
            item_x = self.x + (self.width - self.item.image.get_width()) // 2
            item_y = self.y + (self.height - self.item.image.get_height()) // 2
            screen.blit(self.item.image, (item_x, item_y))
        else:
            # Draw empty slot
            screen.blit(slot_image, (self.x, self.y))