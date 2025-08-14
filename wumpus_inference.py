import time
import os
import sys
import wumpus_world
import agent as Agent
sys.stdout.reconfigure(encoding='utf-8')

# ===== Constants =====
N = wumpus_world.N
world = wumpus_world.world

# ===== KB =====
KB = set()  # Knowledge Base

# ===== FIXED: INFERENCE ENGINE =====
class InferenceEngine:
    """
    Inference Engine sử dụng Forward Chaining cho Wumpus World - LOGIC CHÍNH XÁC
    
    Rules được sửa lại với logic chính xác:
    R1: ¬Breeze(x,y) → ∀(i,j) adjacent to (x,y): ¬Pit(i,j)
    R2: ¬Stench(x,y) → ∀(i,j) adjacent to (x,y): ¬Wumpus(i,j)  
    R3: Breeze(x,y) ∧ (chưa tìm thấy pit nào trong adjacent) ∧ (chỉ còn 1 cell chưa biết) 
        → Pit(cell đó)
    R4: Stench(x,y) ∧ (chưa tìm thấy wumpus nào trong adjacent) ∧ (chỉ còn 1 cell chưa biết)
        → Wumpus(cell đó)
    R5: ¬Pit(x,y) ∧ ¬Wumpus(x,y) → Safe(x,y)
    R6: Pit(x,y) → Dangerous(x,y)
    R7: Wumpus(x,y) → Dangerous(x,y)
    
    Nguyên tắc: Chỉ kết luận khi CHẮC CHẮN dựa trên logic propositional
    """
    
    def __init__(self, grid_size):
        self.N = grid_size
        self.known_facts = {}  # Dictionary để lưu trạng thái của mỗi fact
        
    def parse_fact(self, fact_str):
        """Parse fact string thành (predicate, x, y, is_negative)"""
        is_negative = fact_str.startswith('!')
        if is_negative:
            fact_str = fact_str[1:]
        
        if '(' not in fact_str or ')' not in fact_str:
            return None
            
        predicate = fact_str.split('(')[0]
        coords_str = fact_str.split('(')[1].split(')')[0]
        
        try:
            coords = coords_str.split(',')
            x, y = int(coords[0]), int(coords[1])
            return (predicate, x, y, is_negative)
        except:
            return None
    
    def set_fact(self, predicate, x, y, value):
        """Set giá trị của một fact"""
        key = f"{predicate}({x},{y})"
        self.known_facts[key] = value
    
    def get_fact(self, predicate, x, y):
        """Lấy giá trị của một fact (True, False, hoặc None nếu chưa biết)"""
        key = f"{predicate}({x},{y})"
        return self.known_facts.get(key, None)
    
    def get_adjacent_cells(self, x, y):
        """Lấy danh sách các cells kề với (x,y)"""
        adjacent = []
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.N and 0 <= ny < self.N:
                adjacent.append((nx, ny))
        return adjacent

    def apply_rule_R1_R2(self, KB):
        """
        R1: ¬Breeze(x,y) → ∀(i,j) adjacent: ¬Pit(i,j)
        R2: ¬Stench(x,y) → ∀(i,j) adjacent: ¬Wumpus(i,j)
        """
        new_inferences = []
        
        for clause in KB:
            if clause.startswith('!Breeze('):
                parsed = self.parse_fact(clause)
                if parsed:
                    _, x, y, _ = parsed
                    for nx, ny in self.get_adjacent_cells(x, y):
                        if self.get_fact('Pit', nx, ny) is None:
                            self.set_fact('Pit', nx, ny, False)
                            new_inferences.append(f"!Pit({nx},{ny}) [từ R1: !Breeze({x},{y})]")
            
            elif clause.startswith('!Stench('):
                parsed = self.parse_fact(clause)
                if parsed:
                    _, x, y, _ = parsed
                    for nx, ny in self.get_adjacent_cells(x, y):
                        if self.get_fact('Wumpus', nx, ny) is None:
                            self.set_fact('Wumpus', nx, ny, False)
                            new_inferences.append(f"!Wumpus({nx},{ny}) [từ R2: !Stench({x},{y})]")
        
        return new_inferences
    
    def apply_rule_R3_R4(self, KB):
        """
        R3: Breeze(x,y) ∧ (tất cả adjacent trừ 1 đều ¬Pit) ∧ (chưa có pit nào) → Pit(cell còn lại)
        R4: Stench(x,y) ∧ (tất cả adjacent trừ 1 đều ¬Wumpus) ∧ (chưa có wumpus nào) → Wumpus(cell còn lại)
        
        Logic chính xác: Chỉ khi CHẮC CHẮN rằng phải có pit/wumpus và chỉ còn 1 chỗ có thể
        """
        new_inferences = []
        
        for clause in KB:
            # Rule R3 cho Pit
            if clause.startswith('Breeze(') and '<->' not in clause:
                parsed = self.parse_fact(clause)
                if parsed:
                    _, x, y, _ = parsed
                    adjacent = self.get_adjacent_cells(x, y)
                    
                    # Phân loại adjacent cells
                    confirmed_no_pit = []  # Cells chắc chắn không có pit
                    confirmed_has_pit = []  # Cells chắc chắn có pit
                    unknown_cells = []     # Cells chưa biết
                    
                    for nx, ny in adjacent:
                        pit_status = self.get_fact('Pit', nx, ny)
                        if pit_status is True:
                            confirmed_has_pit.append((nx, ny))
                        elif pit_status is False:
                            confirmed_no_pit.append((nx, ny))
                        else:
                            unknown_cells.append((nx, ny))
                    
                    # Logic: Nếu có breeze nhưng chưa tìm thấy pit nào,
                    # và chỉ còn đúng 1 cell chưa biết
                    # → Cell đó PHẢI có pit
                    if (len(confirmed_has_pit) == 0 and  # Chưa tìm thấy pit nào
                        len(unknown_cells) == 1):       # Chỉ còn 1 cell chưa biết
                        
                        nx, ny = unknown_cells[0]
                        self.set_fact('Pit', nx, ny, True)
                        new_inferences.append(f"Pit({nx},{ny}) [từ R3: Breeze({x},{y}) và chỉ còn 1 cell có thể]")
            
            # Rule R4 cho Wumpus
            elif clause.startswith('Stench(') and '<->' not in clause:
                parsed = self.parse_fact(clause)
                if parsed:
                    _, x, y, _ = parsed
                    adjacent = self.get_adjacent_cells(x, y)
                    
                    confirmed_no_wumpus = []
                    confirmed_has_wumpus = []
                    unknown_cells = []
                    
                    for nx, ny in adjacent:
                        wumpus_status = self.get_fact('Wumpus', nx, ny)
                        if wumpus_status is True:
                            confirmed_has_wumpus.append((nx, ny))
                        elif wumpus_status is False:
                            confirmed_no_wumpus.append((nx, ny))
                        else:
                            unknown_cells.append((nx, ny))
                    
                    # Tương tự cho wumpus
                    if (len(confirmed_has_wumpus) == 0 and
                        len(unknown_cells) == 1):
                        
                        nx, ny = unknown_cells[0]
                        self.set_fact('Wumpus', nx, ny, True)
                        new_inferences.append(f"Wumpus({nx},{ny}) [từ R4: Stench({x},{y}) và chỉ còn 1 cell có thể]")
        
        return new_inferences
    
    def apply_rule_R5_R6_R7(self):
        """
        R5: ¬Pit(x,y) ∧ ¬Wumpus(x,y) → Safe(x,y)
        R6: Pit(x,y) → Dangerous(x,y)
        R7: Wumpus(x,y) → Dangerous(x,y)
        """
        new_inferences = []
        
        for y in range(self.N):
            for x in range(self.N):
                pit_status = self.get_fact('Pit', x, y)
                wumpus_status = self.get_fact('Wumpus', x, y)
                safe_status = self.get_fact('Safe', x, y)
                dangerous_status = self.get_fact('Dangerous', x, y)
                
                # R5: Safe nếu không có pit và không có wumpus
                if (pit_status is False and wumpus_status is False and 
                    safe_status is None):
                    self.set_fact('Safe', x, y, True)
                    new_inferences.append(f"Safe({x},{y}) [từ R5: !Pit ∧ !Wumpus]")
                
                # R6: Dangerous nếu có pit
                elif pit_status is True and dangerous_status is None:
                    self.set_fact('Dangerous', x, y, True)
                    new_inferences.append(f"Dangerous({x},{y}) [từ R6: Pit]")
                
                # R7: Dangerous nếu có wumpus
                elif wumpus_status is True and dangerous_status is None:
                    self.set_fact('Dangerous', x, y, True)
                    new_inferences.append(f"Dangerous({x},{y}) [từ R7: Wumpus]")
        
        return new_inferences
    
    def load_KB_facts(self, KB):
        """Load các facts từ KB vào inference engine"""
        for clause in KB:
            # Chỉ xử lý các facts đơn giản, không phải biconditionals
            if '<->' not in clause and 'OR' not in clause and 'AND' not in clause:
                parsed = self.parse_fact(clause)
                if parsed:
                    predicate, x, y, is_negative = parsed
                    if predicate in ['Breeze', 'Stench', 'Pit', 'Wumpus', 'Safe', 'Dangerous', 'Visited']:
                        self.set_fact(predicate, x, y, not is_negative)
    
    def forward_chaining(self, KB):
        """Forward Chaining với logic chính xác và debug output"""
        # Load facts từ KB
        self.load_KB_facts(KB)
        
        all_inferences = []
        max_iterations = 20
        
        for iteration in range(max_iterations):
            iteration_inferences = []
            old_facts_count = len([f for f in self.known_facts.values() if f is not None])
            
            # Áp dụng các rules theo thứ tự logic
            # 1. Trước tiên áp dụng R1, R2 (negation rules) - chắc chắn nhất
            new_R1_R2 = self.apply_rule_R1_R2(KB)
            iteration_inferences.extend(new_R1_R2)
            
            # 2. Sau đó áp dụng R3, R4 (positive inference) - cần thận trọng hơn
            new_R3_R4 = self.apply_rule_R3_R4(KB)
            iteration_inferences.extend(new_R3_R4)
            
            # 3. Cuối cùng áp dụng R5, R6, R7 (safety rules)
            new_R5_R6_R7 = self.apply_rule_R5_R6_R7()
            iteration_inferences.extend(new_R5_R6_R7)
            
            # Kiểm tra convergence
            new_facts_count = len([f for f in self.known_facts.values() if f is not None])
            if new_facts_count == old_facts_count and not iteration_inferences:
                break  # Không có thay đổi, đã converge
            
            all_inferences.extend(iteration_inferences)
        
        return all_inferences
    
    def infer_cell_status(self, x, y, KB):
        """Suy luận trạng thái của cell (x,y)"""
        # Reset
        self.known_facts.clear()
        
        # Chạy forward chaining
        inferences = self.forward_chaining(KB)
        
        # Kiểm tra trạng thái
        safe_status = self.get_fact('Safe', x, y)
        dangerous_status = self.get_fact('Dangerous', x, y)
        pit_status = self.get_fact('Pit', x, y)
        wumpus_status = self.get_fact('Wumpus', x, y)
        
        # Trả về kết quả với thông tin debug
        if dangerous_status is True or pit_status is True or wumpus_status is True:
            return 'dangerous', inferences
        elif safe_status is True or (pit_status is False and wumpus_status is False):
            return 'safe', inferences
        else:
            return 'uncertain', inferences

