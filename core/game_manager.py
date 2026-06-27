import pygame
import math
from core.assets import load_image, load_sound
from entities.cargo import Cargo
from entities.merchant import Merchant
from entities.raft import Raft

# ── SCREEN LAYOUT (TOP-DOWN) ────────────────────────────────────
SW, SH = 1200, 700

# Zones (left to right)
LEFT_BANK_X = 0
LEFT_BANK_W = 250

RIVER_X = 250
RIVER_W = 700

RIGHT_BANK_X = RIVER_X + RIVER_W
RIGHT_BANK_W = SW - RIGHT_BANK_X

# Heights
TOP_Y = 50
BOTTOM_Y = SH - 100

# ── colours ─────────────────────────────────────────────────────
C_BG = (34, 139, 34)  # Green background (grass)
C_RIVER = (70, 130, 200)  # River blue
C_BANK = (101, 80, 50)  # Bank brown
C_TEXT = (240, 225, 185)
C_GOLD = (220, 185, 60)
C_RED = (210, 70, 60)
C_GREEN = (80, 200, 90)
C_WARN = (230, 130, 40)
C_BLUE = (80, 150, 220)
C_WHITE = (255, 255, 255)

# ── game constants ───────────────────────────────────────────────
TIME_LIMIT = 180.0
CARGO_TYPES = ["food", "cloth", "medicine", "weapons"]

ACHIEVEMENTS = [
    {
        "id": "first_load",
        "name": "First Load!",
        "desc": "Load cargo onto raft"
    },
    {
        "id": "cargo_master",
        "name": "Cargo Master!",
        "desc": "Deliver all cargo successfully"
    },
    {
        "id": "speed_cross",
        "name": "Speed Runner!",
        "desc": "Complete in under 2 mins"
    },
    {
        "id": "no_drowns",
        "name": "Safe Journey!",
        "desc": "Complete without drowning"
    },
]


