# ===== TKINTER GUI CHỌN THÔNG SỐ =====
import tkinter as tk
from tkinter import ttk

def get_user_config():
    result = {}
    def submit():
        result['N'] = int(size_var.get())
        result['NUM_WUMPUS'] = int(wumpus_var.get())
        result['PIT_PROB'] = float(pit_var.get())
        result['mode_var'] = mode_var.get()
        result['agent'] = agent_var.get()
        result['map'] = map_var.get()
        root.destroy()

    root = tk.Tk()
    root.title("Chọn thông số Wumpus World")
    root.geometry("400x600")

    size_var = tk.StringVar(value="8")
    wumpus_var = tk.StringVar(value="2")
    pit_var = tk.StringVar(value="0.2")
    mode_var = tk.StringVar(value="advanced")
    agent_var = tk.StringVar(value="smart")
    map_var = tk.StringVar(value="random")

    font = ("Arial", 16)
    height = 10
    ttk.Label(root, text="Chọn thông số Wumpus World", font=font).pack(pady=10)
    ttk.Label(root, text="---------------------------o0o----------------------------", font=font).pack(pady=10)
    
    ttk.Label(root, text="Kích thước map (N * N):", font=font).pack()
    ttk.Combobox(root, textvariable=size_var, values=[str(i) for i in range(8, 13)], font=font, height=height).pack()

    ttk.Label(root, text="Số lượng Wumpus:", font=font).pack()
    ttk.Combobox(root, textvariable=wumpus_var, values=[str(i) for i in range(2, 5)], font=font, height=height).pack()

    ttk.Label(root, text="Xác suất pit:", font=font).pack()
    ttk.Combobox(root, textvariable=pit_var, values=["0.1", "0.2", "0.3", "0.4", "0.5"], font=font, height=height).pack()
    
    ttk.Label(root, text="Chế độ", font=font).pack()
    ttk.Combobox(root, textvariable=mode_var, values=["advanced", "standard"], font=font, height=height).pack()
    
    ttk.Label(root, text="Chọn agent", font=font).pack()
    ttk.Combobox(root, textvariable=agent_var, values=["smart", "basic"], font=font, height=height).pack()
    
    ttk.Label(root, text="Chọn map", font=font).pack(pady=10)
    ttk.Combobox(root, textvariable=map_var, values=["random", "map_fixed"], font=font, height=height).pack()

    ttk.Button(root, text="Khởi tạo trò chơi", command=submit, style="Big.TButton").pack(pady=15)

    style = ttk.Style()
    style.configure("Big.TButton", font=font, padding=10)

    root.mainloop()
    return result

user_config = get_user_config()
N = user_config['N']
NUM_WUMPUS = user_config['NUM_WUMPUS']
PIT_PROB = user_config['PIT_PROB']
NUM_PITS = round(PIT_PROB * (N * N - 1))
MODE = user_config['mode_var']
AGENT = user_config['agent']
MAP = user_config['map']
MAP = "testcase/" + MAP[:4] + str(N) + ".txt" if MAP != "random" else MAP
# ===== World init =====
world = [[{
    "pit": False,
    "wumpus": False,
    "breeze": False,
    "glitter": False,
    "stench": False,
    "visited": False,
    "safe": False,      # Inference result
    "dangerous": False, # Inference result
    "uncertain": True   # Inference result (default)
} for _ in range(N)] for _ in range(N)]

def in_bounds(x, y):
    return 0 <= x < N and 0 <= y < N

