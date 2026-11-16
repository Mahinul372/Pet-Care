# Garden environment for Buddy's Q-Learning Treasure Hunt.
#
# The garden is a small discrete grid. Buddy (the agent) starts in one
# corner and must learn to reach the hidden bone (the goal) while
# avoiding trees and rocks (obstacles). Every value the agent sees --
# states, rewards, the next state -- comes from this class, and nothing
# else. The OpenGL code in main.py only draws what this class reports.

from collections import deque

# ---------------------------------------------------------------------------
# Rewards -- change these numbers here and the whole game follows. They are
# deliberately kept as named constants at the top of this file.
# ---------------------------------------------------------------------------
REWARD_GOAL = 100.0        # finding the bone
REWARD_CLOSER = 5.0        # moving one step closer to the bone
REWARD_FARTHER = -5.0      # moving one step farther from the bone
REWARD_OBSTACLE = -10.0    # walking into a tree, a rock, or the fence
REWARD_STEP = -1.0         # every step costs a little, so dawdling loses
REWARD_TIMEOUT = -20.0     # running out of steps without finding the bone

# The closer/farther pair is symmetric on purpose. It is a potential-based
# shaping reward: +5 for getting closer, -5 for getting farther. Walk
# toward the bone and back again and the two cancel out (+5 - 5 = 0),
# leaving only the -1 per step -- so Buddy can never farm rewards by
# pacing back and forth between two squares. (An asymmetric pair such as
# +5 / -2 would pay him for doing exactly that, which is a reward loop.)
MAX_STEPS = 60             # steps allowed per episode before a timeout

# Actions: 0 = UP, 1 = DOWN, 2 = LEFT, 3 = RIGHT.
ACTIONS = ("UP", "DOWN", "LEFT", "RIGHT")
_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