class GameManager:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()

        pygame.font.init()
        pygame.mixer.init()

        self.fnt_xl = pygame.font.SysFont("monospace", 36, bold=True)
        self.fnt_lg = pygame.font.SysFont("monospace", 26, bold=True)
        self.fnt_md = pygame.font.SysFont("monospace", 18, bold=True)
        self.fnt_sm = pygame.font.SysFont("monospace", 14)
        self.fnt_xs = pygame.font.SysFont("monospace", 12)

        self.state = "menu"  # menu, instructions, loading, crossing, victory, drowned
        self._menu_anim = 0.0
        self._load_assets()
        self.level = 1
        self.max_level = 3
        pygame.mixer.music.load("assets/sounds/bg_music.mp3")
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)
        self._init_game()

        self.previous_state = "loading"

    # ── ASSETS ──────────────────────────────────────────────────
    def _load_assets(self):

        def si(name, w, h):
            return pygame.transform.scale(load_image(name), (w, h))

        # Backgrounds
        self.img = {
            "bank_left": load_image("bank_left.png"),
            "river": load_image("river_tile.png"),
            "bank_right": load_image("bank_right.png"),

            # Game objects
            "raft": si("raft.png", 220, 130),

            # Merchant
            "m_idle": si("merchant_idle.png", 48, 64),
            "m_walk1": si("merchant_walk1.png", 48, 64),
            "m_walk2": si("merchant_walk2.png", 48, 64),
            "m_row": si("merchant_row.png", 48, 64),
            "m_drown": si("merchant_drown.png", 48, 64),

            # Slot
            "slot": si("slot_bg.png", 80, 80),
        }

        print("Left Bank:", self.img["bank_left"].get_size())
        print("River:", self.img["river"].get_size())
        print("Right Bank:", self.img["bank_right"].get_size())

        self.cargo_imgs = {
            "food": si("cargo_food.png", 60, 60),
            "cloth": si("cargo_cloth.png", 60, 60),
            "medicine": si("cargo_medicine.png", 60, 60),
            "weapons": si("cargo_weapons.png", 60, 60),

        }

        # Sounds
        self.snd_pickup = load_sound("pickup.mp3")
        self.snd_drop = load_sound("drop.mp3")
        self.snd_delivered = load_sound("delivered.mp3")
        self.snd_raft = load_sound("raft.mp3")
        self.snd_river = load_sound("river.mp3")
        self.snd_win = load_sound("win.mp3")
        self.snd_lose = load_sound("lose.mp3")

    # ── INIT GAME ───────────────────────────────────────────────
    def _init_game(self):
        self.time_left = TIME_LIMIT
        self.merchant_weight = 50
        self.raft_capacity = 100
        if self.level == 1:
            self.score = 0
        self.trips = 0

        if self.level == 1:
            self.unlocked = set()
            self.drowned_count = 0
        self._crossing_started = False
        self.previous_state = "loading"

        # Create 4 cargo items on LEFT BANK (2x2 grid)
        self.all_cargo = []
        cargo_positions = [
            (10, 90),
            (150, 90),

            (10, 200),
            (150, 200),

            (10, 310),
            (150, 310),

            (10, 420),
            (150, 420),
        ]

        if self.level == 1:
            cargo_list = [
                "food",
                "cloth",
                "medicine",
                "weapons"
            ]

        elif self.level == 2:
            cargo_list = [
                "food",
                "food",
                "cloth",
                "medicine",
                "weapons",
                "weapons"
            ]

        else:  # level 3
            cargo_list = [
                "food",
                "food",
                "cloth",
                "cloth",
                "medicine",
                "medicine",
                "weapons",
                "weapons"
            ]

        for i, cargo_type in enumerate(cargo_list):
            x, y = cargo_positions[i]

            c = Cargo(
                cargo_type,
                self.cargo_imgs[cargo_type],
                x,
                y
            )

            self.all_cargo.append(c)
        # Create raft (centered in river)
        raft_x = 270
        raft_y = 250
        self.raft = Raft(self.img["raft"], raft_x, raft_y)

        # Create merchant (on left bank, near cargo)
        self.merchant = Merchant(
            {"idle": self.img["m_idle"], "walk1": self.img["m_walk1"],
             "walk2": self.img["m_walk2"], "row": self.img["m_row"]},
            x=100, y=50
        )

        self._dragging_cargo = None
        self._menu_anim = 0.0
        self.river_offset = 0
        self.message = ""
        self.message_timer = 0

    # ── MAIN LOOP ───────────────────────────────────────────────
    def run(self):
        while True:
            dt = min(self.clock.tick(60) / 1000.0, 0.05)
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

    # ── EVENTS ──────────────────────────────────────────────────
    def _handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if ev.type == pygame.KEYDOWN:
                self._on_key(ev.key)

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self._on_mouse_down(ev.pos)

            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self._on_mouse_up()

            if ev.type == pygame.MOUSEMOTION:
                self._on_mouse_move(ev.pos)

    def _on_key(self, k):
        if self.state == "menu":
            if k == pygame.K_RETURN:
                self.level = 1
                self._init_game()
                self.state = "loading"
            elif k == pygame.K_i:
                self.state = "instructions"
            elif k == pygame.K_a:
                self.state = "achievements"
            elif k == pygame.K_ESCAPE:
                self.state = "quit_confirm"

        elif self.state in ("instructions", "achievements"):
            if k in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.state = "menu"

        elif self.state == "quit_confirm":

            if k == pygame.K_RETURN:
                pygame.quit()
                raise SystemExit

            elif k == pygame.K_ESCAPE:
                self.state = "menu"

        elif self.state == "loading":
            if k == pygame.K_e:

                if self.merchant.carrying:

                    if self._deliver_cargo():
                        pass

                    else:

                        distance = abs(
                            self.merchant.rect.centerx -
                            self.raft.rect.centerx
                        )

                        if distance < 150:

                            self._place_on_raft()

                        else:

                            old_cargo = self.merchant.carrying

                            self._pickup_cargo()

                            if self.merchant.carrying == old_cargo:
                                self._drop_cargo()

                else:
                    self._pickup_cargo()

            elif k == pygame.K_SPACE:

                if self.merchant.on_raft:
                    self._leave_raft()
                else:
                    self._board_raft()

            elif k == pygame.K_f:

                if self.merchant.on_raft:
                    self._start_crossing()
            elif k == pygame.K_ESCAPE:
                self.previous_state = self.state
                self.state = "pause"
            elif k == pygame.K_r:
                self._init_game()



        elif self.state == "crossing":

            if k == pygame.K_ESCAPE:
                self.previous_state = self.state

                self.state = "pause"

        elif self.state == "pause":

            if k == pygame.K_c:
                self.state = self.previous_state

            elif k == pygame.K_r:
                self._init_game()
                self.state = "loading"

            elif k == pygame.K_m:
                self.state = "menu"



        elif self.state in (

                "victory",

                "level_complete",

                "drowned",

                "timeout"

        ):

            if self.state == "level_complete":

                if k == pygame.K_SPACE:
                    self.level += 1
                    self._init_game()
                    self.state = "loading"

                elif k == pygame.K_ESCAPE:
                    self.state = "menu"

            if k == pygame.K_r:
                self._init_game()
                self.state = "loading"
            elif k == pygame.K_ESCAPE:
                self.state = "menu"

    def _pickup_cargo(self):

        if self._deliver_cargo():
            return

        # SWAP SYSTEM
        if self.merchant.carrying:

            for cargo in self.all_cargo:

                if cargo.delivered:
                    continue

                if cargo == self.merchant.carrying:
                    continue

                distance = abs(
                    self.merchant.rect.centerx -
                    cargo.rect.centerx
                )

                if distance < 40:
                    old_cargo = self.merchant.carrying

                    old_cargo.set_position(
                        cargo.x,
                        cargo.y
                    )

                    self.merchant.carrying = cargo

                    print(
                        "Swapped",
                        old_cargo.name,
                        "for",
                        cargo.name
                    )

                    return

            return

        distance = abs(
            self.merchant.rect.centerx -
            self.raft.rect.centerx
        )

        if distance < 150:

            for slot in self.raft.slots:

                if slot.item:
                    self.merchant.carrying = slot.item
                    slot.item = None

                    if self.snd_pickup:
                        self.snd_pickup.play()

                    print("Picked from raft")

                    return

        for cargo in self.all_cargo:

            if cargo.delivered:
                continue

            distance = abs(
                self.merchant.rect.centerx -
                cargo.rect.centerx
            )

            if distance < 60:
                self.merchant.carrying = cargo

                if self.snd_pickup:
                    self.snd_pickup.play()

                print("Picked up:", cargo.name)

                break

    def _deliver_cargo(self):

        if not self.merchant.carrying:
            return False

        if self.raft.side != "right":
            return False

        if self.merchant.x < 1000:
            return False

        cargo = self.merchant.carrying

        cargo.delivered = True

        self.merchant.carrying = None

        self.score += 100

        delivered = 0

        for c in self.all_cargo:
            if c.delivered:
                delivered += 1

        if delivered == len(self.all_cargo):
            print("ALL DELIVERED!")

            if self.snd_win:
                self.snd_win.play()

            self._unlock("cargo_master")

            if self.time_left > 60:
                self._unlock("speed_cross")

            if self.drowned_count == 0:
                self._unlock("no_drowns")

            if self.level < self.max_level:
                self.state = "level_complete"
            else:
                self.state = "victory"

        if self.snd_delivered:
            self.snd_delivered.play()

        print(cargo.name, "DELIVERED!")

        return True

    def _get_total_raft_weight(self):

        total = 0

        if self.merchant.on_raft:
            total += self.merchant_weight

        for slot in self.raft.slots:

            if slot.item:
                total += slot.item.weight

        return total

    def _board_raft(self):

        if self.merchant.carrying:
            self.message = "Place the cargo on the raft first!"
            self.message_timer = 2.0
            return

        print("ENTER PRESSED")

        print("Merchant:", self.merchant.rect.center)
        print("Raft:", self.raft.rect.center)

        distance_x = abs(
            self.merchant.rect.centerx -
            self.raft.rect.centerx
        )

        distance_y = abs(
            self.merchant.rect.centery -
            self.raft.rect.centery
        )

        print("X:", distance_x)
        print("Y:", distance_y)

        if distance_x < 150 and distance_y < 120:
            self.merchant.on_raft = True

            self.merchant.set_position(
                self.raft.x + 52,
                self.raft.y + 2
            )

            print("Merchant boarded raft")

    def _leave_raft(self):

        if not self.merchant.on_raft:
            return

        self.merchant.on_raft = False

        if self.raft.side == "left":

            self.merchant.set_position(
                200,
                self.raft.y
            )

        else:

            self.merchant.set_position(
                980,
                self.raft.y
            )

        print("Merchant left raft")

    def _place_on_raft(self):

        print("Trying to place cargo")
        print("On raft:", self.merchant.on_raft)

        if not self.merchant.carrying:
            return

        print("Merchant:", self.merchant.rect.center)
        print("Raft:", self.raft.rect.center)

        distance_x = abs(
            self.merchant.rect.centerx -
            self.raft.rect.centerx
        )

        distance_y = abs(
            self.merchant.rect.centery -
            self.raft.rect.centery
        )

        print("DX =", distance_x)
        print("DY =", distance_y)

        if distance_x > 180 or distance_y > 120:
            print("Too far from raft")
            return

        cargo = self.merchant.carrying

        cargo.set_position(
            int(self.raft.x + 50),
            int(self.raft.y + 20)
        )

        for slot in self.raft.slots:

            if slot.item is None:
                slot.item = cargo

                cargo.set_position(
                    slot.x + 15,
                    slot.y + 15
                )

                break

        self.merchant.carrying = None

        if self.snd_drop:
            self.snd_drop.play()

        print("Placed on raft:", cargo.name)

        self._unlock("first_load")

    def _drop_cargo(self):

        if not self.merchant.carrying:
            return

        cargo = self.merchant.carrying

        cargo.set_position(
            int(self.merchant.x),
            int(self.merchant.y + 40)
        )

        self.merchant.carrying = None

        if self.snd_drop:
            self.snd_drop.play()

        print("Dropped cargo")

    def _on_mouse_down(self, pos):
        if self.state == "loading":
            mx, my = pos
            for cargo in self.all_cargo:
                if cargo.rect.collidepoint(mx, my) and not cargo.on_raft:
                    self._dragging_cargo = cargo
                    cargo.start_drag(mx, my)
                    break

    def _on_mouse_up(self):
        if self.state == "loading" and self._dragging_cargo:
            cargo = self._dragging_cargo
            cargo.end_drag()

            mx, my = pygame.mouse.get_pos()
            for slot in self.raft.slots:
                if slot.contains_point(mx, my) and not slot.item:
                    if slot.add_item(cargo):
                        cargo.on_raft = True
                        cargo.dragging = False
                    break

            self._dragging_cargo = None

    def _on_mouse_move(self, pos):
        if self.state == "loading" and self._dragging_cargo:
            mx, my = pos
            self._dragging_cargo.update_drag(mx, my)



    # ── CROSSING HELPER ─────────────────────────────────────────
    def _start_crossing(self):

        if self.snd_raft:
            self.snd_raft.play()

        total_weight = self._get_total_raft_weight()

        print("TOTAL WEIGHT =", total_weight)

        if total_weight > self.raft_capacity:
            print("OVERLOADED!")

            self.raft.is_drowning = True

        self.state = "crossing"

        if self.raft.side == "left":

            target_x = 820

            self.raft.start_crossing(
                target_x,
                "right"
            )

            print("Crossing to RIGHT")

        else:

            target_x = 270

            self.raft.start_crossing(
                target_x,
                "left"
            )

            print("Crossing to LEFT")

    # ── UPDATE ──────────────────────────────────────────────────
    def _update(self, dt):
        self._menu_anim += dt

        self.river_offset += 40 * dt

        if self.river_offset >= SH:
            self.river_offset = 0

        if self.message_timer > 0:
            self.message_timer -= dt

        if self.state == "pause":
            return

        if self.state not in ("loading", "crossing"):
            return

        self.time_left -= dt
        if self.time_left <= 0:

            if self.snd_lose:
                self.snd_lose.play()

            self.time_left = 0
            self.state = "timeout"
            return

        # Update cargo
        for c in self.all_cargo:
            c.update(dt)

        if self.merchant.carrying:
            cargo = self.merchant.carrying

            cargo.set_position(
                int(self.merchant.x),
                int(self.merchant.y - 40)
            )

        self.merchant.clamp(
            0,
            SW - self.merchant.rect.width,
            0,
            SH - self.merchant.rect.height
        )

        if not self.merchant.on_raft:

            if self.raft.side == "left":

                if self.merchant.x > 220:
                    self.merchant.x = 220

            else:

                if self.merchant.x < 950:
                    self.merchant.x = 950

        self.merchant.update(dt)

        keys = pygame.key.get_pressed()

        self.merchant.state = "idle"

        keys = pygame.key.get_pressed()

        self.merchant.state = "idle"

        # Merchant can only walk when NOT on the raft
        if not self.merchant.on_raft:

            if keys[pygame.K_a]:
                self.merchant.move_left(dt)
                self.merchant.state = "walking"

            if keys[pygame.K_d]:
                self.merchant.move_right(dt)
                self.merchant.state = "walking"

            if keys[pygame.K_w]:
                self.merchant.move_up(dt)
                self.merchant.state = "walking"

            if keys[pygame.K_s]:
                self.merchant.move_down(dt)
                self.merchant.state = "walking"

        if self.state == "loading":
            self.raft.update(dt)

        elif self.state == "crossing":
            result = self.raft.update(dt)

            # Merchant follows raft
            self.merchant.set_position(
                int(self.raft.x) + 52,
                int(self.raft.y) + 2
            )

            if result == "drowned":

                if self.snd_lose:
                    self.snd_lose.play()

                self.drowned_count += 1
                self.state = "drowned"


            elif result == "success":

                print("Arrived at bank")

                self.state = "loading"

    # ── ACHIEVEMENTS ────────────────────────────────────────────
    def _unlock(self, aid):
        if aid not in self.unlocked:
            self.unlocked.add(aid)
            a = next((x for x in ACHIEVEMENTS if x["id"] == aid), None)



    # ── DRAW ────────────────────────────────────────────────────
    def _draw(self):
        self.screen.fill(C_BG)

        if self.state == "menu":
            self._draw_menu()
        elif self.state == "quit_confirm":
            self._draw_quit_confirm()
        elif self.state == "instructions":
            self._draw_instructions()
        elif self.state == "achievements":
            self._draw_achievements()
        elif self.state == "loading":
            self._draw_loading()
        elif self.state == "crossing":
            self._draw_crossing()
        elif self.state == "pause":
            self._draw_pause()
        elif self.state == "level_complete":
            self._draw_level_complete()
        elif self.state == "victory":
            self._draw_victory()

        elif self.state == "drowned":
            self._draw_drowned()

        elif self.state == "timeout":
            self._draw_timeout()

    def _draw_background(self):

        # Draw left bank
        self.screen.blit(
            pygame.transform.scale(
                self.img["bank_left"],
                (LEFT_BANK_W, SH)
            ),
            (0, 0)
        )

        # Draw moving river
        river = pygame.transform.scale(
            self.img["river"],
            (RIVER_W, SH)
        )

        offset = int(self.river_offset)

        self.screen.blit(
            river,
            (LEFT_BANK_W, offset - SH)
        )

        self.screen.blit(
            river,
            (LEFT_BANK_W, offset)
        )

        # Draw right bank
        self.screen.blit(
            pygame.transform.scale(
                self.img["bank_right"],
                (RIGHT_BANK_W, SH)
            ),
            (RIGHT_BANK_X, 0)
        )

    def _draw_loading(self):
        """Loading state: arrange cargo on raft."""
        self._draw_background()

        # Draw cargo on left bank
        for c in self.all_cargo:

            if c.delivered:
                continue

            if not c.on_raft:
                c.draw(self.screen)

        # Draw merchant only if on land
        if not self.merchant.on_raft:
            self.merchant.draw(self.screen)

        # Draw raft
        self.raft.draw(self.screen)

        # Draw merchant on top of raft
        if self.merchant.on_raft:
            old_y = self.merchant.y

            self.merchant.y += self.raft._bob

            self.merchant.draw(self.screen)

            self.merchant.y = old_y

        for cargo in self.raft.cargo_on_raft:
            cargo.draw(self.screen)

        # Draw cargo on raft
        for slot in self.raft.slots:
            if slot.item:
                item_x = slot.x + (slot.width - slot.item.image.get_width()) // 2
                item_y = (
                        slot.y
                        + self.raft._bob
                        + (slot.height - slot.item.image.get_height()) // 2
                )
                self.screen.blit(slot.item.image, (item_x, item_y))

        total_load = self.raft.get_total_weight(
            self.merchant.on_raft
        )

        delivered = 0

        for cargo in self.all_cargo:

            if cargo.delivered:
                delivered += 1

        # ---------- STATUS PANEL ----------
        panel = pygame.Surface((320, 115), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 170))
        self.screen.blit(panel, (SW // 2 - 160, 12))

        pygame.draw.rect(
            self.screen,
            C_GOLD,
            pygame.Rect(SW // 2 - 160, 12, 320, 115),
            2,
            border_radius=8
        )

        # Status text
        if total_load <= 100:
            status_text = "SAFE TO CROSS"
            status_color = C_GREEN
        else:
            status_text = "OVERLOAD! RAFT WILL SINK"
            status_color = C_RED

        self._txt_c(
            f"LOAD : {total_load}/100 kg",
            self.fnt_lg,
            C_GOLD,
            SW // 2,
            25
        )

        self._txt_c(
            status_text,
            self.fnt_md,
            status_color,
            SW // 2,
            58
        )

        self._txt_c(
            f"Delivered : {delivered}/{len(self.all_cargo)}",
            self.fnt_md,
            C_WARN,
            SW // 2,
            88
        )

        # Time Panel
        panel = pygame.Surface((170, 45), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 170))
        self.screen.blit(panel, (15, 10))

        pygame.draw.rect(
            self.screen,
            C_GOLD,
            pygame.Rect(15, 10, 170, 45),
            2,
            border_radius=8
        )

        self._txt(
            f"Time : {int(self.time_left)} s",
            self.fnt_md,
            C_WHITE,
            (30, 22)
        )

        # ---------- CONTROLS PANEL ----------
        panel = pygame.Surface((240, 165), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 170))
        self.screen.blit(panel, (10, SH - 185))

        pygame.draw.rect(
            self.screen,
            C_GOLD,
            pygame.Rect(10, SH - 185, 240, 165),
            2,
            border_radius=8
        )

        self._txt("CONTROLS", self.fnt_md, C_GOLD, (25, SH - 175))

        self._txt("WASD  - Move", self.fnt_sm, C_WHITE, (25, SH - 145))
        self._txt("E     - Pick / Drop", self.fnt_sm, C_WHITE, (25, SH - 120))
        self._txt("SPACE - Board / Leave", self.fnt_sm, C_WHITE, (25, SH - 95))
        self._txt("F     - Cross River", self.fnt_sm, C_WHITE, (25, SH - 70))
        self._txt("ESC   - Pause", self.fnt_sm, C_WHITE, (25, SH - 45))

        # Instructions
        self._txt_c("Keep the raft balanced before crossing.",
                    self.fnt_sm, C_TEXT, SW // 2, SH - 30)

        if self.message_timer > 0:
            self._txt_c(
                self.message,
                self.fnt_md,
                C_RED,
                SW // 2,
                SH - 55
            )



    def _draw_crossing(self):
        """Crossing state: merchant crossing river."""
        self._draw_background()

        # Draw raft
        self.raft.draw(self.screen)

        # Draw cargo on raft
        for slot in self.raft.slots:
            if slot.item:
                item_x = slot.x + (slot.width - slot.item.image.get_width()) // 2
                item_y = slot.y + (slot.height - slot.item.image.get_height()) // 2
                self.screen.blit(slot.item.image, (item_x, item_y))



        # Draw merchant on raft
        if self.merchant.on_raft:
            old_y = self.merchant.y

            self.merchant.y += self.raft._bob

            self.merchant.draw(self.screen)

            self.merchant.y = old_y

        total_load = self.raft.get_total_weight(True)

        delivered = 0

        for cargo in self.all_cargo:
            if cargo.delivered:
                delivered += 1

        # ---------- STATUS PANEL ----------
        panel = pygame.Surface((320, 115), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 170))
        self.screen.blit(panel, (SW // 2 - 160, 12))

        pygame.draw.rect(
            self.screen,
            C_GOLD,
            pygame.Rect(SW // 2 - 160, 12, 320, 115),
            2,
            border_radius=8
        )

        # Status text
        if total_load <= 100:
            status_text = "SAFE TO CROSS"
            status_color = C_GREEN
        else:
            status_text = "OVERLOAD! RAFT WILL SINK"
            status_color = C_RED

        self._txt_c(
            f"LOAD : {total_load}/100 kg",
            self.fnt_lg,
            C_GOLD,
            SW // 2,
            25
        )

        self._txt_c(
            status_text,
            self.fnt_md,
            status_color,
            SW // 2,
            58
        )

        self._txt_c(
            f"Delivered : {delivered}/{len(self.all_cargo)}",
            self.fnt_md,
            C_WARN,
            SW // 2,
            88
        )

        # Time Panel
        panel = pygame.Surface((170, 45), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 170))
        self.screen.blit(panel, (15, 10))

        pygame.draw.rect(
            self.screen,
            C_GOLD,
            pygame.Rect(15, 10, 170, 45),
            2,
            border_radius=8
        )

        self._txt(
            f"Time : {int(self.time_left)} s",
            self.fnt_md,
            C_WHITE,
            (30, 22)
        )

        # ---------- CONTROLS PANEL ----------
        panel = pygame.Surface((240, 165), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 170))
        self.screen.blit(panel, (10, SH - 185))

        pygame.draw.rect(
            self.screen,
            C_GOLD,
            pygame.Rect(10, SH - 185, 240, 165),
            2,
            border_radius=8
        )

        self._txt("CONTROLS", self.fnt_md, C_GOLD, (25, SH - 175))

        self._txt("WASD  - Move", self.fnt_sm, C_WHITE, (25, SH - 145))
        self._txt("E     - Pick / Drop", self.fnt_sm, C_WHITE, (25, SH - 120))
        self._txt("SPACE - Board / Leave", self.fnt_sm, C_WHITE, (25, SH - 95))
        self._txt("F     - Cross River", self.fnt_sm, C_WHITE, (25, SH - 70))
        self._txt("ESC   - Pause", self.fnt_sm, C_WHITE, (25, SH - 45))

        # Instructions
        self._txt_c(
            "Keep the raft balanced before crossing.",
            self.fnt_sm,
            C_TEXT,
            SW // 2,
            SH - 30
        )

    def _draw_victory(self):
        """Victory screen."""
        self._draw_background()

        ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        self.screen.blit(ov, (0, 0))

        bob = int(math.sin(self._menu_anim * 3) * 5)
        self._txt_c("CARGO DELIVERED!", self.fnt_xl, C_GOLD,
                    SW // 2, 200 + bob)
        self._txt_c("You safely crossed the river!", self.fnt_md, C_GREEN,
                    SW // 2, 280)
        self._txt_c(f"Score: {self.score} pts", self.fnt_lg, C_GOLD, SW // 2, 340)
        self._txt_c(f"Time: {int(self.time_left)}s  |  Trips: {self.trips}",
                    self.fnt_md, C_TEXT, SW // 2, 390)
        self._txt_c("[R] Play Again  |  [ESC] Menu", self.fnt_md, C_TEXT,
                    SW // 2, 450)

    def _draw_level_complete(self):

        self._draw_background()

        ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        self.screen.blit(ov, (0, 0))

        self._txt_c(
            f"LEVEL {self.level} COMPLETE!",
            self.fnt_xl,
            C_GOLD,
            SW // 2,
            200
        )

        self._txt_c(
            f"Prepare for Level {self.level + 1}",
            self.fnt_md,
            C_GREEN,
            SW // 2,
            290
        )

        self._txt_c(
            "[SPACE] Next Level",
            self.fnt_md,
            C_WHITE,
            SW // 2,
            380
        )

        self._txt_c(
            "[ESC] Main Menu",
            self.fnt_sm,
            C_TEXT,
            SW // 2,
            430
        )

    def _draw_drowned(self):
        """Drowned screen."""
        self._draw_background()

        ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 165))
        self.screen.blit(ov, (0, 0))

        self._txt_c(" RAFT CAPSIZED! ", self.fnt_xl, C_RED, SW // 2, 200)
        self._txt_c("The raft was too imbalanced!", self.fnt_md, C_WARN, SW // 2, 280)
        self._txt_c(f"Score: {self.score} pts", self.fnt_lg, C_GOLD, SW // 2, 340)
        self._txt_c("[R] Try Again  |  [ESC] Menu", self.fnt_md, C_TEXT, SW // 2, 400)

    def _draw_timeout(self):

        self._draw_background()

        ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 165))
        self.screen.blit(ov, (0, 0))

        self._txt_c(
            "⏰ TIME'S UP! ⏰",
            self.fnt_xl,
            C_WARN,
            SW // 2,
            200
        )

        self._txt_c(
            "You failed to deliver all cargo in time!",
            self.fnt_md,
            C_WHITE,
            SW // 2,
            280
        )

        self._txt_c(
            f"Score: {self.score} pts",
            self.fnt_lg,
            C_GOLD,
            SW // 2,
            340
        )

        self._txt_c(
            "[R] Try Again  |  [ESC] Menu",
            self.fnt_md,
            C_TEXT,
            SW // 2,
            400
        )

    def _draw_pause(self):

        self._draw_background()

        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(260, 120, 560, 360)

        pygame.draw.rect(
            self.screen,
            (25, 25, 25),
            panel,
            border_radius=15
        )

        pygame.draw.rect(
            self.screen,
            C_GOLD,
            panel,
            3,
            border_radius=15
        )



        self._txt_c(
            "GAME PAUSED",
            self.fnt_xl,
            C_GOLD,
            SW // 2 - 80,
            160
        )

        self._txt(
            "[C] Continue Game",
            self.fnt_md,
            C_WHITE,
            (430, 245)
        )

        self._txt(
            "[R] Restart Game",
            self.fnt_md,
            C_WHITE,
            (430, 295)
        )

        self._txt(
            "[M] Return to Menu",
            self.fnt_md,
            C_WHITE,
            (430, 345)
        )

        self._txt(
            "Game progress is paused.",
            self.fnt_sm,
            C_TEXT,
            (430, 400)
        )

    def _draw_menu(self):

        self._draw_background()

        ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 140))
        self.screen.blit(ov, (0, 0))

        cx = SW // 2

        self._txt_c(
            " ANCIENT RIVER ADVENTURE ",
            self.fnt_xl,
            C_GOLD,
            cx,
            90
        )

        self._txt_c(
            "Deliver all cargo before time runs out!",
            self.fnt_md,
            C_TEXT,
            cx,
            150
        )

        self._txt_c(
            "Guide the merchant across the river safely.",
            self.fnt_sm,
            C_GREEN,
            cx,
            190
        )

        opts = [
            ("[ENTER]", "Start Game", C_GREEN),
            ("[I]", "Instructions", C_TEXT),
            ("[A]", "Achievements", C_GOLD),
            ("[ESC]", "Quit", C_RED)
        ]

        for i, (key, lbl, col) in enumerate(opts):
            y = 280 + i * 70
            self._txt_c(
                f"{key}  {lbl}",
                self.fnt_md,
                col,
                cx,
                y
            )

        self._txt_c(
            "Merchant: 50kg   |   Raft Capacity: 100kg",
            self.fnt_sm,
            C_WARN,
            cx,
            SH - 70
        )

        self._txt_c(
            "Can you unlock all achievements?",
            self.fnt_sm,
            C_GOLD,
            cx,
            SH - 40
        )

    def _draw_quit_confirm(self):

        # Draw the normal menu first
        self._draw_menu()

        # Dark overlay
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Popup box
        box = pygame.Rect(360, 220, 560, 260)
        pygame.draw.rect(self.screen, (30, 30, 30), box, border_radius=12)
        pygame.draw.rect(self.screen, C_GOLD, box, 3, border_radius=12)

        cx = box.centerx

        self._txt_c(
            "Exit Game?",
            self.fnt_lg,
            C_GOLD,
            cx,
            box.y + 40
        )

        self._txt_c(
            "Are you sure you want to quit?",
            self.fnt_md,
            C_TEXT,
            cx,
            box.y + 105
        )

        self._txt_c(
            "[ENTER] Exit Game",
            self.fnt_md,
            C_GREEN,
            cx,
            box.y + 165
        )

        self._txt_c(
            "[ESC] Cancel",
            self.fnt_md,
            C_RED,
            cx,
            box.y + 205
        )

    def _draw_instructions(self):
        self._draw_background()

        ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        self.screen.blit(ov, (0, 0))
        cx = SW // 2
        # Main instruction panel
        panel = pygame.Rect(140, 45, SW - 280, 610)

        pygame.draw.rect(
            self.screen,
            (25, 25, 25),
            panel,
            border_radius=15
        )

        pygame.draw.rect(
            self.screen,
            C_GOLD,
            panel,
            3,
            border_radius=15
        )
        self._txt_c("HOW TO PLAY", self.fnt_lg, C_GOLD, cx, 60)

        # ---------- LEFT COLUMN ----------
        lx = 170
        rx = 720

        # GOAL
        self._txt("► GOAL", self.fnt_md, C_GOLD, (lx, 110))
        self._txt("Deliver all cargo before", self.fnt_sm, C_TEXT, (lx + 20, 145))
        self._txt("time runs out.", self.fnt_sm, C_TEXT, (lx + 20, 170))
        self._txt("Avoid overloading the raft.", self.fnt_sm, C_TEXT, (lx + 20, 195))

        # WEIGHT RULES
        self._txt("► WEIGHT RULES", self.fnt_md, C_GOLD, (lx, 250))
        self._txt("Merchant : 50kg", self.fnt_sm, C_TEXT, (lx + 20, 285))
        self._txt("Raft : 100kg", self.fnt_sm, C_TEXT, (lx + 20, 310))

        # WIN
        self._txt("► WIN", self.fnt_md, C_GOLD, (lx, 390))
        self._txt("Deliver all required", self.fnt_sm, C_TEXT, (lx + 20, 425))
        self._txt("cargo in each level.", self.fnt_sm, C_TEXT, (lx + 20, 450))

        # ---------- RIGHT COLUMN ----------

        # CONTROLS
        self._txt("► CONTROLS", self.fnt_md, C_GOLD, (rx, 110))
        self._txt("WASD  - Move", self.fnt_sm, C_TEXT, (rx + 20, 145))
        self._txt("E     - Pick / Drop", self.fnt_sm, C_TEXT, (rx + 20, 170))
        self._txt("SPACE - Board / Leave", self.fnt_sm, C_TEXT, (rx + 20, 195))
        self._txt("F     - Cross River", self.fnt_sm, C_TEXT, (rx + 20, 220))
        self._txt("ESC   - Pause", self.fnt_sm, C_TEXT, (rx + 20, 245))

        # CARGO
        self._txt("► CARGO", self.fnt_md, C_GOLD, (rx, 320))
        self._txt("Food      20kg", self.fnt_sm, C_TEXT, (rx + 20, 355))
        self._txt("Cloth     25kg", self.fnt_sm, C_TEXT, (rx + 20, 380))
        self._txt("Medicine  30kg", self.fnt_sm, C_TEXT, (rx + 20, 405))
        self._txt("Weapons   35kg", self.fnt_sm, C_TEXT, (rx + 20, 430))

        # LOSE
        self._txt("► LOSE", self.fnt_md, C_GOLD, (rx, 500))
        self._txt("Raft overloaded", self.fnt_sm, C_TEXT, (rx + 20, 535))
        self._txt("OR", self.fnt_sm, C_TEXT, (rx + 20, 560))
        self._txt("Time runs out", self.fnt_sm, C_TEXT, (rx + 20, 585))

        # Bottom
        self._txt_c(
            "Press ESC to return to the Main Menu",
            self.fnt_sm,
            C_BLUE,
            SW // 2,
            625
        )

    def _draw_achievements(self):
        self._draw_background()

        ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        self.screen.blit(ov, (0, 0))

        cx = SW // 2

        panel = pygame.Rect(140, 45, SW - 280, 610)

        pygame.draw.rect(
            self.screen,
            (25, 25, 25),
            panel,
            border_radius=15
        )

        pygame.draw.rect(
            self.screen,
            C_GOLD,
            panel,
            3,
            border_radius=15
        )
        self._txt_c("ACHIEVEMENTS", self.fnt_lg, C_GOLD, cx, 60)
        self._txt_c(
            f"Progress : {len(self.unlocked)} / {len(ACHIEVEMENTS)} Unlocked",
            self.fnt_md,
            C_TEXT,
            cx,
            105
        )

        for i, a in enumerate(ACHIEVEMENTS):
            done = a["id"] in self.unlocked
            y = 165 + i * 95
            col = (255, 215, 0) if done else (120, 120, 120)
            self._txt(
                a["name"],
                self.fnt_md,
                col,
                (250, y)
            )
            self._txt(a["desc"], self.fnt_sm, (220, 210, 170) if done else (80, 80, 80),
                      (250, y + 35))

            pygame.draw.line(
                self.screen,
                (70, 70, 70),
                (250, y + 60),
                (1050, y + 60),
                1
            )

        self._txt_c(
            "Press ESC to return to the Main Menu",
            self.fnt_sm,
            C_BLUE,
            cx,
            625
        )

    # ── TEXT HELPERS ────────────────────────────────────────────
    def _txt(self, text, font, col, pos):
        self.screen.blit(font.render(text, True, col), pos)

    def _txt_c(self, text, font, col, cx, y):
        s = font.render(text, True, col)
        self.screen.blit(s, (cx - s.get_width() // 2, y))
