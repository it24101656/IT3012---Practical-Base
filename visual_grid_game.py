# visual_grid_game.py
import random
import tkinter as tk
from agent import SearchAgent

class VisualGridHuntGame:
    """A flexible Pacman-style grid environment with support for configurable opponents and larger scales."""

    def __init__(self, width=10, height=10, facing='Up', num_food=10, num_opponents=2, num_traps=3, custom_walls=None):
        self.width = width
        self.height = height
        
        # IT24101656 IS-Lab02: Track the agent's current facing direction
        self.facing = facing
        # IT24101656 IS-Lab02: Track the previous facing direction before the last action
        self.facing_before = self.facing

        # IT24101656 IS-Lab02: Start position chosen so the agent spawns under a U-shaped wall pocket
        self.agent_pos = [0, 0]  # (x, y)

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            # Generate some default scattered walls for a larger grid
            self.walls = {(2, 2), (2, 3), (5, 5), (6, 5), (3, 7)}

        # Dynamically generate random food positions avoiding walls and agent start
        self.food_positions = set()
        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            pos_tuple = (fx, fy)
            if pos_tuple != (0, 0) and pos_tuple not in self.walls:
                self.food_positions.add(pos_tuple)

        # Generate adversarial opponents
        self.opponents = []
        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            op_pos = [ox, oy]
            if tuple(op_pos) != (0, 0) and tuple(op_pos) not in self.walls and tuple(op_pos) not in self.food_positions:
                self.opponents.append(op_pos)

        # IT24101656 IS-Lab01: New trap collection attribute
        self.toxic_traps = set()
        # IT24101656 IS-Lab01: Randomly place traps avoiding start, walls, and food
        while len(self.toxic_traps) < num_traps:
            tx = random.randint(0, self.width - 1)
            ty = random.randint(0, self.height - 1)
            pos = (tx, ty)
            if pos != (0, 0) and pos not in self.walls and pos not in self.food_positions:
                self.toxic_traps.add(pos)

        self.score = 0
        self.steps = 0
        self.collision = False

    # IT24101656 IS-Lab02: Return the cell directly in front of the agent based on its facing direction
    def _get_ahead_position(self):
        ax, ay = self.agent_pos
        if self.facing == 'Up':
            nx, ny = ax, ay + 1
        elif self.facing == 'Down':
            nx, ny = ax, ay - 1
        elif self.facing == 'Left':
            nx, ny = ax - 1, ay
        elif self.facing == 'Right':
            nx, ny = ax + 1, ay
        else:
            nx, ny = ax, ay

        if 0 <= nx < self.width and 0 <= ny < self.height:
            return (nx, ny)
        return None

    # IT24101656 IS-Lab02: Return the cell directly to the left of the agent based on its facing direction
    def _get_left_position(self):
        ax, ay = self.agent_pos
        if self.facing == 'Up':
            nx, ny = ax - 1, ay
        elif self.facing == 'Down':
            nx, ny = ax + 1, ay
        elif self.facing == 'Left':
            nx, ny = ax, ay - 1
        elif self.facing == 'Right':
            nx, ny = ax, ay + 1
        else:
            nx, ny = ax, ay

        if 0 <= nx < self.width and 0 <= ny < self.height:
            return (nx, ny)
        return None

    # IT24101656 IS-Lab02: Return the cell directly to the right of the agent based on its facing direction
    def _get_right_position(self):
        ax, ay = self.agent_pos
        if self.facing == 'Up':
            nx, ny = ax + 1, ay
        elif self.facing == 'Down':
            nx, ny = ax - 1, ay
        elif self.facing == 'Left':
            nx, ny = ax, ay + 1
        elif self.facing == 'Right':
            nx, ny = ax, ay - 1
        else:
            nx, ny = ax, ay

        if 0 <= nx < self.width and 0 <= ny < self.height:
            return (nx, ny)
        return None

    # IT24101656 IS-Lab01: New sensor. Detects if agent is standing on a toxic trap

    # IT24101656 IS-Lab02: Percept restricted to local booleans (partial observability) - global coordinates removed
    # IT24101656 IS-Lab02: Added wall_ahead, food_ahead, toxin_ahead, opponent_ahead - relative to facing direction
    # IT24101656 IS-Lab02: Added wall_left and wall_right for the model-based agent's decision-making
    # IT24101656 IS-Lab02: Added facing so the agent knows its own orientation
    # IT24101656 IS-Lab02: Removed remaining_food (global info - not directly perceivable in a partially observable world)
    def get_percept(self) -> dict:
        ahead_pos = self._get_ahead_position()
        left_pos = self._get_left_position()
        right_pos = self._get_right_position()

        opponent_positions_set = {tuple(op) for op in self.opponents}

        return {
            'facing': self.facing,

            'wall_ahead': ahead_pos is None or ahead_pos in self.walls,
            'wall_left': left_pos is None or left_pos in self.walls,
            'wall_right': right_pos is None or right_pos in self.walls,

            'food_here': tuple(self.agent_pos) in self.food_positions,
            'food_ahead': ahead_pos is not None and ahead_pos in self.food_positions,

            'toxin_here': tuple(self.agent_pos) in self.toxic_traps,
            'toxin_ahead': ahead_pos is not None and ahead_pos in self.toxic_traps,

            'opponent_here': tuple(self.agent_pos) in opponent_positions_set,
            'opponent_ahead': ahead_pos is not None and ahead_pos in opponent_positions_set,

            'collision': self.collision,

            # IT24101656 IS-Lab03: Added the agent's map data
            'agent_pos': tuple(self.agent_pos),
            'grid_size': (self.width, self.height),
            'walls': list(self.walls),
            'all_food': list(self.food_positions),
        }

    # IT24101656 IS-Lab02: Updated execute_action to treat direction changes as pure turns (no movement)
    def execute_action(self, action: str):
        self.steps += 1

        # IT24101656 IS-Lab02: Update facing_before and facing based on the action
        self.facing_before = self.facing
        self.facing = action

        # IT24101656 IS-Lab02: If the action changes direction, treat it as a pure turn - no movement
        # IT24101656 IS-Lab03: Only treat turn-style actions as pure turns
        if action.startswith('turn_'):
            self.facing = action.replace('turn_', '')
            return
        
        new_pos = list(self.agent_pos)

        if action == 'Up':
            new_pos[1] = min(self.height - 1, new_pos[1] + 1)
        elif action == 'Down':
            new_pos[1] = max(0, new_pos[1] - 1)
        elif action == 'Left':
            new_pos[0] = max(0, new_pos[0] - 1)
        elif action == 'Right':
            new_pos[0] = min(self.width - 1, new_pos[0] + 1)

        if tuple(new_pos) in self.walls:
            self.score -= 5
        else:
            self.agent_pos = new_pos

        tuple_pos = tuple(self.agent_pos)
        if tuple_pos in self.food_positions:
            self.food_positions.remove(tuple_pos)
            self.score += 20

        # IT24101656 IS-Lab01: Penalty for the agent for stepping on a toxic trap
        tuple_pos = tuple(self.agent_pos)
        if tuple_pos in self.toxic_traps:
            self.score -= 15

        for op in self.opponents:
            move = random.choice(['Up', 'Down', 'Left', 'Right', 'Stay'])
            if move == 'Up' and op[1] < self.height - 1:
                op[1] += 1
            elif move == 'Down' and op[1] > 0:
                op[1] -= 1
            elif move == 'Left' and op[0] > 0:
                op[0] -= 1
            elif move == 'Right' and op[0] < self.width - 1:
                op[0] += 1

            if op == self.agent_pos:
                self.score -= 50
                self.collision = True

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 60 or self.collision