# ===== KB update =====
def remove_old_stench_from_KB(KB):
    """
    Remove old stench facts from the knowledge base.
    """
    # Xoá các facts về Stench và Wumpus cũ
    for clause in list(KB):
        if "Stench" in clause:
            KB.remove(clause)

# ===== FIXED: KB update =====
def update_KB(x, y, percept, KB, N):
    """Cập nhật KB với percepts mới"""
    # Thêm visited fact
    # KB.add(f"Visited({x},{y})")
    
    # Xử lý Breeze
    if percept["breeze"]:
        KB.add(f"Breeze({x},{y})")
        # Tạo biconditional cho breeze (có thể bỏ qua vì phức tạp)
        adj = [(x+dx, y+dy) for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)] 
               if wumpus_world.in_bounds(x+dx, y+dy)]
        if adj:  # Chỉ thêm nếu có adjacent cells
            pits = " OR ".join([f"Pit({i},{j})" for i,j in adj])
            KB.add(f"Breeze({x},{y}) <-> ({pits})")
    else:
        KB.add(f"!Breeze({x},{y})")

    # Xử lý Stench
    if percept["stench"]:
        KB.add(f"Stench({x},{y})")
        adj = [(x+dx, y+dy) for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)] 
               if wumpus_world.in_bounds(x+dx, y+dy)]
        if adj:
            wumpuses = " OR ".join([f"Wumpus({i},{j})" for i,j in adj])
            KB.add(f"Stench({x},{y}) <-> ({wumpuses})")
    else:
        KB.add(f"!Stench({x},{y})")

    # Xử lý Glitter
    if percept["glitter"]:
        KB.add(f"Glitter({x},{y})")
        KB.add(f"Gold({x},{y})")

