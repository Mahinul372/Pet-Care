# Buddy's Q-Learning Treasure Hunt

Buddy the dog learns to find a hidden bone in a garden, using **real
Q-Learning** — no scripted route, no hardcoded moves. Watch him
explore, make mistakes, update his Q-table, and get better. Then test
his learned policy in challenge mode.

Buddy is the same dog from the earlier Dog Care game: same golden-brown
coat, floppy ears, patch over one eye, and a tail that never stops
wagging. Only the game around him changed.

## How Q-Learning works here

- **Agent:** Buddy. **Environment:** a 7x7 garden grid with trees and
  rocks. **State:** the square Buddy stands on. **Action:** move up,
  down, left, or right.
- **Q-table:** one number per (square, move) — how good Buddy *thinks*
  that move is in the long run. It starts at zero everywhere and only
  changes through experience.
- **Update rule, every step:**
  `Q(s,a) <- Q(s,a) + alpha * [r + gamma * max Q(s',a') - Q(s,a)]`
  with alpha (learning rate) 0.10 and gamma (discount factor) 0.90.
- **Epsilon-greedy:** with probability epsilon Buddy tries a random
  move (exploration); otherwise he picks his best-known move
  (exploitation). Epsilon starts at 1.00 and decays 0.995 per episode
  down to 0.05, so early Buddy wanders and late Buddy trusts his table.
- **Policy:** usually the best-valued move per square. The garden draws
  one arrow per square showing it, so you can see the policy directly.

## Rewards

| Event | Reward |
|---|---|
| Finding the bone | +100 |
| One step closer to the bone | +5 |
| One step farther from the bone | -5 |
| Hitting a tree, rock, or fence | -10 |
| Every step | -1 |
| 60 steps without finding the bone | -20 |

The closer/farther pair is symmetric on purpose: it is a
potential-based shaping reward, so walking toward the bone and back
again cancels out (+5 - 5 = 0) and only the -1 per step remains. Buddy
can never farm rewards by pacing between two squares. (An asymmetric
pair such as +5 / -2 would pay him for exactly that.)

All rewards live as named constants at the top of
`rl/environment.py` — change them there and the whole game follows.

## Run it

```
pip install PyOpenGL
python main.py
```

## How to use it

1. **Start Training** — Buddy learns on his own. Watch the panel:
   the learning cycle lights up, every event is explained in plain
   words ("Buddy tried to move right but hit a tree. Penalty -10..."),
   the formula shows the last *real* update with Buddy's own numbers,
   and the Q-table section shows the four values for his current
   square. **Pause / Resume** freezes it so you can read.
   **Speed** cycles Slow / Medium / Fast. **Fast train 500** runs 500
   episodes in the background (the window stays responsive).
2. **Start Challenge** — Buddy walks from the start using only his
   learned policy (no learning during a challenge). You will see
   whether he reaches the bone and in how many steps. **Policy:
   trained / explore** switches between the greedy policy and
   epsilon-greedy (0.30) so you can feel the difference.
3. **Place Bone** — click a grass square to hide the bone somewhere
   else. **Edit Garden** — click a square to add or remove a tree or
   rock (the game refuses a change that blocks every path). A changed
   garden makes the old Q-table stale, so the panel says so and
   **Retrain on new garden** starts learning from scratch on it.
4. Click any garden square to inspect its four Q-values. Click Buddy's
   square (or **Follow Buddy**) to track him again.

Keys: `Space` pause/resume, `R` reset, `F` fast train 500,
`C` challenge, `S` save, `Q` save and quit.

There are no hunger, health, energy, or sleep mechanics any more —
nothing decays over time, so you can pause and read for as long as
you like. The doghouse is just decoration at the start square.

## Saving and loading

The Q-table, training statistics, epsilon, and the garden layout save
automatically to `rl/q_table.pkl` every 25 episodes (and with `S` or
`Q`). On the next start the app loads it if it exists, so you can
inspect the trained agent and keep training. **Reset** clears it and
starts from scratch. The file is local only; delete it to start fresh.

## Files

```
main.py               OpenGL window: garden, panel, buttons, timers
rl/environment.py     Garden grid, rewards, episode rules
rl/agent.py           Q-table, epsilon-greedy, the update rule
rl/train.py           Headless episode loop (used by Fast train)
rl/evaluate.py        Greedy-policy evaluation, kept apart from training
rl/q_table.pkl        Saved model (created while training)
requirements.txt      PyOpenGL only -- no TensorFlow, no GPU, no API
```

## Honest limits

Tabular Q-learning fits small, discrete worlds like this garden. A
higher Q-value means "looks better so far" — not a guarantee. Buddy
can still fail after training, and a changed garden needs retraining:
the table was learned for one layout. Training success (with
exploration on) understates what the policy knows; challenge mode
measures the policy itself.
