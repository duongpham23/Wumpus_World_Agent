import wumpus_world

N = wumpus_world.N
NUM_WUMPUS = wumpus_world.NUM_WUMPUS
world = wumpus_world.world

class Agent:
    def __init__(self, pos, direction, num_arrow=1):
        self.pos = pos # (x, y)
        self.direction = direction
        self.num_arrow = num_arrow
        self.score = 0
        self.gold_collected = False

    def move_forward(self):
        if self.facing_to_wall():
            return False

        new_x, new_y = self.pos
        if self.direction == 'N':
            new_y += 1
        elif self.direction == 'S':
            new_y -= 1
        elif self.direction == 'E':
            new_x += 1
        elif self.direction == 'W':
            new_x -= 1
        self.pos = (new_x, new_y)
        self.score -= 1
        
        return True

    def turn_left(self):
        if self.direction == 'N': # Bắc
            self.direction = 'W' # Tây
        elif self.direction == 'W': # Tây
            self.direction = 'S' # Nam
        elif self.direction == 'S': # Nam
            self.direction = 'E' # Đông
        elif self.direction == 'E': # Đông
            self.direction = 'N' # Bắc
        self.score -= 1

    def turn_right(self):
        if self.direction == 'N': # Bắc
            self.direction = 'E' # Đông
        elif self.direction == 'E': # Đông
            self.direction = 'S' # Nam
        elif self.direction == 'S': # Nam
            self.direction = 'W' # Tây
        elif self.direction == 'W': # Tây
            self.direction = 'N' # Bắc
        self.score -= 1

    def grab_gold(self):
        x, y = self.pos
        if wumpus_world.in_bounds(x, y):
            cell = world[y][x]
            if cell["glitter"]:
                cell["glitter"] = False
                self.score += 100
                self.gold_collected = True
    
    def climb_out(self):
        x, y = self.pos
        if (x, y) == (0, 0):
            if self.gold_collected:
                self.score += 1000

    def shoot_arrow(self):
        x, y = self.pos
        self.num_arrow -= 1
        self.score -= 10

        print("💥 Shot arrow in direction:", self.direction)

        if self.direction == 'N':
            for i in range(y, N):
                if world[i][x]["wumpus"]:
                    print("💥 Shot Wumpus at", (x, i))
                    world[i][x]["wumpus"] = False
                    wumpus_world.wumpus_update_stench()
                    return True
        elif self.direction == 'S':
            for i in range(y, -1, -1):
                if world[i][x]["wumpus"]:
                    print("💥 Shot Wumpus at", (x, i))
                    world[i][x]["wumpus"] = False
                    wumpus_world.wumpus_update_stench()
                    return True
        elif self.direction == 'E':
            for i in range(x, N):
                if world[y][i]["wumpus"]:
                    print("💥 Shot Wumpus at", (i, y))
                    world[y][i]["wumpus"] = False
                    wumpus_world.wumpus_update_stench()
                    return True
        else:  # direction == 'W'
            for i in range(x, -1, -1):
                if world[y][i]["wumpus"]:
                    print("💥 Shot Wumpus at", (i, y))
                    world[y][i]["wumpus"] = False
                    wumpus_world.wumpus_update_stench()
                    return True
        print("❌ No Wumpus hit")
        return False

    def facing_to_wall(self):
        x, y = self.pos
        if x == 0 and self.direction == 'W':
            return True
        elif x == N - 1 and self.direction == 'E':
            return True
        elif y == 0 and self.direction == 'S':
            return True
        elif y == N - 1 and self.direction == 'N':
            return True
        return False

    def update(self, pos, direction):
        self.pos = pos
        self.direction = direction
        self.score -= 1

        x, y = self.pos
        if world[y][x]["uncertain"]:
            print("❗️ Come to an uncertain cell:", (x, y))
        else:
            print("✅ Come to a safe cell:", (x, y))


    def clone(self):
        new_agent = Agent(self.pos, self.direction, self.num_arrow)
        new_agent.score = self.score
        new_agent.gold_collected = self.gold_collected
        return new_agent