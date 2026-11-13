# Dog Care - a 2D OpenGL virtual pet dog game.
#
# Take care of Buddy the dog: feed him kibble and bones from his bowl,
# let him sleep in his dog house, and play fetch with him - throw the
# bone and push the ball into the goal. Hunger, health and the day/night
# cycle keep running, so look after him.
#
# Controls:
#   LEFT / RIGHT arrows .... walk Buddy
#   UP arrow ............... jump (catch the bone mid-air!)
#   E ...................... eat from the food bowl (stand next to it)
#   B ...................... sleep in the dog house (stand next to it)
#   W / Q .................. push the ball right / left (fetch ball game)
#   Mouse .................. PLAY / STOP, ball game, bone game buttons
#   Right-click ............ fireworks in the playroom
#
# Run:  pip install PyOpenGL
#       python main.py

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math

width, height = 600, 600

# Global variables for game state and pet attributes
xaxis = width / 2
yaxis = height / 2

dog_x = 0.0
dog_y = -50
bone_x = 0.0
bone_y = -260
bone_vx = 0.0
bone_vy = 0.0
bone_flying = False
bone_wait = 0
bone_xbutton = width - 350
bone_ybutton = 170
food = []
food_pan_empty = False
eating = False
nose = (0, 0)
hungry = 10
health = 5
energy = 5
unhappy = False
sleep = False
day = 1
d2n = True  # day to night
n2d = False  # night to day
play = False
ballx = -280
ballbutton = -280  # upperrightball
ballbuttonON = False
boneON = False
fetchpoints = 0
ballgamepoint = 0
goal = True
rightgoalpost = True  # the goalpost is on right or left
fireworkCircleRadius = 0.5
fireworksCircleSpeed = 6
fireworksCircleColor = [1, 0, 0]
firework = False
fireworkLst = []
wag_phase = 0.0  # tail-wagging animation
food.append((xaxis - 67, -(yaxis - 35)))
food.append((xaxis - 57, -(yaxis - 35)))
food.append((xaxis - 47, -(yaxis - 35)))
food.append((xaxis - 37, -(yaxis - 35)))
food.append((xaxis - 27, -(yaxis - 35)))
food.append((xaxis - 17, -(yaxis - 35)))

# Fixed stars for the night sky in the window (so they don't flicker).
stars = [(random.uniform(-180, 60), random.uniform(-20, 160))
         for _ in range(24)]

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
    global xaxis, yaxis
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
    """Midpoint circle. All of its points are emitted in one
    glBegin/glEnd block: the old version opened a new block for every
    point, which was fine for outlines but far too slow once the dog's
    solid fills draw twenty circles at once. The pixels are identical."""
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
    global xaxis, yaxis
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
    """A solid disc, drawn as concentric midpoint circles in the same
    point-plotting style as the rest of the game. Solid fills are what
    make the dog, the bowl and the sun look like real objects instead
    of wireframes."""
    r = radius
    while r > 0:
        circle(r, center)
        r -= 2
    circle(1, center)

def draw_bone(x, y, s=1.0):
    """A bone: a shaft with two knobs on each end. Used in the food
    bowl, on the bone-game button, and as the thrown bone itself."""
    glColor3f(0.96, 0.90, 0.74)
    glPointSize(max(2, int(5 * s)))
    # shaft
    draw_line(x - 14 * s, y, x + 14 * s, y)
    draw_line(x - 14 * s, y + 3 * s, x + 14 * s, y + 3 * s)
    draw_line(x - 14 * s, y - 3 * s, x + 14 * s, y - 3 * s)
    # knobs
    for kx, ky in ((-16, 5), (-16, -5), (16, 5), (16, -5)):
        filled_circle(5 * s, (x + kx * s, y + ky * s))
    # outline
    glColor3f(0.45, 0.32, 0.15)
    glPointSize(1)
    circle(5 * s, (x - 16 * s, y + 5 * s))
    circle(5 * s, (x - 16 * s, y - 5 * s))
    circle(5 * s, (x + 16 * s, y + 5 * s))
    circle(5 * s, (x + 16 * s, y - 5 * s))

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