def update_KB_after_shot(agent: Agent.Agent, KB, N):
    dx, dy = 0, 0
    direction = agent.direction
    if direction == 'N':
        dy = 1
    elif direction == 'S':
        dy = -1
    elif direction == 'E':
        dx = 1
    elif direction == 'W':
        dx = -1

    x, y = agent.pos
    x += dx
    y += dy
    while 0 <= x < N and 0 <= y < N:
        KB.add(f"!Wumpus({x},{y})")
        x += dx
        y += dy

# ===== ENHANCED: IN KB VÀ INFERENCE RESULTS =====
def print_KB_with_inference(KB, x, y, percept, debug_info):
    # os.system('cls' if os.name == 'nt' else 'clear')
    print(f"🤖 Agent at ({x}, {y}) | Percepts: {percept}")
    # print("\n📚 Knowledge Base (simplified):")
    
    # # Chỉ in các facts quan trọng
    # simple_facts = [clause for clause in KB if '<->' not in clause and 'OR' not in clause]
    # for clause in sorted(simple_facts):
    #     print("  ", clause)

    print("📚 Knowledge Base:")
    for clause in sorted(KB):
        print("  ", clause)
    print("-" * 60)
    
    print("\n🧠 Inference Results:")
    for row in range(N-1, -1, -1):
        line = f"Row {row}: "
        for col in range(N):
            cell = world[row][col]
            # if cell["visited"]:
            #     line += "[V] "
            if cell["safe"]:
                line += "[S] "
            elif cell["dangerous"]: 
                line += "[D] "
            else:  # uncertain
                line += "[?] "
        print(line)
    
    print("\nLegend: [V]=Visited, [S]=Safe, [D]=Dangerous, [?]=Uncertain")
    
    # In một vài inferences quan trọng
    if debug_info:
        print("\n🔍 Recent Inferences:")
        count = 0
        for (cx, cy), (status, inferences) in debug_info.items():
            if inferences and count < 3:  # Chỉ in 3 inferences đầu
                print(f"  Cell ({cx},{cy}): {status}")
                for inf in inferences[:2]:  # Chỉ in 2 inferences đầu tiên
                    print(f"    - {inf}")
                count += 1
    
    print("-" * 60)