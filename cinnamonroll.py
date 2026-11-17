#!/usr/bin/env python3

import math
import random
import time
import tkinter as tk
from tkinter import font as tkfont

ART = r"""
                                                      ==
                                           =+*%@@@@@@@@@@@@@@#+===
                                        =@@@@@@@@@@@@@@@@@@@@@@@@@@*-
                                =*@@@*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@+=+=
                            =%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#=
                           +@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@=
                          =@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@=
                         #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@=
                       -@@@@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@=
                      =@@@@@%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@+@@@=
                     =@@@@@%=@@@@@@@#***@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@**#@@@@@=@@@=
                     #@@@%%=@@@@@@@*@#***@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#@#**@@@@#@@@@
                    =@@%%%#===#@@@@******@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*****@@@@@=%@@=
                   =@@@%+=@@@@@@=@@#****%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@****#@@@@@*@@@=
                   @@@@%=@@@@@@@@=@#***%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@***@@@@@@=@@@+
                  =@@@@%=@@@@@@@@=+@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%-%@@@=
                 =@@@@@#=@@@@@@@@@=%%@@@@@@@@@@@@@+@@@@%*#@@@@*@@@@@@@@@@@@%%%%%%%-%@@@%
                 @@@@@@%-@@@@@@@@@=##%@@@%%@@@@@@@@##%@@@@@%##@@@@@@@@@@@%%%%###*#=@@@@@+
                %@@@@@@%-@@@@@@@@@-**########%%%%%%%%%%%%%%%%%%%%%%%%%#####*****##=@@@@@@+
               %@@@@@@@%-@@@@@@@@@-#############################################-#%@@@@@@@=
              %@@@@@@@%=-%@@@@@@@@++==--+#####################################++##%@@@@@@@@+
             %@@@@@=+@@@=%@@@@@@@@%+@@@@@@-#################################=-####%%%@@@@@@@=
            %@@@@@++@@@@=%@@@@@@@@%@@@@@@@*@@@==#######################=--*########%%%@@@@@@@=
           @@@@@@%=@@@@@+@@@@@@@@@@@@@@@@@@@@@@@=*#########*+=+*#%@@@@=   *#########%%%@@@@@@=
          -%@@@@=-@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@=@@@@@@@@@@@@@@@@@@@@@@@+ =###########%%%%@@@-
          -#%%===@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@=@@@@@@@@@@@@@@@@@@@@@@@@@ =#############%%%#-
          -##-@@=+@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@+%@@@@@@@@@@@@@@@@@@@%%@@@@+=################-
           **-@@@%%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@#+@@@@@@@@@@@@@@@@@@@@*#@@@@  *############=
            -#%@@@###@@@@@%%%@@@@@@@@@@@@@@@@@%#*+@@@@@@@@@@@@@@@@@@@@=###%#     =########-
             -#%@@####@@@@@@@@@@@@@@@@@@@@@%%%##=@@@@@@@@@@@@@@@@@@@@@@+###=
              -##%%####@%%%%%%%%%%%%%%%@@@%%####=@@@@@@@@@@@@@@@@@@@@@@+
               -##%####################%%#######=@@@@@@@@@@@@@@@@@@@@@%=
                -##############################=@@@@@@@@@@@@@@@@@@@@@%#-
                 -+##########################*-@@@@@@@@@@@@@@@@@@@@%%##=
                   -+#######################-+@@@@@@@@@@@@@@@@@@%%%###=
                     -*###################*-#%%%%%%@%%%%%%%%%%######*-
                       ---=*#########+--=###########################++
                                ---    ##########################-=*-
                                       -#%%#*##############*#=-*###=
                                        ##%%%%#*--=-----
                                        =#######=
                                         =*###*=
"""

# ---------------------------------------------------------------- settings
W, H = 860, 760
FONT_SIZE = 8
CHUNK = 6            # columns per independently-moving chunk
FPS = 30
SKY_TOP, SKY_BOT = "#5aa9f0", "#c4e6ff"

CHAR_COLORS = {
    "@": "#ffffff",
    "%": "#ffdff0",   # soft pink shading
    "#": "#e2f0ff",   # pale blue body shading
    "*": "#ffffff",
    "+": "#d4eaff",
    "=": "#4f8fe0",   # outline blue
    "-": "#7db3ee",
}
EYE_COLOR = "#1d4fd7"