def draw_foodbowl():
    global food_pan_empty, food, play, xaxis, yaxis
    if play == False:
        # Steel-blue food bowl, kibble inside and two bones on top
        glPointSize(4)
        glColor3f(0.30, 0.50, 0.85)
        draw_line((xaxis - 80), -(yaxis - 30), (xaxis - 6), -(yaxis - 30))
        draw_line((xaxis - 66), -(yaxis - 11), (xaxis - 11), -(yaxis - 11))
        draw_line((xaxis - 80), -(yaxis - 30), (xaxis - 66), -(yaxis - 11))
        draw_line((xaxis - 20), -(yaxis - 11), (xaxis - 6), -(yaxis - 30))
        glPointSize(3)
        glColor3f(0.35, 0.20, 0.08)
        for item in food:
            circle(4, (item[0], item[1]))
        draw_bone(xaxis - 42, -(yaxis - 22), 0.45)
        draw_bone(xaxis - 58, -(yaxis - 28), 0.35)
        # Water bowl beside it
        glPointSize(4)
        glColor3f(0.30, 0.50, 0.85)
        draw_line((xaxis - 150), -(yaxis - 30), (xaxis - 105), -(yaxis - 30))
        draw_line((xaxis - 142), -(yaxis - 11), (xaxis - 113), -(yaxis - 11))
        draw_line((xaxis - 150), -(yaxis - 30), (xaxis - 142), -(yaxis - 11))
        draw_line((xaxis - 113), -(yaxis - 11), (xaxis - 105), -(yaxis - 30))
        glColor3f(0.20, 0.55, 1.0)
        filled_circle(12, (xaxis - 128, -(yaxis - 24)))
        glColor3f(1, 1, 1)
        filled_circle(3, (xaxis - 132, -(yaxis - 20)))

def draw_doghouse():
    global play
    if play == False:
        # Walls
        glColor3f(0.55, 0.35, 0.15)
        glPointSize(3)
        for y in range(-290, -240, 2):
            draw_line(-285, y, -205, y)
        # Roof, filled triangle
        glColor3f(0.70, 0.20, 0.10)
        glPointSize(3)
        for i in range(0, 46, 3):
            y = -240 + i
            half = 50 - i * (50 / 46)
            draw_line(-245 - half, y, -245 + half, y)
        # Arched doorway
        glColor3f(0.15, 0.08, 0.04)
        for y in range(-290, -272, 2):
            draw_line(-260, y, -230, y)
        filled_circle(15, (-245, -272))
        # A little bone sign above the door
        draw_bone(-245, -212, 0.45)

