import random
import time
import os
import pygame
import sys
sys.stdout.reconfigure(encoding='utf-8')

# ===== Constants =====
N = 5
NUM_WUMPUS = 2
NUM_PITS = 2
DELAY = 1  # Delay giữa các bước

# Pygame constants
CELL_SIZE = 60
SCREEN_WIDTH = N * CELL_SIZE
SCREEN_HEIGHT = N * CELL_SIZE
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)
YELLOW = (255, 255, 0)  # Uncertain cells
ORANGE = (255, 165, 0)  # Safe cells

# ===== KB =====
KB = set()  # Knowledge Base

# ===== World init =====
world = [[{
    "pit": False,
    "wumpus": False,
    "breeze": False,
    "stench": False,
    "visited": False,
    "safe": False,      # Inference result
    "dangerous": False, # Inference result
    "uncertain": True   # Inference result (default)
} for _ in range(N)] for _ in range(N)]

def in_bounds(x, y):
    return 0 <= x < N and 0 <= y < N

# ===== BỔ SUNG: INFERENCE ENGINE =====
class InferenceEngine:
    """
    Inference Engine sử dụng Forward Chaining cho Wumpus World
    
    Rules (mệnh đề logic):
    R1: ¬Breeze(x,y) → ∀(i,j) adjacent to (x,y): ¬Pit(i,j)
    R2: ¬Stench(x,y) → ∀(i,j) adjacent to (x,y): ¬Wumpus(i,j)
    R3: Breeze(x,y) ∧ (only one possible pit cell) → Pit(that cell)
    R4: Stench(x,y) ∧ (only one possible wumpus cell) → Wumpus(that cell)
    R5: ¬Pit(x,y) ∧ ¬Wumpus(x,y) → Safe(x,y)
    """
    
    def __init__(self, grid_size):
        self.N = grid_size
        self.facts = set()  # Chứa các facts đã được chứng minh
        self.negations = set()  # Chứa các negations đã được chứng minh
        
    def add_fact(self, fact):
        """Thêm một fact đã chứng minh vào inference engine"""
        if fact.startswith('!'):
            self.negations.add(fact[1:])
        else:
            self.facts.add(fact)
    
    def is_fact_true(self, fact):
        """Kiểm tra fact có đúng không"""
        return fact in self.facts
    
    def is_fact_false(self, fact):
        """Kiểm tra fact có sai không"""
        return fact in self.negations
    
    def get_adjacent_cells(self, x, y):
        """Lấy danh sách các cells kề với (x,y)"""
        adjacent = []
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.N and 0 <= ny < self.N:
                adjacent.append((nx, ny))
        return adjacent
    
    def apply_rule_R1(self, KB):
        """
        Rule R1: ¬Breeze(x,y) → ∀(i,j) adjacent to (x,y): ¬Pit(i,j)
        Nếu không có gió tại (x,y) thì không có hố ở các ô kề bên
        """
        new_facts = set()
        for clause in KB:
            if clause.startswith('!Breeze('):
                # Extract coordinates from !Breeze(x,y)
                coords_str = clause[8:-1]  # Remove !Breeze( and )
                try:
                    coords = coords_str.split(',')
                    x, y = int(coords[0]), int(coords[1])
                    
                    # Áp dụng rule: không có pit ở các cell kề
                    for nx, ny in self.get_adjacent_cells(x, y):
                        pit_fact = f"Pit({nx},{ny})"
                        if not self.is_fact_false(pit_fact):
                            new_facts.add(f"!Pit({nx},{ny})")
                except:
                    continue
        return new_facts
    
    def apply_rule_R2(self, KB):
        """
        Rule R2: ¬Stench(x,y) → ∀(i,j) adjacent to (x,y): ¬Wumpus(i,j)
        Nếu không có mùi hôi tại (x,y) thì không có wumpus ở các ô kề bên
        """
        new_facts = set()
        for clause in KB:
            if clause.startswith('!Stench('):
                coords_str = clause[9:-1]  # Remove !Stench( and )
                try:
                    coords = coords_str.split(',')
                    x, y = int(coords[0]), int(coords[1])
                    
                    for nx, ny in self.get_adjacent_cells(x, y):
                        wumpus_fact = f"Wumpus({nx},{ny})"
                        if not self.is_fact_false(wumpus_fact):
                            new_facts.add(f"!Wumpus({nx},{ny})")
                except:
                    continue
        return new_facts
    
    def apply_rule_R3(self, KB):
        """
        Rule R3: Breeze(x,y) ∧ (chỉ còn 1 cell có thể có pit) → Pit(cell đó)
        """
        new_facts = set()
        for clause in KB:
            if clause.startswith('Breeze(') and ' <-> ' not in clause:
                coords_str = clause[7:-1]  # Remove Breeze( and )
                try:
                    coords = coords_str.split(',')
                    x, y = int(coords[0]), int(coords[1])
                    
                    # Tìm các cell kề có thể có pit
                    possible_pit_cells = []
                    for nx, ny in self.get_adjacent_cells(x, y):
                        pit_fact = f"Pit({nx},{ny})"
                        if not self.is_fact_false(pit_fact):
                            possible_pit_cells.append((nx, ny))
                    
                    # Nếu chỉ còn 1 cell có thể có pit
                    if len(possible_pit_cells) == 1:
                        nx, ny = possible_pit_cells[0]
                        pit_fact = f"Pit({nx},{ny})"
                        if not self.is_fact_true(pit_fact):
                            new_facts.add(pit_fact)
                except:
                    continue
        return new_facts
    
    def apply_rule_R4(self, KB):
        """
        Rule R4: Stench(x,y) ∧ (chỉ còn 1 cell có thể có wumpus) → Wumpus(cell đó)
        """
        new_facts = set()
        for clause in KB:
            if clause.startswith('Stench(') and ' <-> ' not in clause:
                coords_str = clause[8:-1]  # Remove Stench( and )
                try:
                    coords = coords_str.split(',')
                    x, y = int(coords[0]), int(coords[1])
                    
                    possible_wumpus_cells = []
                    for nx, ny in self.get_adjacent_cells(x, y):
                        wumpus_fact = f"Wumpus({nx},{ny})"
                        if not self.is_fact_false(wumpus_fact):
                            possible_wumpus_cells.append((nx, ny))
                    
                    if len(possible_wumpus_cells) == 1:
                        nx, ny = possible_wumpus_cells[0]
                        wumpus_fact = f"Wumpus({nx},{ny})"
                        if not self.is_fact_true(wumpus_fact):
                            new_facts.add(wumpus_fact)
                except:
                    continue
        return new_facts
    
    def apply_rule_R5(self):
        """
        Rule R5: ¬Pit(x,y) ∧ ¬Wumpus(x,y) → Safe(x,y)
        Nếu không có pit và không có wumpus thì an toàn
        """
        new_facts = set()
        for y in range(self.N):
            for x in range(self.N):
                pit_fact = f"Pit({x},{y})"
                wumpus_fact = f"Wumpus({x},{y})"
                safe_fact = f"Safe({x},{y})"
                
                if (self.is_fact_false(pit_fact) and 
                    self.is_fact_false(wumpus_fact) and 
                    not self.is_fact_true(safe_fact)):
                    new_facts.add(safe_fact)
        return new_facts
    
    def forward_chaining(self, KB):
        """
        Forward Chaining: áp dụng các rules cho đến khi không có fact mới
        """
        max_iterations = 50
        iteration = 0
        
        while iteration < max_iterations:
            old_facts_count = len(self.facts) + len(self.negations)
            
            # Áp dụng các rules
            new_facts_R1 = self.apply_rule_R1(KB)
            new_facts_R2 = self.apply_rule_R2(KB)
            new_facts_R3 = self.apply_rule_R3(KB)
            new_facts_R4 = self.apply_rule_R4(KB)
            new_facts_R5 = self.apply_rule_R5()
            
            # Thêm các facts mới
            all_new_facts = new_facts_R1 | new_facts_R2 | new_facts_R3 | new_facts_R4 | new_facts_R5
            for fact in all_new_facts:
                self.add_fact(fact)
            
            # Kiểm tra xem có facts mới không
            new_facts_count = len(self.facts) + len(self.negations)
            if new_facts_count == old_facts_count:
                break  # Không có facts mới, dừng
                
            iteration += 1
    
    def infer_cell_status(self, x, y, KB):
        """
        Suy luận trạng thái của cell (x,y): safe, dangerous, hoặc uncertain
        """
        # Reset inference engine
        self.facts.clear()
        self.negations.clear()
        
        # Thêm các facts từ KB
        for clause in KB:
            if ('(' in clause and ')' in clause and 
                ' <-> ' not in clause and ' OR ' not in clause):
                self.add_fact(clause)
        
        # Chạy forward chaining
        self.forward_chaining(KB)
        
        # Kiểm tra trạng thái cell
        pit_fact = f"Pit({x},{y})"
        wumpus_fact = f"Wumpus({x},{y})"
        safe_fact = f"Safe({x},{y})"
        
        if self.is_fact_true(pit_fact) or self.is_fact_true(wumpus_fact):
            return 'dangerous'
        elif (self.is_fact_false(pit_fact) and self.is_fact_false(wumpus_fact)) or self.is_fact_true(safe_fact):
            return 'safe'
        else:
            return 'uncertain'