# IT24101656 IS-Lab02: Simple Reflex Agent — pure IF-THEN condition-action rules, no memory
class SimpleReflexAgent:
    def sense_and_act(self, percept: dict) -> str:
        turn_left = {'Up': 'Left', 'Left': 'Down', 'Down': 'Right', 'Right': 'Up'}

        # IT24101656 IS-Lab02: Rule 1 — turn left if any danger is directly ahead
        if percept['wall_ahead'] or percept['toxin_ahead'] or percept['opponent_ahead']:
            return turn_left[percept['facing']]

        # IT24101656 IS-Lab02: Rule 2 — keep moving forward if food is directly ahead
        if percept['food_ahead']:
            return percept['facing']

        # IT24101656 IS-Lab02: Rule 3 — default: keep going forward
        return percept['facing']


# IT24101656 IS-Lab02: Model-Based Agent — maintains internal memory state to escape loops
class ModelBasedAgent:
    def __init__(self):
        # IT24101656 IS-Lab02: Estimated relative position from the start point
        self.rel_pos = (0, 0)
        # IT24101656 IS-Lab02: Count how many times each (rel_pos, facing) state has been visited
        self.visits = {}
        # IT24101656 IS-Lab02: Track the previous facing direction and action
        self.last_facing = None
        self.last_action = None

    def sense_and_act(self, percept: dict) -> str:
        turn_left = {'Up': 'Left', 'Left': 'Down', 'Down': 'Right', 'Right': 'Up'}
        turn_right = {'Up': 'Right', 'Right': 'Down', 'Down': 'Left', 'Left': 'Up'}
        dir_vectors = {'Up': (0, 1), 'Down': (0, -1), 'Left': (-1, 0), 'Right': (1, 0)}

        facing = percept['facing']

        # IT24101656 IS-Lab02: Transition Model — update estimated position if the last action was a move forward
        if (self.last_action is not None
                and self.last_facing is not None
                and self.last_action == self.last_facing):
            dx, dy = dir_vectors[self.last_facing]
            self.rel_pos = (self.rel_pos[0] + dx, self.rel_pos[1] + dy)

        # IT24101656 IS-Lab02: Sensor Model — form internal state from position and facing
        state = (self.rel_pos, facing)
        # IT24101656 IS-Lab02: Record this state's visit count
        self.visits[state] = self.visits.get(state, 0) + 1

        # IT24101656 IS-Lab02: Avoid immediate dangers (toxin or opponent ahead)
        if percept['toxin_ahead'] or percept['opponent_ahead']:
            action = turn_left[facing]
            self.last_facing = facing
            self.last_action = action
            return action

        # IT24101656 IS-Lab02: If a wall is ahead, use memory to decide: turn right if we've been here before, else turn left
        if percept['wall_ahead']:
            if self.visits[state] >= 2:
                action = turn_right[facing]
            else:
                action = turn_left[facing]
            self.last_facing = facing
            self.last_action = action
            return action

        # IT24101656 IS-Lab02: Default — move forward
        self.last_facing = facing
        self.last_action = facing
        return facing