def draw_window():
    global day, play, n2d, d2n
    glColor3f(0, 0, 0)
    glPointSize(2)
    # Window border
    if play == False:
        draw_line(-width + 400, height - 400, width - 600, height - 400)
        draw_line(-width + 400, height - 600, width - 600, height - 600)
        draw_line(-width + 400, height - 400, -width + 400, height - 600)
        draw_line(width - 600, height - 400, width - 600, height - 600)
        # Sky color
        if day > 0.9:
            glColor3f(0, 0.7, 1)
        else:
            g = max(0.1, day - 0.4)
            b = max(0.1, day - 0.2)
            glColor3f(0, g, b)
        glPointSize(198)
        draw_line(-width + 500, height - 500, width - 699, height - 500)
        # Clouds by day, stars by night
        if day > 0.4:
            glColor3f(1, 1, 1)
            glPointSize(3)  # small points: the sky was drawn with huge ones
            filled_circle(14, (-150, 150))
            filled_circle(11, (-125, 138))
            filled_circle(12, (-60, 155))
            filled_circle(10, (-40, 142))
        else:
            glColor3f(1, 1, 1)
            glPointSize(2)
            for sx, sy in stars:
                circle(1, (sx, sy))
        # Sun
        if 0.4 < day <= 1:
            h = height
            inc = 0
            if day == 1:
                glColor3f(1, 1, 0)
            elif 0.9 >= day > 0.4:
                glColor3f(day - 0.2, day - 0.2, 0)
            if d2n == True and day < 1:
                h = height - (1 - day) * 200
            elif n2d == True and day < 1:
                h = height - (1 - day) * 200 + inc
                inc += 1
            glPointSize(5)
            circle(15, (-width + 450, h - 450))
            circle(10, (-width + 450, h - 450))
            circle(5, (-width + 450, h - 450))
            glPointSize(2)
            draw_line(-width + 425, h - 450, -width + 475, h - 450)
            draw_line(-width + 450, h - 425, -width + 450, h - 475)
            draw_line(-width + 435, h - 430, -width + 465, h - 470)
            draw_line(-width + 435, h - 470, -width + 465, h - 430)

    # PLAYROOM
    else:
        draw_line(-width + 400, height - 400, width - 400, height - 400)
        draw_line(-width + 400, height - 600, width - 400, height - 600)
        draw_line(-width + 400, height - 400, -width + 400, height - 600)
        draw_line(width - 400, height - 400, width - 400, height - 600)
        # Sky color
        if day > 0.9:
            glColor3f(0, 0.7, 1)
        else:
            g = max(0.1, day - 0.4)
            b = max(0.1, day - 0.2)
            glColor3f(0, g, b)
        glPointSize(198)
        draw_line(-width + 500, height - 500, width - 499, height - 500)
        # Clouds by day, stars by night
        if day > 0.4:
            glColor3f(1, 1, 1)
            glPointSize(3)  # small points: the sky was drawn with huge ones
            filled_circle(14, (-100, 150))
            filled_circle(11, (-75, 138))
            filled_circle(12, (40, 155))
            filled_circle(10, (65, 142))
        else:
            glColor3f(1, 1, 1)
            glPointSize(2)
            for sx, sy in stars:
                circle(1, (sx, sy))
        # Sun
        if 0.4 < day <= 1:
            h = height
            inc = 0
            if day == 1:
                glColor3f(1, 1, 0)
            elif 0.9 >= day > 0.4:
                glColor3f(day - 0.2, day - 0.2, 0)
            if d2n == True and day < 1:
                h = height - (1 - day) * 200
            elif n2d == True and day < 1:
                h = height - (1 - day) * 200 + inc
                inc += 1
            glPointSize(5)
            circle(15, (-width + 450, h - 450))
            circle(10, (-width + 450, h - 450))
            circle(5, (-width + 450, h - 450))
            glPointSize(2)
            draw_line(-width + 425, h - 450, -width + 475, h - 450)
            draw_line(-width + 450, h - 425, -width + 450, h - 475)
            draw_line(-width + 435, h - 430, -width + 465, h - 470)
            draw_line(-width + 435, h - 470, -width + 465, h - 430)

def windowcross():
    if play == False:
        glColor3f(0, 0, 0)
        glPointSize(1)
        draw_line(width - 700, height - 400, width - 700, height - 600)
        draw_line(-width + 400, height - 500, width - 600, height - 500)
    else:
        glColor3f(0, 0, 0)
        glPointSize(1)
        draw_line(width - 600, height - 402, width - 600, height - 598)
        draw_line(width - 700, height - 402, width - 700, height - 598)
        draw_line(width - 700, height - 402, width - 700, height - 598)
        draw_line(-width + 400, height - 502, width - 400, height - 502)
        draw_line(width - 500, height - 402, width - 500, height - 598)

def draw_thrown_bone():
    global boneON
    if play == True and boneON == True:
        draw_bone(bone_x, bone_y, 1.0)

