import state
import heapq

def a_star(start: state.State, goal: state.State):
    if start.pos == goal.pos:
        return []

    priority = 0
    frontier = [start]
    expanded = set()
    frontier_cost = dict()
    frontier_cost[start] = 0

    while frontier != []:
        current = heapq.heappop(frontier)

        if current.pos == goal.pos:
            path = []
            while current.pos != start.pos: # co the loi
                path.append((current.pos, current.direction))
                current = current.parent
            path.reverse()
            return path

        expanded.add(current)

        children = current.gen_children()
        for child in children:
            if child in expanded:
                continue

            child.calc_heuristic(goal.pos)

            # Nếu chưa có trong frontier hoặc có f(n) nhỏ hơn
            if child not in frontier_cost or child.f() < frontier_cost[child]:
                frontier_cost[child] = child.f()
                if child.status == 'safe':
                    priority = 0
                elif child.status == 'uncertain':
                    priority = 1
                else:
                    continue

                heapq.heappush(frontier, child)

    return []

def choose_next_goal(current_state: state.State, world):
    # Tìm ô mục tiêu tiếp theo dựa trên trạng thái hiện tại và thế giới
    safe_cells = []
    for y in range(len(world)):
        for x in range(len(world[y])):
            if world[y][x]["safe"] and not world[y][x]["visited"]:
                safe_cells.append((x, y))

    if not safe_cells:
        print("No safe cells left to explore!")
        return (0, 0) # Trả về ô (0, 0) nếu không còn ô an toàn

    # Chọn ô mục tiêu gần nhất
    min_cost = float('inf')
    goal = (0, 0)
    for cell in safe_cells:
        cost = current_state.calc_heuristic(cell)
        if cost < min_cost:
            min_cost = cost
            goal = cell

    return goal