import state
import heapq
import random
import wumpus_world

def a_star(start: state.State, goal: tuple):
    if start.agent.pos == goal:
        return []

    priority = 0
    frontier = [start]
    expanded = set()
    frontier_cost = dict()
    frontier_cost[start] = 0

    while frontier != []:
        current = heapq.heappop(frontier)

        if current.agent.pos == goal:
            path = []
            while current != start:
                path.append((current.agent.pos, current.agent.direction))
                current = current.parent
            path.reverse()
            return path

        expanded.add(current)

        children = current.gen_children()
        for child in children:
            if child in expanded:
                continue

            child.calc_heuristic(goal)

            # Nếu chưa có trong frontier hoặc có f(n) nhỏ hơn
            if child not in frontier_cost or child.f() < frontier_cost[child]:
                frontier_cost[child] = child.f()
                heapq.heappush(frontier, child)

    return []

def choose_next_goal(current_state: state.State, world):
    # Nếu đã có vàng, đi về
    if current_state.agent.gold_collected:
        return (0, 0)

    # Tìm ô mục tiêu tiếp theo dựa trên trạng thái hiện tại và thế giới
    safe_cells = []
    for y in range(len(world)):
        for x in range(len(world[y])):
            if (x, y) == current_state.agent.pos:
                continue
            
            if world[y][x]["safe"] and not world[y][x]["visited"]:
                safe_cells.append((x, y))

    if not safe_cells:
        print("No safe cells left to explore! Going to (0, 0)")
        return (0, 0)

    # Chọn ô mục tiêu gần nhất
    min_cost = float('inf')
    goal = (0, 0)
    for cell in safe_cells:
        cost = current_state.calc_heuristic(cell)
        if cost < min_cost:
            min_cost = cost
            goal = cell

    print("Found new safe cell:", goal)
    return goal

def choose_random_next_goal(curent_state: state.State, prev_pos: tuple, prev_goal: tuple):
    if curent_state.agent.gold_collected:
        return (0, 0)
    
    x, y = curent_state.agent.pos
    if prev_pos == (x, y):
        return prev_goal
    
    dx = [0, 0, -1, 1]
    dy = [1, -1, 0, 0]
    potential_next_goal = [prev_pos]
    
    for i in range(len(dx)):
        next_x = x + dx[i]
        next_y = y + dy[i]
        if (next_x, next_y) != prev_pos and wumpus_world.in_bounds(next_x, next_y):
            potential_next_goal.append((next_x, next_y))
            
    prev_pos_prop = 1 / len(potential_next_goal) / 2
    other_pos_prop = (1 - prev_pos_prop) / (len(potential_next_goal) - 1)
    next_goal_prop = [prev_pos_prop]
    for _ in range(len(potential_next_goal) - 1):
        next_goal_prop.append(other_pos_prop)
        
    next_goal = random.choices(potential_next_goal, weights=next_goal_prop, k=1)
    
    return next_goal[0]
    
    
            
    