class GardenEnv:
    """A grid garden. States are (row, col) with row 0 at the top."""

    def __init__(self, size=7, obstacles=None, start=(6, 0), goal=(0, 6)):
        self.size = size
        self.start = tuple(start)
        self.goal = tuple(goal)
        if obstacles is None:
            # A staggered barrier across the middle: Buddy must learn to
            # walk around it instead of straight at the bone.
            obstacles = {(1, 2), (2, 2), (3, 2), (3, 3),
                         (3, 4), (4, 4), (5, 4)}
        self.obstacles = {tuple(o) for o in obstacles}
        self.state = self.start
        self.steps = 0

    # -- basic helpers ----------------------------------------------------
    def in_bounds(self, cell):
        r, c = cell
        return 0 <= r < self.size and 0 <= c < self.size

    def is_walkable(self, cell):
        return self.in_bounds(cell) and cell not in self.obstacles

    @staticmethod
    def manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def distance_to_goal(self, cell):
        return self.manhattan(cell, self.goal)

    # -- episode control --------------------------------------------------
    def reset(self):
        self.state = self.start
        self.steps = 0
        return self.state

    def step(self, action):
        """Take one action. Returns (next_state, reward, done, info).

        `info` carries everything the educational panel needs to explain
        the step in plain words: why the reward was given, the distances
        before and after, and a ready-made event sentence.
        """
        state = self.state
        d_before = self.distance_to_goal(state)
        dr, dc = _DELTAS[action]
        nxt = (state[0] + dr, state[1] + dc)

        if not self.is_walkable(nxt):
            # Ran into a tree, a rock, or the garden fence: Buddy stays
            # where he is and the move is penalised. (If this was also
            # his last allowed step, the timeout ends the episode
            # instead -- a stuck agent must not loop forever.)
            self.steps += 1
            if self.steps >= MAX_STEPS:
                return state, REWARD_TIMEOUT, True, {
                    "reason": "timeout",
                    "moved": False,
                    "distance_before": d_before,
                    "distance_after": d_before,
                    "event": ("Buddy used all %d steps without finding "
                              "the bone. Penalty %.0f -- wandering without "
                              "a result is costly, so long pointless walks "
                              "lose value." % (MAX_STEPS, REWARD_TIMEOUT)),
                }
            reward = REWARD_OBSTACLE
            info = {
                "reason": "obstacle",
                "moved": False,
                "distance_before": d_before,
                "distance_after": d_before,
                "event": ("Buddy tried to move %s from (%d, %d) but hit "
                          "an obstacle, so he stayed put. Penalty %.0f, "
                          "which makes moving %s from there look worse."
                          % (ACTIONS[action], state[0], state[1],
                             REWARD_OBSTACLE, ACTIONS[action])),
            }
            return state, reward, False, info

        self.state = nxt
        self.steps += 1
        d_after = self.distance_to_goal(nxt)

        if nxt == self.goal:
            reward = REWARD_GOAL
            info = {
                "reason": "goal",
                "moved": True,
                "distance_before": d_before,
                "distance_after": 0,
                "event": ("Buddy moved %s into (%d, %d) and found the "
                          "bone! Reward +%.0f -- the biggest prize in the "
                          "garden, so this move becomes much more "
                          "attractive."
                          % (ACTIONS[action], nxt[0], nxt[1], REWARD_GOAL)),
            }
            return nxt, reward, True, info

        if self.steps >= MAX_STEPS:
            reward = REWARD_TIMEOUT
            info = {
                "reason": "timeout",
                "moved": True,
                "distance_before": d_before,
                "distance_after": d_after,
                "event": ("Buddy used all %d steps without finding the "
                          "bone. Penalty %.0f -- wandering without a "
                          "result is costly, so long pointless walks lose "
                          "value." % (MAX_STEPS, REWARD_TIMEOUT)),
            }
            return nxt, reward, True, info

        if d_after < d_before:
            shaping = REWARD_CLOSER
            reason = "closer"
            why = ("one step closer to the bone (distance %d -> %d), so "
                   "a small reward of +%.0f." % (d_before, d_after,
                                                 REWARD_CLOSER))
        elif d_after > d_before:
            shaping = REWARD_FARTHER
            reason = "farther"
            why = ("one step farther from the bone (distance %d -> %d), "
                   "so a small penalty of %.0f." % (d_before, d_after,
                                                   REWARD_FARTHER))
        else:
            shaping = 0.0
            reason = "sideways"
            why = ("sideways -- the distance to the bone stayed %d, so "
                   "no shaping reward either way." % d_before)
        reward = REWARD_STEP + shaping
        info = {
            "reason": reason,
            "moved": True,
            "distance_before": d_before,
            "distance_after": d_after,
            "event": ("Buddy moved %s from (%d, %d) to (%d, %d), %s "
                      "Every step costs %.0f."
                      % (ACTIONS[action], state[0], state[1], nxt[0],
                         nxt[1], why, REWARD_STEP)),
        }
        return nxt, reward, False, info

    # -- layout editing (challenge mode) ----------------------------------
    def set_goal(self, cell):
        """Move the bone. Returns True if the cell is a legal goal spot."""
        cell = tuple(cell)
        if not self.is_walkable(cell) or cell == self.start:
            return False
        self.goal = cell
        return True

    def toggle_obstacle(self, cell):
        """Add or remove a tree/rock. Start, goal and Buddy's square are
        protected. Returns True if the layout changed."""
        cell = tuple(cell)
        if not self.in_bounds(cell):
            return False
        if cell in (self.start, self.goal, self.state):
            return False
        if cell in self.obstacles:
            self.obstacles.discard(cell)
        else:
            self.obstacles.add(cell)
        return True

    def goal_reachable(self):
        """Breadth-first search: is there any walkable path from the
        start to the bone? Used to stop the player building a garden
        Buddy can never solve."""
        seen = {self.start}
        queue = deque([self.start])
        while queue:
            cell = queue.popleft()
            if cell == self.goal:
                return True
            for dr, dc in _DELTAS:
                nxt = (cell[0] + dr, cell[1] + dc)
                if nxt not in seen and self.is_walkable(nxt):
                    seen.add(nxt)
                    queue.append(nxt)
        return False

    def optimal_path_length(self):
        """Length of the shortest walkable path from start to goal, or
        None if the bone cannot be reached. Used by the tests and by the
        panel to say how good Buddy's route is."""
        dist = {self.start: 0}
        queue = deque([self.start])
        while queue:
            cell = queue.popleft()
            if cell == self.goal:
                return dist[cell]
            for dr, dc in _DELTAS:
                nxt = (cell[0] + dr, cell[1] + dc)
                if nxt not in dist and self.is_walkable(nxt):
                    dist[nxt] = dist[cell] + 1
                    queue.append(nxt)
        return None

    # -- persistence ------------------------------------------------------
    def to_dict(self):
        return {
            "size": self.size,
            "start": list(self.start),
            "goal": list(self.goal),
            "obstacles": sorted(list(o) for o in self.obstacles),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(size=data["size"],
                   obstacles=[tuple(o) for o in data["obstacles"]],
                   start=tuple(data["start"]),
                   goal=tuple(data["goal"]))
