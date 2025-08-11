import wumpus_world
import wumpus_inference as inference
import time
import pygame

# Pygame constants
NUM_WUMPUS = wumpus_world.NUM_WUMPUS
NUM_PITS = wumpus_world.NUM_PITS
N = wumpus_world.N
KB = inference.KB
DELAY = 1  # Delay giữa các bước
CELL_SIZE = 70
SCREEN_WIDTH = N * CELL_SIZE
SCREEN_HEIGHT = N * CELL_SIZE
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
RED = (255, 0, 0) # Dangerous
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
YELLOW = (255, 255, 0)  # Gold cells
ORANGE = (255, 165, 0)  # Uncertain cells
GREEN = (0, 255, 0)  # Safe color

# ===== BỔ SUNG: Pygame draw với inference visualization =====
def draw_world_with_inference(screen, world, agent_x, agent_y, font, direction):
    screen.fill(BLACK)
    for y in range(N):
        for x in range(N):
            rect = pygame.Rect(x * CELL_SIZE, (N - 1 - y) * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            cell = world[y][x]
            
            # Chọn màu dựa trên trạng thái inference
            if cell["safe"]:
                color = GREEN
            elif cell["dangerous"]:
                color = RED
            elif cell["uncertain"]:
                color = ORANGE
            elif cell["visited"]:
                color = DARK_GRAY
            else:
                color = GRAY
                
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)

            # Vẽ agent
            if (x, y) == (agent_x, agent_y):
                if direction == 'N':
                    text = font.render("up", True, PURPLE)
                elif direction == 'S':
                    text = font.render("down", True, PURPLE)
                elif direction == 'E':
                    text = font.render("right", True, PURPLE)
                elif direction == 'W':
                    text = font.render("left", True, PURPLE)
                screen.blit(text, (rect.x + 15, rect.y + 10))

            # Vẽ features thực tế (chỉ cho debug - thường ẩn)
            elif cell["glitter"] and cell["wumpus"]:
                text = font.render("W, G", True, YELLOW)
                screen.blit(text, (rect.x + 15, rect.y + 10))
            elif cell["wumpus"]:
                text = font.render("W", True, RED)
                screen.blit(text, (rect.x + 15, rect.y + 10))
            elif cell["pit"]:
                text = font.render("P", True, BLACK)
                screen.blit(text, (rect.x + 15, rect.y + 10))
            elif cell["glitter"]:
                text = font.render("G", True, YELLOW)
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
    import solver
    import state

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Wumpus World with Inference Engine")
    font = pygame.font.Font(None, 36)

    x, y = 0, 0
    running = True
    path = []
    direction = 'E'  # Bắt đầu hướng Đông
    cnt = 0
    collect_gold = False
    next_goal = None
    wumpus_pos = []
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not running: break

        world[y][x]["visited"] = True

        percept = {
            "breeze": world[y][x]["breeze"],
            "stench": world[y][x]["stench"],
            "glitter": world[y][x]["glitter"]
        }
        
        # Cập nhật KB
        inference.update_KB(x, y, percept, KB, N)
        
        # BỔ SUNG: Chạy inference engine
        wumpus_world.update_world_with_inference(world, KB)
        
        # In thông tin
        inference.print_KB_with_inference(KB, x, y, percept)

        # Vẽ world với inference visualization
        draw_world_with_inference(screen, world, x, y, font, direction)

        # Kiểm tra agent có bị wumpus ăn không
        if (x, y) in wumpus_pos:
            print("🚨 Agent eaten by Wumpus! Game Over.")
            break

        pygame.display.flip()
        time.sleep(DELAY)

        if path != []:
            next_step = path.pop(0)

            # Cập nhật vị trí
            x = next_step[0][0]
            y = next_step[0][1]
            direction = next_step[1]

            # Nếu thấy rủi ro, cụ thể là thấy stench
            if world[y][x]["stench"]:
                print("🚨 Danger! Stench detected.")
                path = []  # Reset path nếu thấy stench
                continue  # Bỏ qua nếu thấy stench

            if world[y][x]["glitter"]:
                collect_gold = True
                print("💰 Collected gold! Climbing out of the dungeon...")
                path = solver.a_star(state.State((x, y), direction), state.State((0, 0)))
                world[y][x]["glitter"] = False

            # advance
            cnt += 1
            if cnt % 5 == 0:
                wumpus_pos = wumpus_world.wumpus_move()
                wumpus_world.place_feature("wumpus", NUM_WUMPUS, True)
        else:
            if (x, y) == (0, 0):
                if collect_gold:
                    print("Climbing out of the dungeon with gold!")
                    break
                elif next_goal is not None and next_goal == (0, 0):
                    print("Climbing out of the dungeon!")
                    break

            next_goal = solver.choose_next_goal(state.State((x, y), direction), world)
            path = solver.a_star(state.State((x, y), direction), state.State(next_goal))

    print("Simulation ended.")
    time.sleep(3)  # Chờ trước khi đóng
    pygame.quit()