# ===== BỔ SUNG: CẬP NHẬT WORLD VỚI INFERENCE =====
# ===== FIXED: CẬP NHẬT WORLD VỚI INFERENCE =====
def update_world_with_inference(world, KB, cell_to_update: list, update_safe_cells: list):
    # Tạo inference engine instance
    import wumpus_inference as inference
    inference_engine = inference.InferenceEngine(N)
    """Cập nhật trạng thái inference cho tất cả các cells chưa được thăm"""
    debug_info = {}

    for y in range(N):
        for x in range(N):
            if not world[y][x]["visited"] or (x, y) in cell_to_update or (x, y) in update_safe_cells:
                status, inferences = inference_engine.infer_cell_status(x, y, KB)
                debug_info[(x,y)] = (status, inferences)

                # Reset trạng thái cũ
                world[y][x]["safe"] = False
                world[y][x]["dangerous"] = False
                world[y][x]["uncertain"] = False

                # Set trạng thái mới
                if (x, y) in update_safe_cells:
                    world[y][x]["safe"] = True
                    continue

                if status == 'safe':
                    world[y][x]["safe"] = True
                elif status == 'dangerous':
                    world[y][x]["dangerous"] = True
                else:
                    world[y][x]["uncertain"] = True

    world[0][0]["safe"] = True
    world[0][0]["uncertain"] = False

    return debug_info

import random
# ===== World setup =====
def load_world_from_file(filepath):
    print(f"📂 Loading world from {filepath}...")
    with open(filepath, 'r') as f:
        lines = [line.strip().split() for line in f if line.strip()]
    for y, row in enumerate(lines):
        for x, cell in enumerate(row):
            if cell == 'P':
                world[y][x]['pit'] = True
                # cập nhật breeze cho các ô kề
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx, ny = x+dx, y+dy
                    if in_bounds(nx, ny):
                        world[ny][nx]['breeze'] = True
            elif cell == 'W':
                world[y][x]['wumpus'] = True
                # cập nhật stench cho các ô kề
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx, ny = x+dx, y+dy
                    if in_bounds(nx, ny):
                        world[ny][nx]['stench'] = True
            elif cell == 'G':
                world[y][x]['glitter'] = True
            # '.' thì không cần làm gì

def place_feature(key, count=0, pit_prob=0):
    if key == "pit":
       for y in range(N):
           for x in range(N):
               if (x, y) == (0, 0):
                   continue
               if random.random() < pit_prob:
                   world[y][x]["pit"] = True
                   for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                       nx, ny = x + dx, y + dy
                       if in_bounds(nx, ny):
                           world[ny][nx]["breeze"] = True
    else:
        placed = 0
        while placed < count:
            x = random.randint(0, N - 1)
            y = random.randint(0, N - 1)
            if (x, y) == (0, 0):
                continue
            if not world[y][x]["wumpus"] and not world[y][x]["pit"]:
                if key == "glitter":
                    world[y][x]["glitter"] = True
                    break
                
                world[y][x][key] = True
                if (key != "glitter"):
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if in_bounds(nx, ny):
                            world[ny][nx]["stench"] = True
                placed += 1

def wumpus_update_stench():
    """
    Update Wumpus state
    """
    # Xoá stench cũ
    for y in range(N):
        for x in range(N):
            if world[y][x]["stench"]:
                world[y][x]["stench"] = False

    # Update stench mới
    for y in range(N):
        for x in range(N):
            if world[y][x]["wumpus"]:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if in_bounds(nx, ny):
                        world[ny][nx]["stench"] = True

def wumpus_move():
    """
    Randomly move Wumpus to a new position if it exists
    """
    # Tìm vị trí của Wumpus
    wumpus_pos = []
    for y in range(N):
        for x in range(N):
            if world[y][x]["wumpus"]:
                wumpus_pos.append((x, y))

    wumpus_new_pos = []
    for x, y in wumpus_pos:
        # Chọn ngẫu nhiên 1 hướng để đi
        world[y][x]["wumpus"] = False
        direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        new_x = x + direction[0]
        new_y = y + direction[1]
        if (new_x, new_y) != (0, 0) and in_bounds(new_x, new_y) and not world[new_y][new_x]["pit"] and not world[new_y][new_x]["wumpus"]:
            world[new_y][new_x]["wumpus"] = True
            wumpus_new_pos.append((new_x, new_y))
        else:
            # Nếu không di chuyển được, giữ nguyên vị trí cũ
            world[y][x]["wumpus"] = True
            wumpus_new_pos.append((x, y))

    wumpus_update_stench()