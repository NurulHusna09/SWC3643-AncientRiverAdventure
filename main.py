"""
Ancient River Adventure
=======================
A Python + Pygame puzzle game.

Controls:
  ← → / A D  — Walk
  SPACE       — Pick up cargo / Board raft / Deliver
  P           — Pause / Unpause
  R           — Restart
  ESC         — Menu / Quit

Run:
  python main.py
"""

import pygame
import sys
import os

# Make sure Python can find the core & entities packages
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.game_manager import GameManager, SW, SH


def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((SW, SH))
    pygame.display.set_caption("🛶 Ancient River Adventure")

    gm = GameManager(screen)
    gm.run()


if __name__ == "__main__":
    main()
