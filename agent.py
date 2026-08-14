# agent.py
import random

class GreedyGridAgent:
    """A simple agent that tries to move around systematically to clear the grid."""

    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']

    def sense_and_act(self, percept: dict) -> str:
        # If standing directly on food, or just wander / move towards coordinates
        pos = percept['agent_pos']
        # Simple heuristic or fallback random sweep
        return random.choice(self.actions_pool)

# IS_Lab02 Step 1.2
class SimpleReflexAgent:
    """Reacts only to the current percept. No memory, no __init__ state."""

    def sense_and_act(self, percept: dict) -> str:
        if percept['food_here']:
            return 'move_forward'          # collect by staying on the cell
        if percept['wall_ahead']:
            return 'turn_left'             #always turns the same way
        return 'move_forward'

# IS_Lab02 Step 1.3
class ModelBasedAgent:
    """Keeps an internal state so it can detect and break out of loops."""

    def __init__(self):
        self.last_action = None
        self.consecutive_turns = 0         # tracks how many times it's turned in a row

    def sense_and_act(self, percept: dict) -> str:
        # --- update internal state first (Transition Model) ---
        if percept['wall_ahead'] and self.last_action == 'turn_left':
            self.consecutive_turns += 1
        else:
            self.consecutive_turns = 0

        # --- choose action using memory-aware rules ---
        if percept['food_here']:
            action = 'move_forward'
        elif percept['wall_ahead']:
            # if we already tried turning left here before, try right instead
            action = 'turn_right' if self.consecutive_turns >= 1 else 'turn_left'
        else:
            action = 'move_forward'

        self.last_action = action
        return action