# Tạo inference engine instance
inference_engine = InferenceEngine(N)

# ===== BỔ SUNG: CẬP NHẬT WORLD VỚI INFERENCE =====
def update_world_with_inference(world, KB):
    """
    Cập nhật trạng thái inference cho tất cả các cells chưa được thăm
    """
    for y in range(N):
        for x in range(N):
            if not world[y][x]["visited"]:
                status = inference_engine.infer_cell_status(x, y, KB)
                
                # Reset trạng thái cũ
                world[y][x]["safe"] = False
                world[y][x]["dangerous"] = False
                world[y][x]["uncertain"] = False
                
                # Set trạng thái mới
                if status == 'safe':
                    world[y][x]["safe"] = True
                elif status == 'dangerous':
                    world[y][x]["dangerous"] = True
                else:
                    world[y][x]["uncertain"] = True

# ===== KB update =====
def update_KB(x, y, percept, KB, N):
    adj = [(x-1,y), (x+1,y), (x,y-1), (x,y+1)]

    if percept["breeze"]:
        KB.add(f"Breeze({x},{y})")
        pits = " OR ".join([f"Pit({i},{j})" for i,j in adj if in_bounds(i,j)])
        KB.add(f"Breeze({x},{y}) <-> {pits}")
    else:
        KB.add(f"!Breeze({x},{y})")
        for i,j in adj:
            if in_bounds(i,j):
                KB.add(f"!Pit({i},{j})")

    if percept["stench"]:
        KB.add(f"Stench({x},{y})")
        wumpuses = " OR ".join([f"Wumpus({i},{j})" for i,j in adj if in_bounds(i,j)])
        KB.add(f"Stench({x},{y}) <-> {wumpuses}")
    else:
        KB.add(f"!Stench({x},{y})")
        for i,j in adj:
            if in_bounds(i,j):
                KB.add(f"!Wumpus({i},{j})")

    if percept["glitter"]:
        KB.add(f"Glitter({x},{y}) <-> Gold({x},{y})")

    KB.add(f"Visited({x},{y})")
    KB.add(f"Safe({x},{y}) <-> !Pit({x},{y}) AND !Wumpus({x},{y})")