def playbutton():
    global play, bone_xbutton, bone_ybutton
    glColor3f(0, 0.4, 1)
    glPointSize(2)
    # Button box
    draw_line(width - 320, height - 350, width - 370, height - 350)
    draw_line(width - 320, height - 370, width - 370, height - 370)
    draw_line(width - 315, height - 365, width - 315, height - 355)
    draw_line(width - 375, height - 365, width - 375, height - 355)
    draw_line(width - 370, height - 350, width - 375, height - 355)
    draw_line(width - 370, height - 370, width - 375, height - 365)
    draw_line(width - 320, height - 350, width - 315, height - 355)
    draw_line(width - 320, height - 370, width - 315, height - 365)

    # "PLAY" text
    glPointSize(2)
    if play == False:
        # P
        draw_line(width - 365, height - 365, width - 365, height - 355)
        draw_line(width - 361, height - 361, width - 361, height - 356)
        draw_line(width - 365, height - 355, width - 361, height - 356)
        draw_line(width - 361, height - 361, width - 365, height - 361)
        # L
        draw_line(width - 353, height - 365, width - 353, height - 355)
        draw_line(width - 353, height - 365, width - 348, height - 365)
        # A
        draw_line(width - 337, height - 365, width - 340, height - 355)
        draw_line(width - 343, height - 365, width - 340, height - 354)
        draw_line(width - 337, height - 362, width - 342, height - 362)
        # Y
        draw_line(width - 330, height - 362, width - 333, height - 355)
        draw_line(width - 330, height - 362, width - 327, height - 355)
        draw_line(width - 330, height - 362, width - 330, height - 366)
    else:
        # "STOP" text
        # S
        draw_line(width - 365, height - 355, width - 360, height - 355)
        draw_line(width - 365, height - 360, width - 360, height - 360)
        draw_line(width - 365, height - 365, width - 360, height - 365)
        draw_line(width - 365, height - 355, width - 365, height - 360)
        draw_line(width - 360, height - 360, width - 360, height - 365)
        # T
        draw_line(width - 357, height - 355, width - 350, height - 355)
        draw_line(width - 354, height - 355, width - 354, height - 365)
        # O
        circle(4.3, (width - 343, height - 360))
        # P
        draw_line(width - 335, height - 365, width - 335, height - 355)
        draw_line(width - 331, height - 361, width - 331, height - 356)
        draw_line(width - 335, height - 355, width - 331, height - 356)
        draw_line(width - 331, height - 361, width - 335, height - 361)

        # Ball button
        if ballbuttonON == False:
            glPointSize(4)
            glColor3f(1, 0, 0)
            circle(16, (-ballbutton - 30, 200))
            glColor3f(1, 0, 1)
            circle(11, (-ballbutton - 30, 200))
            glColor3f(1, 0, 0)
            circle(7, (-ballbutton - 30, 200))
            circle(4, (-ballbutton - 30, 200))
        if ballbuttonON == True:
            glPointSize(8)
            glColor3f(1, 0, 0)
            circle(16, (-ballbutton - 30, 200))
            circle(12, (-ballbutton - 30, 200))
            circle(8, (-ballbutton - 30, 200))
            circle(5, (-ballbutton - 30, 200))

        # Bone button (throw-the-bone game)
        if boneON == False:
            draw_bone(bone_xbutton, bone_ybutton - 10, 1.0)
        if boneON == True:
            glPointSize(8)
            glColor3f(1, 0, 0)
            circle(16, (-ballbutton - 30, 150))
            circle(12, (-ballbutton - 30, 150))
            circle(8, (-ballbutton - 30, 150))
            circle(5, (-ballbutton - 30, 150))

def playroomtoys():
    global rightgoalpost
    # Ball
    if ballbuttonON == True:
        glPointSize(4)
        glColor3f(1, 0, 0)
        circle(16, (ballx, -275))
        glColor3f(1, 0, 1)
        circle(11, (ballx, -275))
        glColor3f(1, 0, 0)
        circle(7, (ballx, -275))
        circle(4, (ballx, -275))
        # Goalpost
        if goal == True:
            rightgoalpost = True
            glColor3f(0, 0, 0)
            draw_line(290, -290, 290, -220)
            draw_line(250, -280, 250, -210)
            draw_line(290, -220, 250, -210)
        else:
            rightgoalpost = False
            glColor3f(0, 0, 0)
            draw_line(-290, -290, -290, -220)
            draw_line(-250, -280, -250, -210)
            draw_line(-290, -220, -250, -210)

def fcircle(radius, center):
    for _ in range(10):
        d = 1 - radius
        x = 0
        y = radius
        glPointSize(3)
        fcirclepoints(x, y, center)
        while (x < y):
            if (d < 0):
                d = d + 2 * x + 3
                x += 1
            else:
                d = d + 2 * x - 2 * y + 5
                x += 1
                y -= 1
            if random.random() < 0.1:
                fcirclepoints(x, y, center)
        radius -= 30

