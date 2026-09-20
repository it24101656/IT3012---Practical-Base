# agent.py
import math
from collections import deque
import heapq

class GreedyGridAgent:
    """A simple agent that tries to move around systematically to clear the grid."""

    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']

    def sense_and_act(self, percept: dict) -> str:
        # If standing directly on food, or just wander / move towards coordinates
        pos = percept['agent_pos']
        # Simple heuristic or fallback random sweep
        return random.choice(self.actions_pool)

# IT24101656 IS-Lab03: Goal-based SearchAgent using BFS / DFS / UCS
# IT24101656 IS-Lab04: Added A* with Manhattan and Euclidean heuristics
class SearchAgent:
    """Offline planner: computes a path to the nearest food, then executes it step by step."""

    def __init__(self, algo='BFS', heuristic='manhattan'):
        # IT24101656 IS-Lab03: Current plan (list of action strings) and active algorithm
        self.plan = []
        self.active_algo = algo

        # IT24101656 IS-Lab04: Heuristic for A* ('manhattan' or 'euclidean')
        self.heuristic = heuristic

    # IT24101656 IS-Lab04: Manhattan distance 
    def manhattan_distance(self, pos, goal):
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    # IT24101656 IS-Lab04: Euclidean distance 
    def euclidean_distance(self, pos, goal):
        return math.sqrt((pos[0] - goal[0]) ** 2 + (pos[1] - goal[1]) ** 2)

    # IT24101656 IS-Lab03: Successor function - returns (action, (nx, ny)) pairs
    def _neighbors(self, node, walls_set, width, height):
        x, y = node
        moves = [('Up', (0, 1)), ('Down', (0, -1)),
                 ('Left', (-1, 0)), ('Right', (1, 0))]
        for action, (dx, dy) in moves:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in walls_set:
                yield action, (nx, ny)

    # IT24101656 IS-Lab03: BFS - FIFO frontier, optimal for unit step costs
    def bfs_search(self, start, goal, walls, grid_size):
        walls_set = set(map(tuple, walls))
        start, goal = tuple(start), tuple(goal)
        width, height = grid_size

        if start == goal:
            return []

        frontier = deque([(start, [])])
        reached = {start}

        while frontier:
            node, path = frontier.popleft()
            for action, nxt in self._neighbors(node, walls_set, width, height):
                if nxt in reached:
                    continue
                if nxt == goal:
                    return path + [action]
                reached.add(nxt)
                frontier.append((nxt, path + [action]))
        return None

    # IT24101656 IS-Lab03: DFS - LIFO stack, complete on finite graphs but suboptimal
    def dfs_search(self, start, goal, walls, grid_size):
        walls_set = set(map(tuple, walls))
        start, goal = tuple(start), tuple(goal)
        width, height = grid_size

        if start == goal:
            return []

        frontier = [(start, [])]
        reached = {start}

        while frontier:
            node, path = frontier.pop()
            for action, nxt in self._neighbors(node, walls_set, width, height):
                if nxt in reached:
                    continue
                if nxt == goal:
                    return path + [action]
                reached.add(nxt)
                frontier.append((nxt, path + [action]))
        return None

    # IT24101656 IS-Lab03: UCS - priority queue ordered by path cost g(n)
    def ucs_search(self, start, goal, walls, grid_size):
        walls_set = set(map(tuple, walls))
        start, goal = tuple(start), tuple(goal)
        width, height = grid_size

        if start == goal:
            return []

        # Heap entries: (cost_so_far, counter, node, path)
        counter = 0
        frontier = [(0, counter, start, [])]
        reached = set()

        while frontier:
            cost, _, node, path = heapq.heappop(frontier)
            if node in reached:
                continue
            reached.add(node)

            if node == goal:
                return path

            for action, nxt in self._neighbors(node, walls_set, width, height):
                if nxt in reached:
                    continue
                counter += 1
                heapq.heappush(frontier, (cost + 1, counter, nxt, path + [action]))
        return None

    # IT24101656 IS-Lab04: A* - priority queue 
    def astar_search(self, start_pos, goal_pos, walls, grid_size, heuristic_type='manhattan'):
        walls_set = set(map(tuple, walls))
        start, goal = tuple(start_pos), tuple(goal_pos)
        width, height = grid_size

        if start == goal:
            return []

        # IT24101656 IS-Lab04: Pick heuristic function based on caller's choice
        h = self.manhattan_distance if heuristic_type == 'manhattan' else self.euclidean_distance

        counter = 0
        # IT24101656 IS-Lab04: Heap entries: (f_cost, g_cost, counter, pos, path)
        g_start = 0
        f_start = g_start + h(start, goal)
        frontier = [(f_start, g_start, counter, start, [])]
        reached_states = set()

        while frontier:
            f_cost, g_cost, _, current_pos, path = heapq.heappop(frontier)

            if current_pos == goal:
                return path
            if current_pos in reached_states:
                continue
            reached_states.add(current_pos)

            for action, nxt in self._neighbors(current_pos, walls_set, width, height):
                if nxt in reached_states:
                    continue
                g_new = g_cost + 1
                h_new = h(nxt, goal)
                f_new = g_new + h_new
                counter += 1
                heapq.heappush(frontier, (f_new, g_new, counter, nxt, path + [action]))

        return None

    # IT24101656 IS-Lab03: Return the nearest food pellet to the agent's current position
    def _closest_food(self, agent_pos, all_food):
        ax, ay = agent_pos
        return min(all_food, key=lambda f: abs(f[0] - ax) + abs(f[1] - ay))

    # IT24101656 IS-Lab03: Pick a plan and pop the next action
    # IT24101656 IS-Lab04: Added 'AStar' branch with configurable heuristic
    def sense_and_act(self, percept: dict) -> str:
        # If we still have a plan, keep executing it
        if self.plan:
            return self.plan.pop(0)

        # Otherwise, build a new plan to the closest food
        start = tuple(percept['agent_pos'])
        goal = tuple(self._closest_food(percept['agent_pos'], percept['all_food']))
        walls = percept['walls']
        grid_size = percept['grid_size']

        if self.active_algo == 'BFS':
            self.plan = self.bfs_search(start, goal, walls, grid_size) or []
        elif self.active_algo == 'DFS':
            self.plan = self.dfs_search(start, goal, walls, grid_size) or []
        elif self.active_algo == 'UCS':
            self.plan = self.ucs_search(start, goal, walls, grid_size) or []
        elif self.active_algo == 'AStar':
            # IT24101656 IS-Lab04: Run A* with the chosen heuristic
            self.plan = self.astar_search(start, goal, walls, grid_size, self.heuristic) or []

        # If the plan is still empty (unreachable goal), fall back to a random turn
        if not self.plan:
            return percept['facing']

        return self.plan.pop(0)