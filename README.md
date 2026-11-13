# Dog Care — Buddy

A 2D OpenGL-based virtual pet care game. You take care of **Buddy**, a
golden-brown dog: feed him kibble and bones from his bowl, let him sleep
in his dog house, and play fetch with him. Hunger, health and the
day/night cycle keep running, so you have to look after him.

The game is drawn with OpenGL points, lines and circles, using the
midpoint line and circle algorithms — the whole scene (Buddy, his house,
his bowls, the sun and clouds) is plotted point by point.

## 1. Buddy

Buddy is drawn with solid filled shapes (`draw_dog()`): a golden-brown
coat with a cream belly and muzzle, floppy ears, a dark patch over one
eye, and a tail that never stops wagging.

His face changes with his mood:

- Happy smile with his tongue out when he is doing well
- Open mouth while eating
- Frown when he is unhappy (health at zero)
- Closed sleepy eyes while he sleeps
- Wide excited eyes when fireworks go off

He walks with the LEFT / RIGHT arrow keys and jumps with the UP arrow
key. Jumping is how you catch a bone mid-air.

## 2. Pet stats

- **Health** (green bar, top left) drops if Buddy goes hungry or misses
  sleep, and reaches zero only if he is badly neglected.
- **Hunger** grows over time and eats into health — feed him before the
  bowl is empty.
- **Sleep** follows the day/night cycle: he gets tired at night and
  wakes up in the morning.
- **Unhappiness** sets in when health reaches zero. Feed him to make him
  happy again.

## 3. Feeding

Buddy eats from a steel-blue food bowl (bottom right), filled with
kibble and two bones, with a water bowl beside it.

- Walk up to the bowl and press **E** to eat. Each bite lowers hunger
  and raises health a little.
- When the bowl is empty, press **E** again next to it to refill it
  with fresh kibble.

## 4. Sleeping

Buddy sleeps in his dog house (bottom left) — red roof, arched door,
and a little bone sign above the door.

- Walk up to the house and press **B** to sleep. He can only sleep at
  night (when the sky goes dark); during the day the game tells you to
  play instead.
- Press **B** again to wake him up.

## 5. Mini-games

Press **PLAY** (top right) to enter the playroom, then pick a game with
the buttons.

### a. Throw the Bone (fetch)

Click the bone button and a bone is thrown across the playroom in an
arc. Two ways to score:

- **Fetch it:** run under the bone with the arrow keys and walk over it
  where it lands.
- **Catch it mid-air:** jump (UP arrow) while standing under the flying
  bone.

Each fetch or catch scores 1 point. A new bone is thrown a moment
later. Click the bone button again (or STOP) to see your final score.

### b. Fetch Ball

Click the ball button, then push the ball with **W** (right) and **Q**
(left). Buddy has to stand next to the ball to push it. Score a point
every time the ball crosses the goal — the goal switches sides after
each goal, so keep chasing it.

## 6. User interface

- **PLAY / STOP** button toggles play mode.
- **Ball / Bone** buttons pick a mini-game.
- **Health bar** (top left) with a heart.
- **Food bowl and water bowl** (bottom right), **dog house**
  (bottom left).
- **Day/night cycle** in the window: blue sky with sun and clouds by
  day, dark sky with stars by night.
- **Fireworks** in the playroom: right-click anywhere in the playroom
  and Buddy jumps with excitement.

## 7. Day / night cycle

- Daytime: the sky is bright, the sun is up, clouds drift in the
  window.
- Nighttime: the sky darkens, stars come out, and Buddy gets sleepy.
  If he stays up too late his health drops, so put him to bed.

## How to run

Requires Python 3 and PyOpenGL:

```bash
pip install PyOpenGL
python main.py
```

## Controls

| Key / mouse | What it does |
| --- | --- |
| LEFT / RIGHT arrows | Walk Buddy |
| UP arrow | Jump (catch the bone mid-air) |
| E | Eat from the food bowl / refill it |
| B | Sleep in / wake up from the dog house |
| W / Q | Push the ball right / left |
| PLAY / STOP button | Enter / leave the playroom |
| Ball button | Start / stop the fetch ball game |
| Bone button | Start / stop the throw-the-bone game |
| Right-click | Fireworks in the playroom |
