import os
import pygame

BASE_DIR   = os.path.dirname(os.path.dirname(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images")
SOUNDS_DIR = os.path.join(BASE_DIR, "assets", "sounds")


def load_image(filename: str, size: tuple = None) -> pygame.Surface:
    """Load an image from assets/images/ and optionally scale it."""
    path = os.path.join(IMAGES_DIR, filename)
    img  = pygame.image.load(path).convert_alpha()
    if size:
        img = pygame.transform.scale(img, size)
    return img


def load_sound(filename: str):
    """Load a sound from assets/sounds/. Returns None if file missing."""
    path = os.path.join(SOUNDS_DIR, filename)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None


# Auto-generate missing images
def create_all_missing_images():
    """Create all missing image files."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    pygame.init()

    images_to_create = {
        "raft.png": ((140, 60), (139, 69, 19), "rect"),
        "slot_bg.png": ((82, 82), (200, 200, 200), "rect"),
        "river_tile.png": ((100, 100), (70, 130, 200), "rect"),
    }

    for filename, (size, color, shape) in images_to_create.items():
        path = os.path.join(IMAGES_DIR, filename)
        if not os.path.exists(path):
            surf = pygame.Surface(size)
            surf.fill(color)
            pygame.draw.rect(surf, (0, 0, 0), (0, 0, size[0], size[1]), 2)
            pygame.image.save(surf, path)
            print(f"✅ Created {filename}")


create_all_missing_images()