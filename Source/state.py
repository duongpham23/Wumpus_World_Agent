import wumpus_world
import agent as Agent

world = wumpus_world.world
N = wumpus_world.N

class State:
    def __init__(self, agent: Agent.Agent, status="safe", cost=0, heuristic=0, parent=None):
        self.agent = agent
        self.status = status      # trạng thái của ô (có thể là 'safe', 'dangerous', 'uncertain')
        self.cost = cost          # g(n) chi phí từ start đến state này
        self.heuristic = heuristic  # h(n) ước lượng chi phí đến goal
        self.parent = parent      # trạng thái cha để truy vết đường đi

    def f(self):
        return self.cost + self.heuristic

    def __eq__(self, other):
        return self.agent.pos == other.agent.pos and self.agent.direction == other.agent.direction

    def __hash__(self):
        return hash((self.agent.pos, self.agent.direction))

    def __lt__(self, other):
        priority = {'safe': 0, 'uncertain': 1}
        if self.status != other.status:
            return priority[self.status] < priority[other.status]
        return self.f() < other.f()

    def calc_heuristic(self, goal_pos):
        if self.agent.pos == goal_pos:
            self.heuristic = 0
            return self.heuristic

        x1, y1 = self.agent.pos
        x2, y2 = goal_pos
        # Tính khoảng cách Manhattan
        manhattan_dist = abs(x1 - x2) + abs(y1 - y2)

        # Chi phí quay đầu
        turn_cost = 0
        # Tính toán hướng của state hiên tại so với goal
        direction_map = {
            (1, 0): 'E', # Đông
            (-1, 0): 'W', # Tây
            (0, -1): 'S', # Nam
            (0, 1): 'N', # Bắc
            (1, 1): 'NE', # Đông Bắc
            (1, -1): 'SE', # Đông Nam
            (-1, 1): 'NW', # Tây Bắc
            (-1, -1): 'SW' # Tây Nam
        }

        dx = x2 - x1
        if dx != 0:
            dx = dx // abs(dx)  # Chỉ lấy hướng

        dy = y2 - y1
        if dy != 0:
            dy = dy // abs(dy)  # Chỉ lấy hướng

        direction_to_goal = direction_map[(dx, dy)]
        # Nếu cần quay 90 độ
        if (self.agent.direction == 'W' or self.agent.direction == 'E') and (direction_to_goal == 'N' or direction_to_goal == 'S'):
            turn_cost = 1
        elif (self.agent.direction == 'N' or self.agent.direction == 'S') and (direction_to_goal == 'E' or direction_to_goal == 'W'):
            turn_cost = 1
        elif self.agent.direction == 'N' and (direction_to_goal == 'SE' or direction_to_goal == 'SW'):
            turn_cost = 1
        elif self.agent.direction == 'S' and (direction_to_goal == 'NE' or direction_to_goal == 'NW'):
            turn_cost = 1
        elif self.agent.direction == 'E' and (direction_to_goal == 'SW' or direction_to_goal == 'NW'):
            turn_cost = 1
        elif self.agent.direction == 'W' and (direction_to_goal == 'SE' or direction_to_goal == 'NE'):
            turn_cost = 1
        # Nếu cần quay 180 độ
        elif (self.agent.direction == 'N' and direction_to_goal == 'S') or (self.agent.direction == 'S' and direction_to_goal == 'N'):
            turn_cost = 2
        elif (self.agent.direction == 'E' and direction_to_goal == 'W') or (self.agent.direction == 'W' and direction_to_goal == 'E'):
            turn_cost = 2
        # Nếu không cần quay
        else:
            turn_cost = 0

        self.heuristic = manhattan_dist + turn_cost
        return self.heuristic

    def gen_children(self):
        children = []

        new_agent = self.agent.clone()
        # Đi tới
        new_agent.move_forward()
        new_x, new_y = new_agent.pos

        # duyệt trên world để kiểm tra ô này có nguy hiểm không
        if wumpus_world.in_bounds(new_x, new_y):
            cell = world[new_y][new_x]
            if cell["safe"]:
                new_state = State(new_agent, "safe", self.cost + 1, 0, self)
                children.append(new_state)
            elif cell["uncertain"]:
                new_state = State(new_agent, "uncertain", self.cost + 10, 0, self)
                children.append(new_state)

        # Quay trái
        new_agent = self.agent.clone()
        new_agent.turn_left()
        # Kiểm tra xem có đập mặt vô tường không
        if not new_agent.facing_to_wall():
            new_state = State(new_agent, "safe", self.cost + 1, 0, self)
            children.append(new_state)

        # Quay phải
        new_agent = self.agent.clone()
        new_agent.turn_right()
        if not new_agent.facing_to_wall():
            new_state = State(new_agent, "safe", self.cost + 1, 0, self)
            children.append(new_state)

        return children