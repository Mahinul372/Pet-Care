# Q-Learning agent (Buddy's brain).
#
# The whole of Buddy's knowledge lives in one table: Q[state][action],
# the estimated long-term value of taking `action` from `state`. The
# agent learns only by the Q-learning update rule -- there is no
# predefined route and no hardcoded sequence of moves anywhere.

import pickle
import random


class QLearningAgent:
    """Tabular Q-learning with epsilon-greedy action selection."""

    def __init__(self, alpha=0.10, gamma=0.90, epsilon=1.0,
                 epsilon_min=0.05, epsilon_decay=0.995):
        self.alpha = alpha            # learning rate: how much each
                                      # single experience moves a Q-value
        self.gamma = gamma            # discount factor: how much the
                                      # future matters vs. right now
        self.epsilon = epsilon        # exploration rate: how often Buddy
                                      # tries a random move instead of
                                      # his best-known one
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.q = {}                   # {state: [Q_up, Q_down, Q_left, Q_right]}

    # -- Q-table access ---------------------------------------------------
    def values(self, state):
        """The four Q-values for a state, created at 0.0 on first sight.
        A state Buddy has never visited has no knowledge yet, which is
        exactly what 0.0 means here."""
        if state not in self.q:
            self.q[state] = [0.0, 0.0, 0.0, 0.0]
        return self.q[state]

    def best_action(self, state):
        """The greedy action: the highest Q-value, with ties broken at
        random so Buddy does not always favour UP when several moves
        look equally good."""
        vals = self.values(state)
        best = max(vals)
        return random.choice([a for a, v in enumerate(vals) if v == best])

    def best_value(self, state):
        return max(self.values(state))

    # -- action selection -------------------------------------------------
    def choose_action(self, state, epsilon=None):
        """Epsilon-greedy: with probability epsilon Buddy explores (a
        random move), otherwise he exploits (his best-known move).
        Exploration is how he discovers better routes; exploitation is
        how he uses what he already knows."""
        if epsilon is None:
            epsilon = self.epsilon
        if random.random() < epsilon:
            return random.randrange(4), True    # explored
        return self.best_action(state), False   # exploited

    # -- the learning update ----------------------------------------------
    def update(self, state, action, reward, next_state, done):
        """One Q-learning update:
            Q(s,a) <- Q(s,a) + alpha * [r + gamma * max Q(s',a') - Q(s,a)]
        The next state's best value is 0 when the episode is over
        (there is no future after finding the bone or timing out).
        Returns every number the panel shows, so the displayed update
        is the real one, not an illustration."""
        old_q = self.values(state)[action]
        max_next = 0.0 if done else self.best_value(next_state)
        target = reward + self.gamma * max_next
        new_q = old_q + self.alpha * (target - old_q)
        self.values(state)[action] = new_q
        return {
            "state": state,
            "action": action,
            "old_q": old_q,
            "reward": reward,
            "max_next_q": max_next,
            "alpha": self.alpha,
            "gamma": self.gamma,
            "new_q": new_q,
            "td_error": target - old_q,
        }

    def decay_epsilon(self):
        """Explore a little less after every episode. Early on Buddy
        tries almost everything (epsilon near 1); later he mostly
        trusts what he has learned (epsilon near 0.05)."""
        self.epsilon = max(self.epsilon_min,
                           self.epsilon * self.epsilon_decay)

    # -- bookkeeping ------------------------------------------------------
    def reset(self):
        """Start learning from scratch: empty Q-table, epsilon back to 1."""
        self.q = {}
        self.epsilon = 1.0

    def greedy_policy(self):
        """The learned policy as {state: best action} for every state
        Buddy has visited. The garden draws one arrow per cell from
        this, so visitors can see the policy directly."""
        return {s: max(range(4), key=lambda a: v[a])
                for s, v in self.q.items()}

    # -- persistence ------------------------------------------------------
    def save(self, path):
        with open(path, "wb") as f:
            pickle.dump({
                "alpha": self.alpha,
                "gamma": self.gamma,
                "epsilon": self.epsilon,
                "epsilon_min": self.epsilon_min,
                "epsilon_decay": self.epsilon_decay,
                "q": self.q,
            }, f)

    @classmethod
    def load(cls, path):
        with open(path, "rb") as f:
            data = pickle.load(f)
        agent = cls(alpha=data["alpha"], gamma=data["gamma"],
                    epsilon=data["epsilon"], epsilon_min=data["epsilon_min"],
                    epsilon_decay=data["epsilon_decay"])
        agent.q = {tuple(s): list(v) for s, v in data["q"].items()}
        return agent