def fcirclepoints(x, y, center):
    global xaxis, yaxis, width, height
    glBegin(GL_POINTS)
    x0 = x / xaxis
    y0 = y / yaxis
    ax = center[0] / xaxis
    ay = center[1] / yaxis
    if play and (x0 + ax <= width - 400):
        glVertex2f(x0 + ax, y0 + ay)
        glVertex2f(y0 + ax, x0 + ay)
        glVertex2f(y0 + ax, -x0 + ay)
        glVertex2f(x0 + ax, -y0 + ay)
        glVertex2f(-x0 + ax, -y0 + ay)
        glVertex2f(-y0 + ax, -x0 + ay)
        glVertex2f(-y0 + ax, x0 + ay)
        glVertex2f(-x0 + ax, y0 + ay)
    glEnd()

def toclear():
    glColor3f(1, 1, 1)
    glPointSize(200)
    draw_line(width - 300, height + 700, width - 300, height - 1500)
    glPointSize(100)
    draw_line(width - 850, height + 700, width - 850, height - 1500)
    glPointSize(300)
    draw_line(width - 850, height - 750, width, height - 750)
    glPointSize(200)
    draw_line(width - 850, height - 300, width, height - 300)

def healthbar():
    global health
    a = -(xaxis - 50)
    b = yaxis - 30
    c = 20
    glPointSize(4)
    glColor3f(1, 0, 0)
    draw_line(-285, 275, -280, 263)
    draw_line(-275, 275, -280, 263)
    circle(1, (-280, 270))
    circle(1, (-285, 273))
    circle(1, (-275, 273))
    draw_line(-286, 275, -280, 263)
    draw_line(-274, 275, -280, 263)

    glPointSize(2)
    glColor3f(0, 0, 0)
    circle(12, (-280, 270))
    draw_line(-270, 280, -155, 280)
    draw_line(-270, 260, -155, 260)
    draw_line(-155, 280, -155, 260)
    glPointSize(6)
    glColor3f(0.4, 0.8, 0.4)
    health = max(0, health)
    for i in range(health):
        circle(5, (a, b))
        a += c

def showScreen():
    global health, unhappy
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    draw_window()
    toclear()  # to hide the fireworks outside the window
    draw_dog()
    draw_foodbowl()
    healthbar()
    draw_doghouse()
    playbutton()
    windowcross()
    draw_thrown_bone()

    if play == True and sleep == False:
        playroomtoys()

    if health <= 0 and unhappy == False:
        print("!!!Your pet is unhappy!!!")
        unhappy = True
    elif health > 0:
        unhappy = False

    glutSwapBuffers()

def mouseFunc(button, state, x, y):
    global fetchpoints, bone_x, bone_y, boneON, ballbuttonON, ballbutton
    global firework, fireworksCircleSpeed, fireworkCircleRadius, play
    global food_pan_empty, food, eating, dog_x, dog_y, nose, hungry
    global health, unhappy, sleep, day

    nose = (dog_x, dog_y - 186)
    a = x - (600 / 2)
    b = (600 / 2) - y

    # Handle toy button clicks
    if play == True and width - 370 <= a <= width - 320 and height - 410 <= b <= height - 390:
        if boneON == False and button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and ballbuttonON == False:
            ballbuttonON = True
        elif boneON == False and button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and ballbuttonON == True:
            ballbuttonON = False
            print("Ball Game Final Score: ", ballgamepoint)
            ballgamepoint = 0

    if play == True and width - 370 <= a <= width - 320 and height - 460 <= b <= height - 420:
        if boneON == False and button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and ballbuttonON == False:
            boneON = True
            throw_bone()
        elif boneON == True and button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and ballbuttonON == False:
            boneON = False
            print("Bone Game Final Score: ", fetchpoints)
            fetchpoints = 0

    # Handle Play/Stop button
    if width - 370 <= a <= width - 320 and height - 370 <= b <= height - 350:
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            if play == False:
                if unhappy == False:
                    if sleep == True:
                        print("To play, you need energy. Finish sleeping.")
                    else:
                        play = True
                else:
                    print("To play, you need to eat first.")
            else:
                play = False
                if boneON == True:
                    print("Bone game Final Score: ", fetchpoints)
                    boneON = False
                    fetchpoints = 0
                ballbuttonON = False

    # Handle fireworks
    if play == True and button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        if -width + 400 <= a <= width - 400 and height - 600 <= b <= height - 400:
            fireworkLst.append([a, b, 3])
            if dog_y < 20:
                dog_y += 70
                glutTimerFunc(300, come_down, 0)

    # Food bowl and dog house are keyboard-driven (E and B keys).

