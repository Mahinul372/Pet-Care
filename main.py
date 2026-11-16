# Buddy's Q-Learning Treasure Hunt -- an interactive Q-Learning demo.
#
# Buddy the dog learns to find a hidden bone in a garden, using real
# tabular Q-learning (see the rl/ package). There is no scripted route:
# every move Buddy makes comes from his Q-table, which he updates as he
# trains. The right-hand panel explains Q-Learning with live numbers
# from the actual training run.
#
# The old pet-care mechanics (hunger, health, energy, sleep, feeding)
# are gone on purpose: nothing here decays over time, so you can pause,
# read, and inspect the Q-table for as long as you like.
#
# Controls:
#   Mouse .......... buttons, and click a garden square to inspect its
#                    Q-values (or place the bone / edit the garden in
#                    the matching mode)
#   SPACE .......... pause / resume training
#   R .............. reset training (fresh Q-table)
#   F .............. fast-train 500 episodes
#   C .............. start the challenge (Buddy uses his learned policy)
#   S .............. save the Q-table now
#   Q .............. save and quit
#
# Run:  pip install PyOpenGL
#       python main.py

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import os
import random
import sys
import time

from rl.environment import GardenEnv, ACTIONS, MAX_STEPS
from rl.agent import QLearningAgent
from rl.train import run_episode
from rl.evaluate import greedy_path

WIDTH, HEIGHT = 1280, 800
xaxis = WIDTH / 2      # 640
yaxis = HEIGHT / 2     # 400

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "rl", "q_table.pkl")

# ---------------------------------------------------------------------------
# Drawing helpers carried over from the original game (same midpoint
# line/circle algorithms, same point-plotting style). The dog below is
# the original Buddy, unchanged -- same shapes, colours and proportions.
# ---------------------------------------------------------------------------

def findzone(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if abs(dx) > abs(dy):
        if (dx >= 0 and dy >= 0):
            zone = 0
        elif (dx <= 0 and dy >= 0):
            zone = 3
        elif (dx <= 0 and dy <= 0):
            zone = 4
        elif (dx >= 0 and dy <= 0):
            zone = 7
    else:
        if (dx >= 0 and dy >= 0):
            zone = 1
        elif (dx <= 0 and dy >= 0):
            zone = 2
        elif (dx <= 0 and dy <= 0):
            zone = 5
        elif (dx >= 0 and dy <= 0):
            zone = 6
    return zone

def zone0(zone, x, y):
    if zone == 0:
        x1 = x
        y1 = y
    elif zone == 1:
        x1 = y
        y1 = x
    elif zone == 2:
        x1 = y
        y1 = -x
    elif zone == 3:
        x1 = -x
        y1 = y
    elif zone == 4:
        x1 = -x
        y1 = -y
    elif zone == 5:
        x1 = -y
        y1 = -x
    elif zone == 6:
        x1 = -y
        y1 = x
    elif zone == 7:
        x1 = x
        y1 = -y
    return (x1, y1)

def originalzone(zone, x, y):
    if zone == 0:
        x1 = x
        y1 = y
    elif zone == 1:
        x1 = y
        y1 = x
    elif zone == 2:
        x1 = -y
        y1 = x
    elif zone == 3:
        x1 = -x
        y1 = y
    elif zone == 4:
        x1 = -x
        y1 = -y
    elif zone == 5:
        x1 = -y
        y1 = -x
    elif zone == 6:
        x1 = y
        y1 = -x
    elif zone == 7:
        x1 = x
        y1 = -y
    return (x1, y1)

def draw_line(x1, y1, x2, y2):
    zone = findzone(x1, y1, x2, y2)
    x1, y1 = zone0(zone, x1, y1)
    x2, y2 = zone0(zone, x2, y2)
    dx = x2 - x1
    dy = y2 - y1
    d = 2 * dy - dx
    x = x1
    y = y1
    glBegin(GL_POINTS)
    while x < x2:
        xo, yo = originalzone(zone, x, y)
        glVertex2f(xo / xaxis, yo / yaxis)
        x += 1
        if d < 0:
            d += 2 * dy
        else:
            d += 2 * (dy - dx)
            y += 1
    glEnd()

def circle(radius, center):
    """Midpoint circle, all points in one glBegin/glEnd block."""
    d = 1 - radius
    x = 0
    y = radius
    glBegin(GL_POINTS)
    _circle_octants(x, y, center)
    while (x < y):
        if (d < 0):
            d = d + 2 * x + 3
            x += 1
        else:
            d = d + 2 * x - 2 * y + 5
            x += 1
            y -= 1
        _circle_octants(x, y, center)
    glEnd()

def _circle_octants(x, y, center):
    x0 = x / xaxis
    y0 = y / yaxis
    ax = center[0] / xaxis
    ay = center[1] / yaxis
    glVertex2f(x0 + ax, y0 + ay)
    glVertex2f(y0 + ax, x0 + ay)
    glVertex2f(y0 + ax, -x0 + ay)
    glVertex2f(x0 + ax, -y0 + ay)
    glVertex2f(-x0 + ax, -y0 + ay)
    glVertex2f(-y0 + ax, -x0 + ay)
    glVertex2f(-y0 + ax, x0 + ay)
    glVertex2f(-x0 + ax, y0 + ay)

def filled_circle(radius, center):
    """A solid disc, drawn as concentric midpoint circles."""
    r = radius
    while r > 0:
        circle(r, center)
        r -= 2
    circle(1, center)

def fill_rect(x1, y1, x2, y2, color):
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x1 / xaxis, y1 / yaxis)
    glVertex2f(x2 / xaxis, y1 / yaxis)
    glVertex2f(x2 / xaxis, y2 / yaxis)
    glVertex2f(x1 / xaxis, y2 / yaxis)
    glEnd()

