import time
import os
import sys
import wumpus_world
sys.stdout.reconfigure(encoding='utf-8')

# ===== Constants =====
N = wumpus_world.N

# ===== KB =====
KB = set()  # Knowledge Base

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

# ===== KB update =====
def update_KB(x, y, percept, KB, N):
    adj = [(x-1,y), (x+1,y), (x,y-1), (x,y+1)]

    if percept["breeze"]:
        KB.add(f"Breeze({x},{y})")
        pits = " OR ".join([f"Pit({i},{j})" for i,j in adj if wumpus_world.in_bounds(i,j)])
        KB.add(f"Breeze({x},{y}) <-> {pits}")
    else:
        KB.add(f"!Breeze({x},{y})")
        for i,j in adj:
            if wumpus_world.in_bounds(i,j):
                KB.add(f"!Pit({i},{j})")

    if percept["stench"]:
        KB.add(f"Stench({x},{y})")
        wumpuses = " OR ".join([f"Wumpus({i},{j})" for i,j in adj if wumpus_world.in_bounds(i,j)])
        KB.add(f"Stench({x},{y}) <-> {wumpuses}")
    else:
        KB.add(f"!Stench({x},{y})")
        for i,j in adj:
            if wumpus_world.in_bounds(i,j):
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
    
    world = wumpus_world.world
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