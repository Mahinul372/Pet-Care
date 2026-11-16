"""Buddy's Q-Learning Treasure Hunt -- reinforcement learning package.

environment: the garden grid, rewards, and episode rules.
agent:       tabular Q-learning with epsilon-greedy action selection.
train:       headless episode loop (the UI drives it step by step).
evaluate:    greedy-policy rollouts, kept separate from training.
"""

from .environment import GardenEnv, ACTIONS
from .agent import QLearningAgent

__all__ = ["GardenEnv", "QLearningAgent", "ACTIONS"]
