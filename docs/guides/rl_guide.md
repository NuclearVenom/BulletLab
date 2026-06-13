# Reinforcement Learning Guide

BulletLab exposes clean state/action interfaces for custom RL implementations without depending on PyTorch, Stable-Baselines3, or Gymnasium.

## State and Action Interface

```python
# Get state as a flat numpy array
state = robot.get_state()
# Shape: (13 + 2*N,) where N = num controllable joints
# [x, y, z, qx, qy, qz, qw, vx, vy, vz, wx, wy, wz, j0_pos..., j0_vel...]

# Apply action (target velocities for each controllable joint)
action = my_policy(state)        # → numpy array of length N
robot.apply_action(action)

# Apply torques instead
robot.apply_torques(torques)     # → numpy array of length N
```

## Manual Q-Learning Example

```python
import numpy as np
from bulletlab import Simulation, Robot

# Discretize state and action spaces yourself
def discretize(state: np.ndarray) -> int:
    ...

def select_action(q_table, state_idx, epsilon) -> int:
    if np.random.random() < epsilon:
        return np.random.randint(num_actions)
    return np.argmax(q_table[state_idx])

# Training loop
sim = Simulation(mode="direct")  # headless for speed
sim.start()
robot = Robot.load("cartpole.urdf", sim=sim)

Q = np.zeros((num_states, num_actions))
epsilon = 0.9

for episode in range(1000):
    robot.reset()
    state = discretize(robot.get_state())
    total_reward = 0

    for step in range(500):
        action_idx = select_action(Q, state, epsilon)
        action = action_space[action_idx]
        robot.apply_action(action)

        for _ in range(4):  # 4 physics steps per action
            sim.step()

        next_state = discretize(robot.get_state())
        reward = compute_reward(robot)
        done = check_done(robot)

        # Q-update
        Q[state, action_idx] += alpha * (
            reward + gamma * np.max(Q[next_state]) - Q[state, action_idx]
        )

        state = next_state
        total_reward += reward
        if done:
            break

    epsilon *= 0.99  # decay

sim.stop()
```

## Evolutionary Algorithm Example

```python
import numpy as np

def evaluate(policy_weights: np.ndarray, sim, robot) -> float:
    """Run one episode and return total reward."""
    robot.reset()
    total = 0.0
    for _ in range(500):
        state = robot.get_state()
        action = np.tanh(policy_weights @ state)  # simple linear policy
        robot.apply_action(action)
        sim.step()
        total += compute_reward(robot)
    return total

# Evolve
population = [np.random.randn(num_actions, 13 + 2*N) for _ in range(20)]

for generation in range(100):
    fitness = [evaluate(w, sim, robot) for w in population]
    survivors = [population[i] for i in np.argsort(fitness)[-10:]]

    # Mutate survivors
    new_pop = []
    for w in survivors:
        new_pop.append(w + 0.1 * np.random.randn(*w.shape))
    population = survivors + new_pop
```

## Tips for RL with BulletLab

1. **Use `mode="direct"`** for headless, fast training
2. **Use `sim.reset()`** between episodes (call `robot.reset()` too)
3. **Scale the timestep** to speed up training: `sim.timestep = 1/60`
4. **Normalize state** before passing to any policy
5. **Use `robot.speed`** and `robot.roll` as reward signals for locomotion
