# Pet-Care
This is a 2D OpenGL-based virtual pet care game where you take care of a digital cat. You can feed it, let it sleep, and play mini-games with it like ball game and fishing game. The game also simulates day/night cycles, hunger, and health levels, so you must manage your pet’s needs.

1. Cat Display

The cat is drawn using points, lines, and circles (draw_cat() function).

Animations include:

Sleeping eyes

Eating mouth

Tail and paws

Whiskers

Firework reactions when in play mode.

The cat can jump when pressing the UP arrow key, and move left/right with LEFT/RIGHT arrow keys.

2. Pet Stats

Health (shown as a green bar) decreases if hungry or sleep-deprived.

Hunger increases over time and affects health.

Sleepiness is simulated through day/night cycles.

Unhappiness occurs if health reaches zero.

3. Feeding

Food is placed in a food pan.

Player feeds the cat by pressing e when near the pan (automatic eating without using the mouse).

Eating reduces hunger and increases health slightly.

Food pan can become empty and must be refilled manually.

4. Sleeping

The cat can sleep near the bed by pressing b.

Sleep can only happen at night (day <= 0.4), otherwise the game will warn the player.

Sleeping restores energy for playing.

5. Mini-games
a. Ball Game

Activate by clicking the ball button.

Press w to push the ball right, q to push it left.

Score points if the ball crosses goalposts.

Cat must be near the ball to play.

b. Fishing Game

Activate by clicking the fish button.

The cat can catch fish by moving under them while the fish moves.

Points are scored for catching fish before it goes off-screen.

6. User Interface

Buttons:

PLAY / STOP button toggles play mode.

Ball / Fish buttons for mini-games.

Health bar displayed on top left.

Food pan bottom-right.

Bed bottom-left.

Day/Night Cycle reflected by window and sky colors.

Optional fireworks during play mode (right-click).

7. Day/Night Cycle

Daytime: day value > 0.4

Nighttime: day value < 0.4

Automatic changes affect:

Sleep requirement

Health if cat sleeps too little

Visual changes:

Sun position

Sky color gradient