def throw_bone():
    """Throw a bone across the playroom in an arc. It starts at one side
    and lands somewhere on the other side for Buddy to fetch."""
    global bone_x, bone_y, bone_vx, bone_vy, bone_flying
    start_x = random.choice([-240, 240])
    land_x = random.uniform(-260, 260)
    if abs(land_x - start_x) < 120:
        land_x = -land_x
    bone_x, bone_y = start_x, -150
    flight = 45  # ticks of 20ms
    bone_vx = (land_x - start_x) / flight
    bone_vy = 7.0
    bone_flying = True

def bone_animate(val):
    global bone_x, bone_y, bone_vx, bone_vy, bone_flying, bone_wait
    global boneON, fetchpoints, dog_x
    if boneON == True:
        if bone_flying:
            bone_vy -= 0.35
            bone_y += bone_vy
            bone_x += bone_vx
            if bone_y <= -260:
                bone_y = -260
                bone_flying = False
        elif bone_wait > 0:
            bone_wait -= 1
            if bone_wait == 0:
                throw_bone()
        else:
            # The bone is lying on the ground: run to it and fetch it!
            if abs(dog_x - bone_x) <= 40:
                fetchpoints += 1
                print("Fetched! Point: ", fetchpoints)
                bone_wait = 30
    glutTimerFunc(20, bone_animate, 0)
    glutPostRedisplay()

def come_down(val):
    global dog_y, hungry
    if dog_y > -50:
        dog_y -= 70
    hungry += 0.5
    glutPostRedisplay()

def wag_animate(val):
    """Keep Buddy's tail wagging."""
    global wag_phase
    wag_phase += 0.35
    glutTimerFunc(50, wag_animate, 0)
    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global sleep, dog_x, dog_y, bone_x, bone_y, boneON, fetchpoints
    global bone_flying, bone_wait

    if key == GLUT_KEY_LEFT and dog_x >= -xaxis + 62 and sleep == False:
        dog_x -= 10.0
    if key == GLUT_KEY_RIGHT and dog_x <= xaxis - 62 and sleep == False:
        dog_x += 10.0
    if sleep == False and key == GLUT_KEY_UP:
        if dog_y < 20:
            dog_y += 70
        glutTimerFunc(300, come_down, 0)

    # Catch the bone mid-air: jump while standing under it.
    if boneON == True and bone_flying:
        if bone_x - 50 <= dog_x <= bone_x + 50:
            if dog_y - 127 >= bone_y - 20:
                fetchpoints += 1
                print("Caught it mid-air! Point: ", fetchpoints)
                bone_flying = False
                bone_y = -260
                bone_wait = 30

    glutPostRedisplay()