# ===== BỔ SUNG: IN KB VÀ INFERENCE RESULTS =====
def print_KB_with_inference(KB, x, y, percept):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"🤖 Agent at ({x}, {y}) | Percepts: {percept}")
    print("📚 Knowledge Base:")
    for clause in sorted(KB):
        print("  ", clause)
    print("-" * 60)
    
    # In kết quả inference
    print("🧠 Inference Results:")
    for row in range(N-1, -1, -1):  # In từ trên xuống
        line = f"Row {row}: "
        for col in range(N):
            cell = world[row][col]
            if cell["visited"]:
                line += "[V] "
            elif cell["safe"]:
                line += "[S] "
            elif cell["dangerous"]: 
                line += "[D] "
            elif cell["uncertain"]:
                line += "[?] "
            else:
                line += "[ ] "
        print(line)
    print("Legend: [V]=Visited, [S]=Safe, [D]=Dangerous, [?]=Uncertain")
    print("-" * 60)

# ===== World setup =====
def place_feature(key, count):
    placed = 0
    while placed < count:
        x = random.randint(0, N - 1)
        y = random.randint(0, N - 1)
        if (x, y) == (0, 0):
            continue
        if not world[y][x]["wumpus"] and not world[y][x]["pit"]:
            world[y][x][key] = True
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if in_bounds(nx, ny):
                    if key == "pit":
                        world[ny][nx]["breeze"] = True
                    elif key == "wumpus":
                        world[ny][nx]["stench"] = True
            placed += 1

