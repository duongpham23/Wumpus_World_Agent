import wumpus_world

world = wumpus_world.world

class State:
    def __init__(self, pos, direction='N', status="safe", cost=0, heuristic=0, parent=None):
        self.pos = pos            # (x, y)
        self.direction = direction  # hướng agent,  'N', 'S', 'E', 'W'
        self.status = status      # trạng thái của ô (có thể là 'safe', 'dangerous', 'uncertain')
        self.cost = cost          # g(n) chi phí từ start đến state này
        self.heuristic = heuristic  # h(n) ước lượng chi phí đến goal
        self.parent = parent      # trạng thái cha để truy vết đường đi

    def f(self):
        return self.cost + self.heuristic

    def __eq__(self, other):
        return self.pos == other.pos and self.direction == other.direction

    def __hash__(self):
        return hash((self.pos, self.direction))

    def __lt__(self, other):
        priority = {'safe': 0, 'uncertain': 1}
        if self.status != other.status:
            return priority[self.status] < priority[other.status]
        return self.f() < other.f()

    def calc_heuristic(self, goal_pos):
        if self.pos == goal_pos:
            self.heuristic = 0
            return self.heuristic

        x1, y1 = self.pos
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
        if (self.direction == 'W' or self.direction == 'E') and (direction_to_goal == 'N' or direction_to_goal == 'S'):
            turn_cost = 1
        elif (self.direction == 'N' or self.direction == 'S') and (direction_to_goal == 'E' or direction_to_goal == 'W'):
            turn_cost = 1
        elif self.direction == 'N' and (direction_to_goal == 'SE' or direction_to_goal == 'SW'):
            turn_cost = 1
        elif self.direction == 'S' and (direction_to_goal == 'NE' or direction_to_goal == 'NW'):
            turn_cost = 1
        elif self.direction == 'E' and (direction_to_goal == 'SW' or direction_to_goal == 'NW'):
            turn_cost = 1
        elif self.direction == 'W' and (direction_to_goal == 'SE' or direction_to_goal == 'NE'):
            turn_cost = 1
        # Nếu cần quay 180 độ
        elif (self.direction == 'N' and direction_to_goal == 'S') or (self.direction == 'S' and direction_to_goal == 'N'):
            turn_cost = 2
        elif (self.direction == 'E' and direction_to_goal == 'W') or (self.direction == 'W' and direction_to_goal == 'E'):
            turn_cost = 2
        # Nếu không cần quay
        else:
            turn_cost = 0

        self.heuristic = manhattan_dist + turn_cost
        return self.heuristic

    def gen_children(self):
        children = []
        
        # Đi tới
        new_x = self.pos[0]
        new_y = self.pos[1]

        if self.direction == 'N':  # Bắc
            new_y += 1
        elif self.direction == 'S':  # Nam
            new_y -= 1
        elif self.direction == 'E':  # Đông
            new_x += 1
        elif self.direction == 'W':  # Tây
            new_x -= 1

        new_pos = (new_x, new_y)

        # duyệt trên world để kiểm tra ô này có nguy hiểm không
        if wumpus_world.in_bounds(new_x, new_y):
            cell = world[new_y][new_x]
            if cell["safe"]:
                new_state = State(new_pos, self.direction, "safe", self.cost + 1, 0, self)
                children.append(new_state)
            elif cell["uncertain"]:
                new_state = State(new_pos, self.direction, "uncertain", self.cost + 1, 0, self)
                children.append(new_state)

        new_direction = self.direction
        # Quay trái
        if self.direction == 'N': # Bắc
            new_direction = 'W' # Tây
        elif self.direction == 'W': # Tây
            new_direction = 'S' # Nam
        elif self.direction == 'S': # Nam
            new_direction = 'E' # Đông
        elif self.direction == 'E': # Đông
            new_direction = 'N' # Bắc

        new_state = State(self.pos, new_direction, "safe", self.cost + 1, 0, self)
        children.append(new_state)

        # Quay phải
        if self.direction == 'N': # Bắc
            new_direction = 'E' # Đông
        elif self.direction == 'E': # Đông
            new_direction = 'S' # Nam
        elif self.direction == 'S': # Nam
            new_direction = 'W' # Tây
        elif self.direction == 'W': # Tây
            new_direction = 'N' # Bắc

        new_state = State(self.pos, new_direction, "safe", self.cost + 1, 0, self)
        children.append(new_state)

        return children