class GridGameGUI:
    """Tkinter wrapper that dynamically scales cell sizes to keep larger grids on screen."""

    # IT24101656 IS-Lab01: Added num_traps so the GUI can pass it through to the environment

    def __init__(self, root, width=10, height=10, num_food=12, num_opponents=2, num_traps=3, walls=None):
        self.root = root
        self.root.title("IT3012 - Scalable Multi-Agent Grid Hunt")

        # IT24101656 IS-Lab01: Pass num_traps through to the environment
        self.env = VisualGridHuntGame(width=width, height=height, num_food=num_food, num_opponents=num_opponents, num_traps=num_traps,
                                      custom_walls=walls)

        # IT24101656 IS-Lab02: Uncomment this line to use the SimpleReflexAgent instead
        # self.agent = SimpleReflexAgent()
        # IT24101656 IS-Lab02: Uncomment this line to use ModelBasedAgent 
        #self.agent = ModelBasedAgent()

        # IT24101656 IS-Lab03: Use the SearchAgent - change the algo string to 'BFS', 'DFS', or 'UCS'
        self.agent = SearchAgent(algo='BFS')

        # Dynamically calculate cell size so the total canvas fits nicely within a 600x600 window ceiling
        max_canvas_dim = 600
        self.cell_size = max(20, min(max_canvas_dim // self.env.width, max_canvas_dim // self.env.height))

        canvas_w = self.env.width * self.cell_size
        canvas_h = self.env.height * self.cell_size

        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack()

        self.label = tk.Label(root, text="Score: 0 | Steps: 0", font=("Arial", 14))
        self.label.pack(pady=10)

        self.btn = tk.Button(root, text="Start Simulation", command=self.run_loop, font=("Arial", 12), bg="#000066",
                             fg="white")
        self.btn.pack(pady=5)

        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")

        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = (self.env.height - 1 - y) * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "#f1f5f9" if (x, y) not in self.env.walls else "#64748b"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#cbd5e1")

                # Only draw text if cell is large enough
                if self.cell_size >= 40 and (x, y) in self.env.walls:
                    self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text="W", fill="white",
                                            font=("Arial", 8, "bold"))

        for fx, fy in self.env.food_positions:
            offset = self.cell_size * 0.25
            x1 = fx * self.cell_size + offset
            y1 = (self.env.height - 1 - fy) * self.cell_size + offset
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5, fill="#f59e0b",
                                    outline="#d97706")

        # IT24101656 IS-Lab01: Render toxic traps as purple squares on the canvas     
        for tx, ty in self.env.toxic_traps:
            offset = self.cell_size * 0.25
            x1 = tx * self.cell_size + offset
            y1 = (self.env.height - 1 - ty) * self.cell_size + offset
            self.canvas.create_polygon(
                x1, y1,
                x1 + self.cell_size * 0.5, y1,
                x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5,
                fill="#7e22ce", outline="#581c87"
            )

        for ox, oy in self.env.opponents:
            offset = self.cell_size * 0.2
            x1 = ox * self.cell_size + offset
            y1 = (self.env.height - 1 - oy) * self.cell_size + offset
            self.canvas.create_rectangle(x1, y1, x1 + self.cell_size * 0.6, y1 + self.cell_size * 0.6, fill="#990000",
                                         outline="#7a0000")

        ax, ay = self.env.agent_pos
        offset = self.cell_size * 0.15
        x1 = ax * self.cell_size + offset
        y1 = (self.env.height - 1 - ay) * self.cell_size + offset
        self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.7, y1 + self.cell_size * 0.7, fill="#000066",
                                outline="#1e3a8a")

    def run_loop(self):
        self.btn.config(state="disabled")

        def step():
            if not self.env.is_done():
                # IT24101656 IS-Lab02: Let the chosen agent decide the action from the current percept
                percept = self.env.get_percept()
                action = self.agent.sense_and_act(percept)
                self.env.execute_action(action)

                self.draw_grid()
                self.label.config(text=f"Score: {self.env.score} | Steps: {self.env.steps} | Action: {action}")
                self.root.after(250, step)
            else:
                end_text = f"Collision! Game Over! Final Score: {self.env.score}" if self.env.collision else f"Finished! Final Score: {self.env.score}"
                self.label.config(text=end_text)
                self.btn.config(state="normal")

        step()


if __name__ == "__main__":
    root = tk.Tk()
    # Try a larger grid size like 12x12 with 15 food and 3 opponents!
    # IT24101656 IS-Lab02: Custom walls to demonstrate the agent getting stuck in a U-shaped corner
    # IT24101656 IS-Lab03: Maze walls with multiple paths and dead ends
    walls = [
        (2,8), (3,8), (4,8), (5,8), (6,8), (7,8),
        (4,2), (4,3), (4,4),
        (5,4), (6,4),
    ]
    app = GridGameGUI(root, width=12, height=12, num_food=15, num_opponents=0, , walls=walls)
    root.mainloop()