def lerp_color(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class App:
    def __init__(self, root):
        self.root = root
        root.title("cinnamoroll ☁")
        root.resizable(False, False)
        root.bind("<Escape>", lambda e: root.destroy())

        self.c = tk.Canvas(root, width=W, height=H, highlightthickness=0, bg=SKY_TOP)
        self.c.pack()
        self.c.bind("<Button-1>", self.on_click)

        self.lines = [l.rstrip() for l in ART.split("\n")]
        while self.lines and not self.lines[0].strip():
            self.lines.pop(0)
        while self.lines and not self.lines[-1].strip():
            self.lines.pop()
        self.rows = len(self.lines)
        self.cols = max(len(l) for l in self.lines)

        self.font = tkfont.Font(family="Courier", size=FONT_SIZE, weight="bold")
        self.cw = self.font.measure("@")
        self.lh = self.font.metrics("linespace")
        self.x0 = (W - self.cols * self.cw) / 2
        self.y0 = 110

        self.build_background()
        self.build_clouds()
        self.build_stars()
        self.build_shadow()
        self.build_sprite()
        self.build_title()

        self.hearts = []
        self.next_heart = 0.5
        self.flap_phase = 0.0
        self.jump_start = None
        self.blink_until = 0.0
        self.next_blink = 2.0
        self.blinking = False
        self.t0 = self.last = time.perf_counter()
        self.tick()

    # ------------------------------------------------------------- scene
    def build_background(self):
        n = 60
        for i in range(n):
            y = i * H / n
            self.c.create_rectangle(0, y, W, y + H / n + 1, outline="",
                                    fill=lerp_color(SKY_TOP, SKY_BOT, i / (n - 1)), tags="bg")

    def build_clouds(self):
        self.clouds = []
        for i, (x, y, s, v) in enumerate([(80, 140, 1.0, 10), (560, 80, 1.3, 6),
                                          (700, 330, 0.8, 14), (-40, 520, 1.1, 8)]):
            tag = f"cloud{i}"
            for dx, dy, r in [(0, 0, 34), (36, -14, 42), (82, 0, 34), (40, 12, 38), (18, 8, 30), (62, 10, 30)]:
                self.c.create_oval(x + (dx - r) * s, y + (dy - r * 0.6) * s,
                                   x + (dx + r) * s, y + (dy + r * 0.6) * s,
                                   fill="#f4faff", outline="", tags=tag)
            self.clouds.append((tag, v))

    def build_stars(self):
        self.stars = []
        for _ in range(22):
            x, y = random.randint(20, W - 20), random.randint(20, H - 160)
            ch = random.choice(["✦", "✧", "·", "+"])
            item = self.c.create_text(x, y, text=ch, fill="#ffffff",
                                      font=("Helvetica", random.randint(9, 16)))
            self.stars.append((item, random.uniform(0, 6.28), random.uniform(1.5, 3.5)))

    def build_shadow(self):
        self.shadow_y = self.y0 + self.rows * self.lh + 6
        self.shadow = self.c.create_oval(W / 2 - 150, self.shadow_y - 12, W / 2 + 150,
                                         self.shadow_y + 12, fill="#82b9ec", outline="")

    def build_sprite(self):
        self.chunk_tags = {}
        self.chunk_off = {}
        self.eyes = []  # (item, row, col, ch)

        # find the eye characters: '*' in the face rows, plus '#' touching them
        star_rows = {r: [c for c, ch in enumerate(self.lines[r]) if ch == "*" and 30 <= c <= 78]
                     for r in range(9, min(15, self.rows))}
        self.eye_mid = max(star_rows, key=lambda r: len(star_rows[r]))
        eye_cells = set()
        for r, cs in star_rows.items():
            for c in cs:
                eye_cells.add((r, c))
        for r in star_rows:
            line = self.lines[r]
            for c, ch in enumerate(line):
                if ch == "#" and ((r, c - 1) in eye_cells or (r, c + 1) in eye_cells):
                    eye_cells.add((r, c))

        for r, line in enumerate(self.lines):
            for c, ch in enumerate(line):
                if ch == " ":
                    continue
                tag = f"k{r}_{c // CHUNK}"
                if tag not in self.chunk_tags:
                    self.chunk_tags[tag] = (r, c // CHUNK * CHUNK + CHUNK / 2)
                    self.chunk_off[tag] = (0.0, 0.0)
                is_eye = (r, c) in eye_cells
                item = self.c.create_text(self.x0 + c * self.cw, self.y0 + r * self.lh,
                                          text=ch, anchor="nw", font=self.font,
                                          fill=EYE_COLOR if is_eye else CHAR_COLORS.get(ch, "#fff"),
                                          tags=(tag,))
                if is_eye:
                    self.eyes.append((item, r, c, ch))

    def build_title(self):
        self.c.create_text(W / 2, 46, text="cinnamoroll", fill="#ffffff",
                           font=("Helvetica", 30, "bold"))
        self.c.create_text(W / 2, 80, text="♥  click me  ♥", fill="#fff3fa",
                           font=("Helvetica", 12))

    # ---------------------------------------------------------- interaction
    def on_click(self, e):
        self.jump_start = time.perf_counter()
        for _ in range(8):
            self.spawn_heart(e.x + random.randint(-30, 30), e.y + random.randint(-20, 20), burst=True)

    def spawn_heart(self, x, y, burst=False):
        size = random.randint(12, 24)
        item = self.c.create_text(x, y, text="♥", fill="#ff6fa8", font=("Helvetica", size))
        self.hearts.append({
            "id": item, "x": x, "y": y, "age": 0.0,
            "life": random.uniform(1.8, 3.0),
            "vy": random.uniform(50, 110) if not burst else random.uniform(80, 170),
            "vx": random.uniform(-40, 40) if burst else 0,
            "ph": random.uniform(0, 6.28),
        })

    # ---------------------------------------------------------------- loop
    def set_blink(self, closed):
        if closed == self.blinking:
            return
        self.blinking = closed
        for item, r, c, ch in self.eyes:
            if closed:
                if r == self.eye_mid:
                    self.c.itemconfig(item, text="-", fill=EYE_COLOR)
                else:
                    self.c.itemconfig(item, text="@", fill="#ffffff")
            else:
                self.c.itemconfig(item, text=ch, fill=EYE_COLOR)

    def tick(self):
        now = time.perf_counter()
        t = now - self.t0
        dt = min(now - self.last, 0.1)
        self.last = now

        # jump envelope
        jump = 0.0
        env = 0.0
        if self.jump_start is not None:
            p = (now - self.jump_start) / 0.7
            if p >= 1:
                self.jump_start = None
            else:
                env = math.sin(math.pi * p)
                jump = -48 * env

        # ear flap (phase integrated so speed changes stay smooth)
        self.flap_phase += (3.0 + 12.0 * env) * dt
        flap = (math.sin(self.flap_phase) + 1) / 2
        flap_amp = 0.35 + 0.65 * env

        bob = math.sin(t * 2.2) * 7
        sway = math.sin(t * 1.1) * 4

        # move chunks
        for tag, (r, cc) in self.chunk_tags.items():
            col_dist = (cc - self.cols / 2) / (self.cols / 2)
            ear_w = max(0.0, abs(col_dist) - 0.3) / 0.7
            rowf = min(1.0, max(0.0, (r - 14) / 6.0))
            ear = ear_w * rowf * flap * flap_amp
            dy = bob + jump - ear * 16
            dx = sway * (1 - 0.6 * r / self.rows) + math.copysign(1, col_dist) * ear * 7
            px, py = self.chunk_off[tag]
            if abs(dx - px) > 0.05 or abs(dy - py) > 0.05:
                self.c.move(tag, dx - px, dy - py)
                self.chunk_off[tag] = (dx, dy)

        # shadow breathes with height
        lift = -(bob + jump)
        scale = max(0.55, 1 - lift / 160)
        self.c.coords(self.shadow, W / 2 - 150 * scale, self.shadow_y - 12 * scale,
                      W / 2 + 150 * scale, self.shadow_y + 12 * scale)

        # blinking
        if not self.blinking and t > self.next_blink:
            self.set_blink(True)
            self.blink_until = t + 0.14
        elif self.blinking and t > self.blink_until:
            self.set_blink(False)
            self.next_blink = t + (0.25 if random.random() < 0.2 else random.uniform(2.5, 5.0))

        # clouds
        for tag, v in self.clouds:
            self.c.move(tag, v * dt, 0)
            bb = self.c.bbox(tag)
            if bb and bb[0] > W + 20:
                self.c.move(tag, -(bb[2] - bb[0]) - W - 40, 0)

        # stars
        for item, ph, sp in self.stars:
            k = (math.sin(t * sp + ph) + 1) / 2
            self.c.itemconfig(item, fill=lerp_color("#8ec9ff", "#ffffff", k))

        # hearts
        self.next_heart -= dt
        if self.next_heart <= 0:
            self.next_heart = random.uniform(0.5, 1.2)
            side = random.choice([-1, 1])
            self.spawn_heart(W / 2 + side * random.randint(150, 330), self.y0 + random.randint(150, 450))
        alive = []
        for h in self.hearts:
            h["age"] += dt
            if h["age"] >= h["life"]:
                self.c.delete(h["id"])
                continue
            h["y"] -= h["vy"] * dt
            h["x"] += (h["vx"] + math.sin(h["age"] * 3 + h["ph"]) * 25) * dt
            self.c.coords(h["id"], h["x"], h["y"])
            self.c.itemconfig(h["id"], fill=lerp_color("#ff5f9e", "#cfe9ff", h["age"] / h["life"]))
            alive.append(h)
        self.hearts = alive

        self.root.after(int(1000 / FPS), self.tick)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()