def fill_triangle(p1, p2, p3, color):
    glColor3f(*color)
    glBegin(GL_TRIANGLES)
    for px, py in (p1, p2, p3):
        glVertex2f(px / xaxis, py / yaxis)
    glEnd()

def rect_outline(x1, y1, x2, y2, color, size=2):
    glColor3f(*color)
    glPointSize(size)
    draw_line(x1, y1, x2, y1)
    draw_line(x2, y1, x2, y2)
    draw_line(x2, y2, x1, y2)
    draw_line(x1, y2, x1, y1)

# -- text (GLUT bitmap fonts; the original game drew letters by hand, but
#    an educational panel needs real paragraphs) ---------------------------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_12, color=(0.12, 0.12, 0.12)):
    glColor3f(*color)
    glRasterPos2f(x / xaxis, y / yaxis)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

def text_width(text, font=GLUT_BITMAP_HELVETICA_12):
    # Average character width in pixels for the two fonts we use.
    return len(text) * (9 if font == GLUT_BITMAP_HELVETICA_18 else 7)

def draw_text_centered(cx, y, text, font=GLUT_BITMAP_HELVETICA_12,
                       color=(0.12, 0.12, 0.12)):
    draw_text(cx - text_width(text, font) // 2, y, text, font, color)

def wrap(text, width):
    """Split a paragraph into lines of at most `width` characters."""
    lines, line = [], ""
    for word in text.split(" "):
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        lines.append(line)
    return lines

# -- the bone (used as the goal and on the doghouse sign) ------------------
def draw_bone(x, y, s=1.0):
    """A bone: a shaft with two knobs on each end."""
    glColor3f(0.96, 0.90, 0.74)
    glPointSize(max(2, int(5 * s)))
    draw_line(x - 14 * s, y, x + 14 * s, y)
    draw_line(x - 14 * s, y + 3 * s, x + 14 * s, y + 3 * s)
    draw_line(x - 14 * s, y - 3 * s, x + 14 * s, y - 3 * s)
    for kx, ky in ((-16, 5), (-16, -5), (16, 5), (16, -5)):
        filled_circle(5 * s, (x + kx * s, y + ky * s))
    glColor3f(0.45, 0.32, 0.15)
    glPointSize(1)
    circle(5 * s, (x - 16 * s, y + 5 * s))
    circle(5 * s, (x - 16 * s, y - 5 * s))
    circle(5 * s, (x + 16 * s, y + 5 * s))
    circle(5 * s, (x + 16 * s, y - 5 * s))

# -- Buddy, the original dog, unchanged ------------------------------------
# The old mood flags are kept but never change: nothing in this game makes
# Buddy hungry, tired or unhappy any more, so he always shows his happy
# face -- smile, tongue out, tail wagging.
dog_x = 0.0
dog_y = 193.0
nose = (0, 0)
eating = False
unhappy = False
sleep = False
firework = False
wag_phase = 0.0

def draw_dog():
    global dog_x, dog_y, eating, nose, unhappy, sleep, firework, wag_phase
    COAT = (0.72, 0.45, 0.20)       # warm golden-brown coat
    COAT_DARK = (0.45, 0.28, 0.10)  # darker ears, patch and paws
    CREAM = (0.93, 0.80, 0.60)      # muzzle and belly

    # Body: a solid sitting blob with a cream belly and a dark spot
    glColor3f(*COAT)
    glPointSize(2)
    filled_circle(30, (dog_x - 5, dog_y - 225))
    filled_circle(24, (dog_x - 28, dog_y - 225))
    glColor3f(*CREAM)
    filled_circle(17, (dog_x + 2, dog_y - 233))
    glColor3f(*COAT_DARK)
    filled_circle(11, (dog_x - 18, dog_y - 214))
    # Haunch and front paws
    glColor3f(*COAT)
    filled_circle(12, (dog_x - 32, dog_y - 240))
    glColor3f(*COAT_DARK)
    filled_circle(6, (dog_x + 5, dog_y - 252))
    filled_circle(6, (dog_x + 22, dog_y - 252))

    # Tail: it wags, swinging with wag_phase
    tail_base_x, tail_base_y = dog_x - 50, dog_y - 218
    tip_x = tail_base_x - 28 + math.sin(wag_phase) * 12
    tip_y = tail_base_y + 22 + math.cos(wag_phase) * 4
    glColor3f(*COAT_DARK)
    glPointSize(6)
    draw_line(tail_base_x, tail_base_y, tip_x, tip_y)
    filled_circle(5, (tip_x, tip_y))

    # Head
    glColor3f(*COAT)
    filled_circle(40, (dog_x, dog_y - 175))
    glColor3f(0, 0, 0)
    glPointSize(1.5)
    circle(40, (dog_x, dog_y - 175))
    # Dark patch over one eye, floppy ears
    glColor3f(*COAT_DARK)
    filled_circle(13, (dog_x + 14, dog_y - 166))
    filled_circle(15, (dog_x - 38, dog_y - 182))
    filled_circle(15, (dog_x + 38, dog_y - 182))
    glColor3f(0, 0, 0)
    glPointSize(1)
    circle(15, (dog_x - 38, dog_y - 182))
    circle(15, (dog_x + 38, dog_y - 182))

    # Eyes
    if firework:
        glColor3f(1, 1, 1)
        glPointSize(2)
        filled_circle(6, (dog_x - 14, dog_y - 172))
        filled_circle(6, (dog_x + 14, dog_y - 172))
        glColor3f(0, 0, 0)
        filled_circle(3, (dog_x - 14, dog_y - 172))
        filled_circle(3, (dog_x + 14, dog_y - 172))
    elif sleep:
        glColor3f(0, 0, 0)
        glPointSize(2)
        draw_line(dog_x - 20, dog_y - 172, dog_x - 8, dog_y - 172)
        draw_line(dog_x + 8, dog_y - 172, dog_x + 20, dog_y - 172)
    else:
        glColor3f(1, 1, 1)
        filled_circle(5, (dog_x - 14, dog_y - 172))
        filled_circle(5, (dog_x + 14, dog_y - 172))
        glColor3f(0, 0, 0)
        filled_circle(3, (dog_x - 14, dog_y - 172))
        filled_circle(3, (dog_x + 14, dog_y - 172))
        glColor3f(1, 1, 1)
        filled_circle(1, (dog_x - 12, dog_y - 170))
        filled_circle(1, (dog_x + 16, dog_y - 170))

    # Muzzle and nose
    glColor3f(*CREAM)
    filled_circle(18, (dog_x, dog_y - 192))
    glColor3f(0, 0, 0)
    filled_circle(6, (dog_x, dog_y - 186))
    nose = (dog_x, dog_y - 186)

    # Mouth: happy smile with a tongue, open while eating, frown when sad
    if firework:
        glColor3f(0, 0, 0)
        glPointSize(2)
        filled_circle(7, (dog_x, dog_y - 204))
        glColor3f(1, 0.55, 0.6)
        filled_circle(5, (dog_x, dog_y - 208))
    elif eating and not unhappy:
        glColor3f(0, 0, 0)
        glPointSize(1)
        filled_circle(7, (dog_x, dog_y - 204))
        glColor3f(1, 0.55, 0.6)
        filled_circle(5, (dog_x, dog_y - 209))
    elif unhappy:
        glColor3f(0, 0, 0)
        glPointSize(1)
        draw_line(dog_x - 8, dog_y - 206, dog_x, dog_y - 201)
        draw_line(dog_x + 8, dog_y - 206, dog_x, dog_y - 201)
    elif sleep:
        glColor3f(0, 0, 0)
        glPointSize(1)
        draw_line(dog_x - 6, dog_y - 202, dog_x + 6, dog_y - 202)
    else:
        glColor3f(0, 0, 0)
        glPointSize(1)
        draw_line(dog_x - 10, dog_y - 200, dog_x - 4, dog_y - 205)
        draw_line(dog_x - 4, dog_y - 205, dog_x, dog_y - 201)
        draw_line(dog_x + 4, dog_y - 205, dog_x, dog_y - 201)
        draw_line(dog_x + 4, dog_y - 205, dog_x + 10, dog_y - 200)
        glColor3f(1, 0.55, 0.6)
        filled_circle(4, (dog_x, dog_y - 209))

# ---------------------------------------------------------------------------
# Layout (pixels, origin at the window centre, x right, y up)
# ---------------------------------------------------------------------------
CELL = 68
GRID_N = 7
GARDEN_X0, GARDEN_Y1 = -620, 324          # garden top-left corner
PANEL_X0, PANEL_X1 = -80, 620             # educational panel
PANEL_Y0, PANEL_Y1 = -152, 324
TITLE_Y = 368

INK = (0.12, 0.12, 0.12)
MUTED = (0.35, 0.35, 0.35)
HEAD = (0.10, 0.25, 0.45)                 # section headers
GOLD = (0.85, 0.65, 0.10)
GREEN = (0.16, 0.55, 0.16)
RED = (0.75, 0.15, 0.15)
BLUE = (0.15, 0.35, 0.75)
PANEL_BG = (0.97, 0.96, 0.93)
BAR_BG = (0.93, 0.94, 0.96)


def cell_rect(r, c):
    """Pixel rectangle of grid cell (r, c), row 0 at the top."""
    x0 = GARDEN_X0 + c * CELL
    y1 = GARDEN_Y1 - r * CELL
    return x0, y1 - CELL, x0 + CELL, y1


def cell_center(r, c):
    x0, y0, x1, y1 = cell_rect(r, c)
    return (x0 + x1) / 2, (y0 + y1) / 2


# ---------------------------------------------------------------------------
# Application state (one object holds the whole demo)
# ---------------------------------------------------------------------------
class App:
    def __init__(self):
        self.env = GardenEnv()
        self.agent = QLearningAgent()
        self.mode = "train"          # train | challenge | place_bone | edit
        self.training = False        # training loop running
        self.paused = False
        self.speed = "Medium"        # Slow | Medium | Fast
        self.speed_steps = {"Slow": 1, "Medium": 4, "Fast": 15}
        self.challenge = False       # a challenge run is in progress
        self.challenge_policy = "trained"   # trained | explore
        self.challenge_steps = 0
        self.challenge_seen = {}
        self.episodes = 0
        self.successes = 0
        self.failures = 0
        self.success_step_sum = 0
        self.success_step_count = 0
        self.visited = set()         # cells Buddy visited this episode
        self.last_event = ("Press Start Training and watch Buddy learn. "
                           "Every move, reward and Q-value update will be "
                           "explained here, in plain words.")
        self.last_update = None      # dict from agent.update()
        self.last_update_time = 0.0
        self.last_action = None      # (state, action, explored?)
        self.cycle_phase = 0         # 0 observe, 1 choose, 2 act,
                                     # 3 reward, 4 update, 5 decide
        self.inspect = None          # pinned (row, col) or None = follow Buddy
        self.garden_changed = False
        self.saved = False
        self.notice = ""
        self.pending_fast = 0        # fast-train episodes still to run
        self.challenge_result = ""


app = App()


def success_rate():
    if app.episodes == 0:
        return 0.0
    return 100.0 * app.successes / app.episodes


def avg_steps():
    if app.success_step_count == 0:
        return None
    return app.success_step_sum / app.success_step_count


# ---------------------------------------------------------------------------
# Garden drawing
# ---------------------------------------------------------------------------
def draw_tree(cx, cy):
    glColor3f(0.45, 0.28, 0.12)
    glPointSize(4)
    draw_line(cx, cy - 16, cx, cy + 2)
    glColor3f(0.15, 0.45, 0.15)
    filled_circle(13, (cx - 7, cy + 8))
    filled_circle(13, (cx + 7, cy + 8))
    filled_circle(12, (cx, cy + 16))

def draw_rock(cx, cy):
    glColor3f(0.55, 0.55, 0.58)
    filled_circle(15, (cx, cy - 2))
    glColor3f(0.35, 0.35, 0.38)
    filled_circle(9, (cx - 4, cy + 4))

def draw_doghouse_mini(cx, cy):
    """The doghouse, redrawn small for the start square: same design as
    the original -- brown walls, red roof, arched door -- now a
    decoration, not a place Buddy must sleep."""
    fill_rect(cx - 22, cy - 20, cx + 22, cy + 2, (0.55, 0.35, 0.15))
    fill_triangle((cx - 27, cy + 2), (cx + 27, cy + 2), (cx, cy + 22),
                  (0.70, 0.20, 0.10))
    fill_rect(cx - 8, cy - 20, cx + 8, cy - 4, (0.15, 0.08, 0.04))
    glColor3f(0.15, 0.08, 0.04)
    filled_circle(8, (cx, cy - 4))

def draw_policy_arrow(cx, cy, action, qmax):
    """A small arrow showing the greedy move from this square, coloured
    by how good the Q-table thinks it is."""
    if qmax > 0.5:
        col = (0.16, 0.55, 0.16)
    elif qmax < -0.5:
        col = (0.75, 0.15, 0.15)
    else:
        col = (0.45, 0.45, 0.45)
    dx, dy = {0: (0, 13), 1: (0, -13), 2: (-13, 0), 3: (13, 0)}[action]
    glColor3f(*col)
    glPointSize(3)
    draw_line(cx - dx, cy - dy, cx + dx, cy + dy)
    # arrow head
    hx, hy = cx + dx, cy + dy
    if action == 0:
        fill_triangle((hx - 5, hy - 6), (hx + 5, hy - 6), (hx, hy + 2), col)
    elif action == 1:
        fill_triangle((hx - 5, hy + 6), (hx + 5, hy + 6), (hx, hy - 2), col)
    elif action == 2:
        fill_triangle((hx + 6, hy - 5), (hx + 6, hy + 5), (hx - 2, hy), col)
    else:
        fill_triangle((hx - 6, hy - 5), (hx - 6, hy + 5), (hx + 2, hy), col)

def draw_garden():
    global dog_x, dog_y
    draw_text(GARDEN_X0, GARDEN_Y1 + 12, "THE GARDEN  --  Buddy's world",
              GLUT_BITMAP_HELVETICA_18, HEAD)
    for r in range(GRID_N):
        for c in range(GRID_N):
            x0, y0, x1, y1 = cell_rect(r, c)
            cell = (r, c)
            # grass: two alternating greens
            grass = (0.55, 0.82, 0.38) if (r + c) % 2 == 0 else (0.48, 0.77, 0.33)
            fill_rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, grass)
            if cell in app.visited and cell != app.env.state:
                fill_rect(x0 + 4, y0 + 4, x1 - 4, y1 - 4, (0.85, 0.90, 0.55))
            cx, cy = cell_center(r, c)
            if cell in app.env.obstacles:
                fill_rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, (0.42, 0.35, 0.28))
                if (r * 7 + c) % 2 == 0:
                    draw_tree(cx, cy)
                else:
                    draw_rock(cx, cy)
            elif cell == app.env.goal:
                fill_rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, (0.98, 0.85, 0.30))
                draw_bone(cx, cy, 1.0)
                draw_text(cx - 14, y0 + 6, "BONE", GLUT_BITMAP_HELVETICA_12,
                          (0.45, 0.30, 0.05))
            elif cell == app.env.start:
                draw_doghouse_mini(cx, cy - 4)
                draw_text(cx - 16, y0 + 6, "START", GLUT_BITMAP_HELVETICA_12,
                          (0.30, 0.18, 0.05))
            else:
                # policy arrow: what the Q-table currently recommends here
                if cell in app.agent.q:
                    vals = app.agent.values(cell)
                    draw_policy_arrow(cx, cy, max(range(4),
                                                  key=lambda a: vals[a]),
                                      max(vals))
            # grid line
            rect_outline(x0, y0, x1, y1, (0.25, 0.45, 0.20), 1)

    # Buddy, drawn at his current square, scaled to fit the cell. The
    # dog himself is unchanged -- same shapes, colours and wagging tail,
    # only drawn smaller so he fits inside one square.
    br, bc = app.env.state
    cx, cy = cell_center(br, bc)
    glPushMatrix()
    glTranslatef(cx / xaxis, cy / yaxis, 0.0)
    glScalef(0.5, 0.5, 1.0)
    dog_x, dog_y = 12.0, 193.0
    draw_dog()
    glPopMatrix()
    # gold ring around Buddy's square
    x0, y0, x1, y1 = cell_rect(br, bc)
    rect_outline(x0 + 2, y0 + 2, x1 - 2, y1 - 2, GOLD, 3)

    # challenge result line under the garden
    if app.challenge_result:
        draw_text(GARDEN_X0, GARDEN_Y1 - GRID_N * CELL - 12,
                  app.challenge_result, GLUT_BITMAP_HELVETICA_12, HEAD)


