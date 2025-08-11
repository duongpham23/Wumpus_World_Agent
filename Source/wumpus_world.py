# ===== Constants =====
N = 8
NUM_WUMPUS = 2
NUM_PITS = 2
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
def update_world_with_inference(world, KB):
    # Tạo inference engine instance
    import wumpus_inference as inference
    inference_engine = inference.InferenceEngine(N)
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
                world[0][0]["safe"] = True
                if status == 'safe':
                    world[y][x]["safe"] = True
                elif status == 'dangerous':
                    world[y][x]["dangerous"] = True
                else:
                    world[y][x]["uncertain"] = True

import random
# ===== World setup =====
def place_feature(key, count, ingame=False):
    
    #Xoa mui wumpus cu
    if ingame and key == "wumpus":
        for x in range(N):
            for y in range(N):
                if world[y][x]["stench"]:
                    world[y][x]["stench"] = False

        #Cap nhap mui wumpus moi
        for x in range(N):
            for y in range(N):
                if world[y][x]["wumpus"]:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if in_bounds(nx, ny):
                            world[ny][nx]["stench"] = True
        return

    placed = 0
    while placed < count:
        x = random.randint(0, N - 1)
        y = random.randint(0, N - 1)
        if (x, y) == (0, 0):
            continue
        if not world[y][x]["wumpus"] and not world[y][x]["pit"]:
            world[y][x][key] = True
            if (key != "glitter"):
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if in_bounds(nx, ny):
                        if key == "pit":
                            world[ny][nx]["breeze"] = True
                        elif key == "wumpus":
                            world[ny][nx]["stench"] = True
            placed += 1

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

    for x, y in wumpus_pos:
        # Chọn ngẫu nhiên 1 hướng để đi
        world[y][x]["wumpus"] = False
        direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        new_x = x + direction[0]
        new_y = y + direction[1]
        if (new_x, new_y) != (0, 0) and in_bounds(new_x, new_y) and not world[new_y][new_x]["pit"] and not world[new_y][new_x]["wumpus"]:
            world[new_y][new_x]["wumpus"] = True
        else:
            # Nếu không di chuyển được, giữ nguyên vị trí cũ
            world[y][x]["wumpus"] = True