# ===== BỔ SUNG: Pygame draw với inference visualization =====
def draw_world_with_inference(screen, world, agent_x, agent_y, font):
    screen.fill(BLACK)
    for y in range(N):
        for x in range(N):
            rect = pygame.Rect(x * CELL_SIZE, (N - 1 - y) * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            cell = world[y][x]
            
            # Chọn màu dựa trên trạng thái inference
            if cell["visited"]:
                color = DARK_GRAY
            elif cell["safe"]:
                color = ORANGE  # Màu cam cho safe cells
            elif cell["dangerous"]:
                color = RED
            elif cell["uncertain"]:
                color = YELLOW
            else:
                color = GRAY
                
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)

            # Vẽ agent
            if (x, y) == (agent_x, agent_y):
                text = font.render("A", True, GREEN)
                screen.blit(text, (rect.x + 15, rect.y + 10))
            
            # Vẽ features thực tế (chỉ cho debug - thường ẩn)
            elif cell["wumpus"]:
                text = font.render("W", True, RED)
                screen.blit(text, (rect.x + 15, rect.y + 10))
            elif cell["pit"]:
                text = font.render("P", True, BLACK)
                screen.blit(text, (rect.x + 15, rect.y + 10))
            
            # Vẽ percepts
            percept_texts = []
            if cell["breeze"]:
                percept_texts.append(("B", BLUE))
            if cell["stench"]:
                percept_texts.append(("S", PURPLE))
            
            # Hiển thị percepts
            for i, (symbol, color) in enumerate(percept_texts):
                x_offset = 5 + (i % 2) * 30
                y_offset = 35
                text = pygame.font.Font(None, 20).render(symbol, True, color)
                screen.blit(text, (rect.x + x_offset, rect.y + y_offset))

# ===== Simulation =====
def simulate_agent(world):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Wumpus World with Inference Engine")
    font = pygame.font.Font(None, 36)

    x, y = 0, 0
    running = True
    for row in range(N):
        for col in range(N):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            if not running: break

            world[y][x]["visited"] = True
            percept = {
                "breeze": world[y][x]["breeze"],
                "stench": world[y][x]["stench"],
                "glitter": False
            }
            
            # Cập nhật KB
            update_KB(x, y, percept, KB, N)
            
            # BỔ SUNG: Chạy inference engine
            update_world_with_inference(world, KB)
            
            # In thông tin
            print_KB_with_inference(KB, x, y, percept)

            # Vẽ world với inference visualization
            draw_world_with_inference(screen, world, x, y, font)
            pygame.display.flip()
            time.sleep(DELAY)

            if row % 2 == 0:
                if x < N - 1:
                    x += 1
                else:
                    y += 1
            else:
                if x > 0:
                    x -= 1
                else:
                    y += 1
            if y >= N:
                running = False

    time.sleep(3)  # Chờ trước khi đóng
    pygame.quit()

# ===== Main =====
if __name__ == "__main__":
    print("🎮 Initializing Wumpus World with Inference Engine...")
    place_feature("wumpus", NUM_WUMPUS)
    place_feature("pit", NUM_PITS)
    print(f"📍 Placed {NUM_WUMPUS} Wumpuses and {NUM_PITS} Pits")
    print("🚀 Starting simulation...")
    simulate_agent(world)