# Training loop (headless). The OpenGL interface in main.py drives
# training one step at a time so the window stays responsive, but the
# episode logic lives here so it can be tested and reused without a
# window at all.

from .environment import MAX_STEPS


def run_episode(env, agent, max_steps=MAX_STEPS, epsilon=None):
    """Play one full episode: Buddy starts over, acts until he finds
    the bone or runs out of steps, and learns from every move.
    Returns what happened, with real numbers only."""
    state = env.reset()
    total_reward = 0.0
    steps = 0
    while steps < max_steps:
        action, _explored = agent.choose_action(state, epsilon)
        next_state, reward, done, _info = env.step(action)
        agent.update(state, action, reward, next_state, done)
        total_reward += reward
        steps += 1
        state = next_state
        if done:
            break
    success = (state == env.goal)
    agent.decay_epsilon()
    return {
        "steps": steps,
        "success": success,
        "total_reward": total_reward,
    }


def train_episodes(env, agent, count, max_steps=MAX_STEPS):
    """Run `count` episodes back to back and summarise them. Used by
    the 'Fast train' button (in small chunks, so the window never
    freezes) and by the tests."""
    successes = 0
    success_steps = []
    for _ in range(count):
        result = run_episode(env, agent, max_steps)
        if result["success"]:
            successes += 1
            success_steps.append(result["steps"])
    return {
        "episodes": count,
        "successes": successes,
        "success_rate": successes / count if count else 0.0,
        "avg_steps": (sum(success_steps) / len(success_steps)
                      if success_steps else None),
    }
