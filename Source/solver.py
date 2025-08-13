import state
import heapq

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