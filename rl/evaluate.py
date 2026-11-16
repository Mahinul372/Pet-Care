# Evaluation: how good is Buddy's learned policy, when he stops
# exploring and simply does what the Q-table says is best?
#
# Evaluation is deliberately separate from training. During training
# Buddy explores (epsilon > 0), so training success is noisy and
# understates what he actually knows. Evaluation turns exploration off
# (epsilon = 0) and measures the policy itself.

from .environment import MAX_STEPS
from .train import run_episode


def evaluate(env, agent, episodes=50, max_steps=MAX_STEPS):
    """Run greedy episodes and report the policy's real performance."""
    successes = 0
    success_steps = []
    for _ in range(episodes):
        result = run_episode(env, agent, max_steps, epsilon=0.0)
        if result["success"]:
            successes += 1
            success_steps.append(result["steps"])
    return {
        "episodes": episodes,
        "successes": successes,
        "success_rate": successes / episodes if episodes else 0.0,
        "avg_steps": (sum(success_steps) / len(success_steps)
                      if success_steps else None),
    }


def greedy_path(env, agent, max_steps=MAX_STEPS):
    """Follow the greedy policy from the start and return the list of
    states Buddy walks through. Returns None if the policy loops or
    times out instead of reaching the bone -- a real failure, shown
    honestly, not hidden."""
    state = env.reset()
    path = [state]
    seen = {state}
    for _ in range(max_steps):
        action = agent.best_action(state)
        next_state, _reward, done, _info = env.step(action)
        path.append(next_state)
        if next_state == env.goal:
            return path
        if next_state in seen:
            return None          # walking in circles: the policy failed
        seen.add(next_state)
        state = next_state
    return None