def keyboardListener(key, x, y):
    global ballx, dog_x, goal, ballgamepoint, health, ballbuttonON, rightgoalpost
    global play, sleep, unhappy, day, eating, hungry, food, food_pan_empty, dog_y

    # Fetch ball game: push the ball into the goal.
    if play == True and key == b'w' and abs(dog_x - ballx) <= 40:
        if health <= 1:
            ballbuttonON = False
            print("Game over")
        else:
            ballx += 40
            if ballx > 270:
                ballx = 280
                goal = False
                if rightgoalpost == True:
                    ballgamepoint += 1
                    print("Yay goal! Score:", ballgamepoint)
    if play == True and key == b'q' and abs(dog_x - ballx) <= 40:
        if health <= 1:
            ballbuttonON = False
            print("Game over")
        else:
            ballx -= 40
            if ballx < -270:
                ballx = -280
                goal = True
                if rightgoalpost == False:
                    ballgamepoint += 1
                    print("Yay goal! Score:", ballgamepoint)

    # Eat from the food bowl with 'e' when standing next to it.
    if key == b'e' and play == False and 170 <= dog_x <= 230:
        if not food_pan_empty:
            if len(food) > 1 and hungry != 0:
                eating = True
                food.pop()
                hungry = max(0, hungry - 1)
                health += 1
                health = min(health, 4)
                if hungry == 0:
                    health = 5
            elif len(food) > 1 and hungry == 0:
                print("I am not hungry anymore.")
            elif len(food) == 1:
                food.pop()
                hungry = max(0, hungry - 1)
                print("Oh no! Refill food")
                food_pan_empty = True
                eating = False
            elif len(food) == 0:
                food_pan_empty = True
                eating = False
        else:
            # Refill the bowl with kibble
            food_pan_empty = False
            food.append((xaxis - 67, -(yaxis - 35)))
            food.append((xaxis - 57, -(yaxis - 35)))
            food.append((xaxis - 47, -(yaxis - 35)))
            food.append((xaxis - 37, -(yaxis - 35)))
            food.append((xaxis - 27, -(yaxis - 35)))
            food.append((xaxis - 17, -(yaxis - 35)))
            food.append((xaxis - 63, -(yaxis - 45)))
            food.append((xaxis - 53, -(yaxis - 45)))
            food.append((xaxis - 43, -(yaxis - 45)))
            food.append((xaxis - 33, -(yaxis - 45)))
            food.append((xaxis - 23, -(yaxis - 45)))
    else:
        if key == b'e':
            eating = False

    # Sleep in the dog house with 'b' when standing next to it.
    if key == b'b' and play == False and (-xaxis + 60) <= dog_x < (-xaxis + 160):
        if day > 0.4 and sleep == False:
            print("It's still day! You should play!")
        elif unhappy == True:
            print("Eat first.")
        else:
            if sleep == False:
                sleep = True
                dog_y += 20
                dog_x = -230
            else:
                sleep = False
                dog_y -= 20
                if day <= 0.4:
                    print('Sleep some more.')

    glutPostRedisplay()

def hungry_announce(val):
    global hungry, health, sleep
    glutTimerFunc(6000, hungry_announce, 0)
    if sleep == False:
        if hungry == 11 and play == False:
            health -= 1
            print("I am hungry. Let's go eat")
        elif hungry == 11 and play == True:
            health -= 1
            if health <= 2:
                print("Enough playing. Let's go eat first")
        hungry += 0.5
        hungry = min(11, hungry)
    glutPostRedisplay()

def sleep_announce(val):
    global sleep, hungry, day
    glutTimerFunc(6000, sleep_announce, 0)
    glutPostRedisplay()

def day_announce(val):
    global day, d2n, n2d, sleep, health
    glutTimerFunc(5000, day_announce, 0)
    if day <= 0.1:
        n2d = True
        d2n = False
    if day >= 1:
        d2n = True
        n2d = False
    if n2d == True and day < 1:
        day += 0.1
    elif d2n == True and day >= 0.1:
        day -= 0.1
    if day <= 0.4 and sleep == False:
        print("Time to sleep.")
        health -= 1
    if day >= 0.7 and sleep == True:
        print('Time to wakey wakey.')
    glutPostRedisplay()

# Main program setup
glutInit()
glutInitDisplayMode(GLUT_RGBA)
glutInitWindowSize(width, height)
glutInitWindowPosition(0, 0)
wind = glutCreateWindow(b"DOG CARE - Buddy")
glOrtho(0, width, 0, height, -1, 1)
glClearColor(1, 1, 1, 1)

# Register callbacks
glutDisplayFunc(showScreen)
glutSpecialFunc(specialKeyListener)
glutMouseFunc(mouseFunc)
glutKeyboardFunc(keyboardListener)

# Register timers for game logic
glutTimerFunc(3000, hungry_announce, 0)
glutTimerFunc(3000, sleep_announce, 0)
glutTimerFunc(5000, day_announce, 0)
glutTimerFunc(20, bone_animate, 0)
glutTimerFunc(50, wag_animate, 0)

# Start the main loop
glutMainLoop()