# ---------------------------------------------------------------------------
# Educational panel
# ---------------------------------------------------------------------------
CYCLE_STEPS = ["1 Observe", "2 Choose", "3 Act", "4 Reward", "5 Update",
               "6 Decide"]

def section_header(y, text):
    draw_text(PANEL_X0, y, text, GLUT_BITMAP_HELVETICA_18, HEAD)
    glColor3f(0.75, 0.75, 0.75)
    glPointSize(1)
    draw_line(PANEL_X0, y - 8, PANEL_X1, y - 8)
    return y - 24

def draw_panel():
    fill_rect(PANEL_X0 - 10, PANEL_Y0, PANEL_X1 + 10, PANEL_Y1, PANEL_BG)
    rect_outline(PANEL_X0 - 10, PANEL_Y0, PANEL_X1 + 10, PANEL_Y1,
                 (0.70, 0.70, 0.70), 1)
    y = PANEL_Y1 - 8

    # A. What is Q-Learning?
    y = section_header(y, "WHAT IS Q-LEARNING?")
    for line in [
        "Buddy (the agent) learns by trying moves in the garden (the environment). Each square is a",
        "state; each move -- up, down, left, right -- is an action. Good moves earn rewards, bad",
        "moves earn penalties. The Q-table stores what he has learned: how good each move looks",
        "from each square. His policy is simple: usually pick the best-looking move.",
    ]:
        draw_text(PANEL_X0, y, line)
        y -= 14
    y -= 6

    # B. How Buddy learns -- the cycle, with the live step highlighted
    y = section_header(y, "HOW BUDDY LEARNS")
    box_w = (PANEL_X1 - PANEL_X0) // 6
    for i, label in enumerate(CYCLE_STEPS):
        bx0 = PANEL_X0 + i * box_w
        bx1 = bx0 + box_w - 6
        by1 = y + 4
        by0 = y - 22
        if i == app.cycle_phase:
            fill_rect(bx0, by0, bx1, by1, (0.98, 0.85, 0.30))
            rect_outline(bx0, by0, bx1, by1, GOLD, 2)
        else:
            fill_rect(bx0, by0, bx1, by1, (1.0, 1.0, 1.0))
            rect_outline(bx0, by0, bx1, by1, (0.70, 0.70, 0.70), 1)
        draw_text_centered((bx0 + bx1) // 2, by0 + 8, label)
    y -= 40
    y -= 8

    # C. The formula, with the last real update plugged in
    y = section_header(y, "THE FORMULA")
    draw_text(PANEL_X0, y,
              "Q(s,a) <- Q(s,a) + alpha x [ r + gamma x max Q(s',a') - Q(s,a) ]")
    y -= 14
    for line in [
        "Q(s,a): how good this move looked. alpha (0.10): learning rate -- how much one",
        "experience moves the value. r: reward just received. gamma (0.90): how much the",
        "future matters. max Q(s',a'): the best the next square promises.",
    ]:
        draw_text(PANEL_X0, y, line, color=MUTED)
        y -= 14
    y -= 2
    if app.last_update is not None:
        u = app.last_update
        draw_text(PANEL_X0, y, "Last real update, from Buddy's training:",
                  color=HEAD)
        y -= 17
        draw_text(PANEL_X0, y,
                  "%.2f + %.2f x [ %.0f + %.2f x %.2f - %.2f ] = %.2f"
                  % (u["old_q"], u["alpha"], u["reward"], u["gamma"],
                     u["max_next_q"], u["old_q"], u["new_q"]))
        y -= 14
    else:
        draw_text(PANEL_X0, y,
                  "No update yet -- press Start Training and a real one",
                  color=MUTED)
        y -= 14
        draw_text(PANEL_X0, y, "will appear here, with Buddy's own numbers.",
                  color=MUTED)
        y -= 14
    y -= 6

    # D. What just happened -- the event, explained, not just a number
    y = section_header(y, "WHAT JUST HAPPENED?")
    for line in wrap(app.last_event, 96)[:3]:
        draw_text(PANEL_X0, y, line)
        y -= 14
    y -= 6

    # E. The Q-table for one state
    inspect = app.inspect if app.inspect is not None else app.env.state
    y = section_header(y, "Q-TABLE  --  SQUARE (%d, %d)%s"
                       % (inspect[0], inspect[1],
                          "  (pinned -- click Follow Buddy to track him)"
                          if app.inspect is not None else ""))
    vals = app.agent.values(inspect)
    best = max(range(4), key=lambda a: vals[a])
    vmax = max(max(abs(v) for v in vals), 1.0)
    bar_x0 = PANEL_X0 + 190
    bar_max = 300
    for a, name in enumerate(ACTIONS):
        # the just-updated action flashes gold for a moment
        fresh = (app.last_update is not None
                 and app.last_update["state"] == inspect
                 and app.last_update["action"] == a
                 and time.time() - app.last_update_time < 1.5)
        tag = ""
        if a == best:
            tag = "  BEST"
            col = GREEN
        elif vals[a] < 0:
            col = RED
        else:
            col = BLUE
        mark = ">" if (app.last_action is not None
                       and app.last_action[0] == inspect
                       and app.last_action[1] == a) else " "
        draw_text(PANEL_X0, y, "%s %-5s %7.2f%s" % (mark, name, vals[a], tag),
                  color=col)
        # value bar, growing right from the zero line; colour shows the
        # sign (green best, red negative, blue the rest)
        bw = int(abs(vals[a]) / vmax * bar_max)
        fill_rect(bar_x0, y + 2, bar_x0 + max(bw, 2), y + 12, col)
        if fresh:
            rect_outline(bar_x0 - 4, y - 2, bar_x0 + bar_max + 4, y + 16,
                         GOLD, 2)
        y -= 18
    draw_text(PANEL_X0, y,
              "Higher = Buddy thinks it pays off better in the long run. An",
              color=MUTED)
    y -= 14
    draw_text(PANEL_X0, y,
              "estimate, not a promise. Tabular Q-learning fits small,",
              color=MUTED)
    y -= 14
    draw_text(PANEL_X0, y,
              "discrete worlds like this garden -- Buddy can still fail.",
              color=MUTED)


# ---------------------------------------------------------------------------
# Buttons and the bottom control bar
# ---------------------------------------------------------------------------
class Button:
    def __init__(self, x1, y1, x2, y2, label, action, enabled=True):
        self.rect = (x1, y1, x2, y2)
        self.label = label
        self.action = action
        self.enabled = enabled

    def contains(self, mx, my):
        x1, y1, x2, y2 = self.rect
        return x1 <= mx <= x2 and y1 <= my <= y2

    def draw(self):
        x1, y1, x2, y2 = self.rect
        fill = (0.85, 0.89, 0.95) if self.enabled else (0.92, 0.92, 0.92)
        fill_rect(x1, y1, x2, y2, fill)
        rect_outline(x1, y1, x2, y2,
                     (0.25, 0.35, 0.55) if self.enabled else (0.70, 0.70, 0.70),
                     2)
        col = INK if self.enabled else (0.60, 0.60, 0.60)
        draw_text_centered((x1 + x2) // 2, y1 + 10, self.label, color=col)


BUTTONS = []

def rebuild_buttons():
    BUTTONS.clear()
    bx, by = -620, -243
    BUTTONS.append(Button(bx, by, bx + 150, by + 30, "Start Training",
                          "start_train", enabled=not app.training))
    BUTTONS.append(Button(bx + 160, by, bx + 250, by + 30, "Pause",
                          "pause", enabled=app.training and not app.paused))
    BUTTONS.append(Button(bx + 260, by, bx + 350, by + 30, "Resume",
                          "resume", enabled=app.training and app.paused))
    BUTTONS.append(Button(bx + 360, by, bx + 450, by + 30, "Reset",
                          "reset"))
    BUTTONS.append(Button(bx + 460, by, bx + 600, by + 30,
                          "Speed: " + app.speed, "speed"))
    BUTTONS.append(Button(bx + 610, by, bx + 750, by + 30, "Fast train 500",
                          "fast_train"))
    bx, by = -620, -283
    BUTTONS.append(Button(bx, by, bx + 150, by + 30, "Start Challenge",
                          "start_challenge",
                          enabled=not app.challenge and app.episodes > 0))
    BUTTONS.append(Button(bx + 160, by, bx + 270, by + 30, "Place Bone",
                          "place_bone"))
    BUTTONS.append(Button(bx + 280, by, bx + 390, by + 30, "Edit Garden",
                          "edit_garden"))
    BUTTONS.append(Button(bx + 400, by, bx + 540, by + 30,
                          "Policy: " + app.challenge_policy, "policy"))
    BUTTONS.append(Button(bx + 550, by, bx + 760, by + 30,
                          "Retrain on new garden", "retrain",
                          enabled=app.garden_changed))
    BUTTONS.append(Button(bx + 770, by, bx + 890, by + 30, "Follow Buddy",
                          "follow", enabled=app.inspect is not None))

def draw_bottom_bar():
    fill_rect(-620, -352, 620, -168, BAR_BG)
    rect_outline(-620, -352, 620, -168, (0.70, 0.70, 0.70), 1)
    asteps = avg_steps()
    draw_text(-620, -186,
              "Episode %d   |   Successes %d   |   Failures %d   |   "
              "Success rate %.1f%%   |   Avg steps %s   |   Epsilon %.2f   |   "
              "Alpha %.2f   |   Gamma %.2f   |   Q-table: %s"
              % (app.episodes, app.successes, app.failures,
                 success_rate(),
                 ("%.1f" % asteps) if asteps is not None else "--",
                 app.agent.epsilon, app.agent.alpha, app.agent.gamma,
                 "saved" if app.saved else "not saved yet"))
    mode_line = "Mode: TRAINING -- Buddy is learning from his own moves."
    if app.mode == "challenge":
        mode_line = ("Mode: CHALLENGE -- watch Buddy use his learned "
                     "policy to find the bone.")
    elif app.mode == "place_bone":
        mode_line = ("Mode: PLACE BONE -- click a grass square to hide the "
                     "bone there.")
    elif app.mode == "edit":
        mode_line = ("Mode: EDIT GARDEN -- click a square to add or "
                     "remove a tree or rock.")
    if app.garden_changed:
        mode_line += ("  Garden changed! The old Q-table was learned on a "
                      "different layout -- retrain to start fresh.")
    if app.notice:
        mode_line += "  " + app.notice
    draw_text(-620, -210, mode_line, color=HEAD)
    rebuild_buttons()
    for b in BUTTONS:
        b.draw()
    draw_text(-620, -320,
              "Space: pause/resume   |   R: reset   |   F: fast train 500   |  "
              "C: challenge   |   S: save   |   Q: save and quit   |   Click a "
              "garden square to inspect its Q-values",
              color=MUTED)

# ---------------------------------------------------------------------------
# Training and challenge logic (the UI drives the RL step by step so the
# window never freezes: a timer tick runs a few steps, then returns)
# ---------------------------------------------------------------------------
def record_episode(success, steps):
    app.episodes += 1
    if success:
        app.successes += 1
        app.success_step_sum += steps
        app.success_step_count += 1
    else:
        app.failures += 1
    if app.episodes % 25 == 0:
        save_model()

def finish_episode():
    """Bookkeeping at the end of one live training episode."""
    steps = app.env.steps
    success = app.env.state == app.env.goal
    record_episode(success, steps)
    app.agent.decay_epsilon()
    app.env.reset()
    app.visited = {app.env.start}
    app.cycle_phase = 5        # Decide: the next choice uses the new table

def do_train_step():
    """One live training step: observe, choose, act, reward, update."""
    env, agent = app.env, app.agent
    app.cycle_phase = 0        # Observe
    state = env.state
    action, explored = agent.choose_action(state)
    app.cycle_phase = 1        # Choose
    next_state, reward, done, info = env.step(action)
    app.cycle_phase = 2        # Act
    app.cycle_phase = 3        # Reward
    detail = agent.update(state, action, reward, next_state, done)
    app.cycle_phase = 4        # Update
    app.last_action = (state, action, explored)
    app.last_event = info["event"]
    if explored:
        app.last_event += " (Buddy was exploring -- a random move.)"
    app.last_update = detail
    app.last_update_time = time.time()
    app.visited.add(next_state)
    if app.inspect is None:
        pass                   # panel follows Buddy automatically
    if done:
        finish_episode()

def do_challenge_step():
    """One challenge step: Buddy follows his learned policy. No
    learning happens here -- this is evaluation, not training."""
    env, agent = app.env, app.agent
    if app.challenge_policy == "trained":
        action = agent.best_action(env.state)
        explored = False
    else:
        action, explored = agent.choose_action(env.state, epsilon=0.30)
    app.last_action = (env.state, action, explored)
    app.cycle_phase = 1
    next_state, reward, done, info = env.step(action)
    app.cycle_phase = 3
    app.last_event = info["event"]
    if explored:
        app.last_event += " (Exploration mode: a random move.)"
    app.visited.add(next_state)
    app.challenge_steps += 1
    app.challenge_seen[next_state] = app.challenge_seen.get(next_state, 0) + 1
    if next_state == env.goal:
        app.challenge_result = ("Buddy found the bone in %d steps using "
                                "the %s policy!"
                                % (app.challenge_steps,
                                   app.challenge_policy))
        app.challenge = False
        app.mode = "train"
    elif app.challenge_seen[next_state] >= 3:
        app.challenge_result = ("Buddy got stuck: he kept coming back to "
                                "(%d, %d). The policy has no good move "
                                "from there yet -- more training would help."
                                % (next_state[0], next_state[1]))
        app.challenge = False
        app.mode = "train"
    elif app.challenge_steps >= MAX_STEPS:
        app.challenge_result = ("Buddy ran out of %d steps without finding "
                                "the bone. The policy is not good enough "
                                "yet -- train some more." % MAX_STEPS)
        app.challenge = False
        app.mode = "train"

def start_challenge():
    path = greedy_path(app.env, app.agent)
    app.env.reset()
    app.visited = {app.env.start}
    app.challenge_steps = 0
    app.challenge_seen = {app.env.start: 1}
    app.challenge_result = ""
    app.challenge = True
    app.training = False
    app.mode = "challenge"
    if path is not None:
        app.notice = ("Greedy check: this policy reaches the bone in %d "
                      "steps from the start." % (len(path) - 1))
    else:
        app.notice = ("Greedy check: this policy does not reach the bone "
                      "yet -- watch what happens.")
    if app.episodes == 0:
        app.notice = ("Buddy has not trained yet, so his Q-table is empty "
                      "and he is mostly guessing. Train first for a real "
                      "demo.")

def reset_all():
    app.agent.reset()
    app.env = GardenEnv()
    app.episodes = 0
    app.successes = 0
    app.failures = 0
    app.success_step_sum = 0
    app.success_step_count = 0
    app.visited = {app.env.start}
    app.last_update = None
    app.last_action = None
    app.inspect = None
    app.garden_changed = False
    app.training = False
    app.paused = False
    app.challenge = False
    app.mode = "train"
    app.pending_fast = 0
    app.challenge_result = ""
    app.saved = False
    app.last_event = ("Fresh start -- empty Q-table, epsilon back to 1.00. "
                      "Press Start Training and watch Buddy learn.")
    app.notice = ""
    if os.path.exists(SAVE_PATH):
        os.remove(SAVE_PATH)

def retrain_on_new_garden():
    """The garden changed, so the old Q-table belongs to a different
    world. Start learning from scratch on the new layout."""
    app.agent.reset()
    app.episodes = 0
    app.successes = 0
    app.failures = 0
    app.success_step_sum = 0
    app.success_step_count = 0
    app.visited = {app.env.start}
    app.last_update = None
    app.last_action = None
    app.inspect = None
    app.garden_changed = False
    app.training = True
    app.paused = False
    app.challenge = False
    app.mode = "train"
    app.pending_fast = 0
    app.challenge_result = ""
    app.env.reset()
    app.notice = "Retraining from scratch on the new garden layout."

def save_model():
    import pickle
    data = {
        "q": {tuple(s): list(v) for s, v in app.agent.q.items()},
        "epsilon": app.agent.epsilon,
        "alpha": app.agent.alpha,
        "gamma": app.agent.gamma,
        "episodes": app.episodes,
        "successes": app.successes,
        "failures": app.failures,
        "success_step_sum": app.success_step_sum,
        "success_step_count": app.success_step_count,
        "garden": app.env.to_dict(),
    }
    with open(SAVE_PATH, "wb") as f:
        pickle.dump(data, f)
    app.saved = True

def load_model():
    import pickle
    if not os.path.exists(SAVE_PATH):
        return False
    try:
        with open(SAVE_PATH, "rb") as f:
            data = pickle.load(f)
    except Exception as exc:
        print("Could not load the saved Q-table:", exc)
        return False
    app.agent.q = {tuple(s): list(v) for s, v in data["q"].items()}
    app.agent.epsilon = data.get("epsilon", 1.0)
    app.episodes = data.get("episodes", 0)
    app.successes = data.get("successes", 0)
    app.failures = data.get("failures", 0)
    app.success_step_sum = data.get("success_step_sum", 0)
    app.success_step_count = data.get("success_step_count", 0)
    app.env = GardenEnv.from_dict(data["garden"])
    app.env.reset()
    app.visited = {app.env.start}
    app.saved = True
    app.last_event = ("Loaded a saved Q-table: %d episodes of training, "
                      "%d bones found. Press Start Training to keep going, "
                      "or Start Challenge to test it."
                      % (app.episodes, app.successes))
    return True

# ---------------------------------------------------------------------------
# Timers
# ---------------------------------------------------------------------------
def step_timer(val):
    # Fast-train runs headless episodes in small chunks so the window
    # never freezes: 10 episodes per tick.
    while app.pending_fast > 0:
        chunk = min(app.pending_fast, 10)
        for _ in range(chunk):
            result = run_episode(app.env, app.agent)
            record_episode(result["success"], result["steps"])
        app.pending_fast -= chunk
        app.env.reset()
        app.visited = {app.env.start}
        break
    if app.training and not app.paused:
        for _ in range(app.speed_steps[app.speed]):
            do_train_step()
    elif app.challenge:
        do_challenge_step()
    glutPostRedisplay()
    glutTimerFunc(100, step_timer, 0)

def wag_animate(val):
    """Keep Buddy's tail wagging."""
    global wag_phase
    wag_phase += 0.35
    glutTimerFunc(50, wag_animate, 0)
    glutPostRedisplay()

# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------
def do_action(name):
    if name == "start_train":
        app.training = True
        app.paused = False
        app.challenge = False
        app.mode = "train"
        app.notice = ""
    elif name == "pause":
        app.paused = True
    elif name == "resume":
        app.paused = False
    elif name == "reset":
        reset_all()
    elif name == "speed":
        order = ["Slow", "Medium", "Fast"]
        app.speed = order[(order.index(app.speed) + 1) % len(order)]
    elif name == "fast_train":
        app.pending_fast += 500
        app.training = True
        app.paused = False
        app.challenge = False
        app.mode = "train"
        app.notice = "Fast-training 500 episodes in the background..."
    elif name == "start_challenge":
        start_challenge()
    elif name == "place_bone":
        app.mode = "place_bone"
        app.training = False
        app.challenge = False
    elif name == "edit_garden":
        app.mode = "edit"
        app.training = False
        app.challenge = False
    elif name == "policy":
        app.challenge_policy = ("explore" if app.challenge_policy == "trained"
                                else "trained")
    elif name == "retrain":
        retrain_on_new_garden()
    elif name == "follow":
        app.inspect = None
    glutPostRedisplay()

def mouseFunc(button, state, x, y):
    if button != GLUT_LEFT_BUTTON or state != GLUT_DOWN:
        return
    mx = x - WIDTH // 2
    my = HEIGHT // 2 - y
    rebuild_buttons()
    for b in BUTTONS:
        if b.enabled and b.contains(mx, my):
            do_action(b.action)
            return
    # Garden clicks
    c = (mx - GARDEN_X0) // CELL
    r = (GARDEN_Y1 - my) // CELL
    if not (0 <= r < GRID_N and 0 <= c < GRID_N):
        return
    cell = (r, c)
    if app.mode == "place_bone":
        if app.env.set_goal(cell):
            app.garden_changed = True
            app.env.reset()
            app.visited = {app.env.start}
            app.mode = "train"
            app.notice = ("Bone moved to (%d, %d). The old Q-table was "
                          "learned for the old spot." % (r, c))
        else:
            app.notice = "The bone needs a grass square, not the start."
    elif app.mode == "edit":
        if app.env.toggle_obstacle(cell):
            if not app.env.goal_reachable():
                app.env.toggle_obstacle(cell)   # undo: no path left
                app.notice = ("That would block every path to the bone -- "
                              "undone.")
            else:
                app.garden_changed = True
                app.env.reset()
                app.visited = {app.env.start}
                app.notice = "Garden changed. Retrain to teach the new layout."
        else:
            app.notice = "That square is protected (start, bone or Buddy)."
    else:
        # Inspect a square's Q-values; clicking Buddy follows him again.
        app.inspect = None if cell == app.env.state else cell
    glutPostRedisplay()

def keyboardListener(key, x, y):
    if key == b" ":
        if app.training:
            app.paused = not app.paused
    elif key == b"r":
        reset_all()
    elif key == b"f":
        do_action("fast_train")
    elif key == b"c":
        start_challenge()
    elif key == b"s":
        save_model()
        app.notice = "Q-table saved to rl/q_table.pkl."
    elif key == b"q":
        save_model()
        print("Q-table saved. Goodbye!")
        try:
            glutLeaveMainLoop()
        except Exception:
            sys.exit(0)
    glutPostRedisplay()

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    draw_text_centered(0, TITLE_Y, "Buddy's Q-Learning Treasure Hunt",
                       GLUT_BITMAP_HELVETICA_18, HEAD)
    draw_text_centered(0, TITLE_Y - 20,
                       "Watch a real Q-learning agent learn to find the bone "
                       "-- no scripted moves.",
                       GLUT_BITMAP_HELVETICA_12, MUTED)
    draw_garden()
    draw_panel()
    draw_bottom_bar()
    glutSwapBuffers()

# ---------------------------------------------------------------------------
# Main program setup
# ---------------------------------------------------------------------------
glutInit()
glutInitDisplayMode(GLUT_RGBA)
glutInitWindowSize(WIDTH, HEIGHT)
glutInitWindowPosition(0, 0)
wind = glutCreateWindow(b"Buddy's Q-Learning Treasure Hunt")
glOrtho(0, WIDTH, 0, HEIGHT, -1, 1)
glClearColor(1, 1, 1, 1)

glutDisplayFunc(showScreen)
glutMouseFunc(mouseFunc)
glutKeyboardFunc(keyboardListener)

glutTimerFunc(100, step_timer, 0)
glutTimerFunc(50, wag_animate, 0)

if load_model():
    print("Loaded a saved Q-table: %d episodes, %d bones found."
          % (app.episodes, app.successes))

glutMainLoop()
