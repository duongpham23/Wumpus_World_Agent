import wumpus_world
import wumpus_inference as inference
import time
import pygame
import agent as Agent

# Pygame constants
NUM_WUMPUS = wumpus_world.NUM_WUMPUS
NUM_PITS = wumpus_world.NUM_PITS
N = wumpus_world.N
KB = inference.KB
DELAY = 1  # Delay giữa các bước

SIDEBAR_WIDTH = 450
CELL_SIZE = 70
SCREEN_WIDTH = N * CELL_SIZE + SIDEBAR_WIDTH
SCREEN_HEIGHT = N * CELL_SIZE
SIDEBAR_BG = (30, 30, 30)
TEXT_COLOR = (230, 230, 230)
TITLE_COLOR = (255, 215, 0)

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
def draw_world_with_inference(screen, world, agent_x, agent_y, font, direction, shoot):
    screen.fill(BLACK)
    for y in range(N):
        for x in range(N):
            rect = pygame.Rect(x * CELL_SIZE, (N - 1 - y) * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            cell = world[y][x]
            
            # Chọn màu dựa trên trạng thái inference
            # if cell["visited"]:
            #     color = DARK_GRAY
            if cell["safe"]:
                color = GREEN
            elif cell["dangerous"]:
                color = RED
            elif cell["uncertain"]:
                color = ORANGE
            else:
                color = GRAY
                
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)

           # Vẽ agent
            if (x, y) == (agent_x, agent_y):
                arrow = font.render("-->", True, PURPLE)
                if direction == 'N':
                    #text = font.render("up", True, PURPLE)
                    arrow = pygame.transform.rotate(arrow, 90)
                elif direction == 'S':
                    #text = font.render("down", True, PURPLE)
                    arrow = pygame.transform.rotate(arrow, -90)
                elif direction == 'E':
                    #text = font.render("right", True, PURPLE)
                    arrow = pygame.transform.rotate(arrow, 0)
                elif direction == 'W':
                    #text = font.render("left", True, PURPLE)
                    arrow = pygame.transform.rotate(arrow, 180)
                screen.blit(arrow, (rect.x + 15, rect.y + 10))

            # Vẽ features thực tế (chỉ cho debug - thường ẩn)
            elif cell["glitter"] and cell["wumpus"]:
                text = font.render("W, G", True, YELLOW)
                screen.blit(text, (rect.x + 15, rect.y + 10))
            elif cell["wumpus"]:
                text = font.render("W", True, BLUE)
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

def draw_sidebar(agent: Agent.Agent,screen, font_title, font_text, stats, direction, percept):
    # Sidebar rect
    sidebar_rect = pygame.Rect(N * CELL_SIZE, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, SIDEBAR_BG, sidebar_rect)

    padding = 12
    x = sidebar_rect.x + padding
    y = padding

    # Title
    title_surf = font_title.render("GAME STATS", True, TITLE_COLOR)
    screen.blit(title_surf, (x, y))
    y += font_title.get_linesize() + 8

    # Lines to display (thêm/bớt tuỳ bạn)
    kb_lists = list(KB)
    kb_lists = kb_lists[-8:]
    percepts_str = ", ".join([k for k, v in percept.items() if v]) or "None"
    lines = [
        f"  - Score: {stats['score']}",
        f"  - Gold: {'Yes' if stats['gold'] else 'No'}",
        f"  - Arrow: {agent.num_arrow}",
        f"  - Steps: {stats['steps']}",
        f"  - Agent pos: {stats['pos']}",
        f"  - Direction: {direction}",
        f"  - Percepts: {percepts_str}",
        "",
        f"  - Visited: {stats['visited_count']}",
        f"  - Safe: {stats['safe_count']}",
        f"  - Uncertain: {stats['uncertain_count']}",
        f"  - Dangerous: {stats['dangerous_count']}",
        f"  - KB / World summary:",
    ] + [str(item) for item in kb_lists]

    for line in lines:
        surf = font_text.render(line, True, TEXT_COLOR)
        screen.blit(surf, (x, y))
        y += font_text.get_linesize() + 6


# ===== Simulation =====
def simulate_agent(world, mode="standard"):
    import solver
    import state

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Wumpus World with Inference Engine")
    font = pygame.font.Font(None, 36)
    font_title = pygame.font.Font(None, 28)
    font_text = pygame.font.Font(None, 24)

    agent = Agent.Agent((0, 0), 'E')
    running = True
    path = []
    cnt = 0
    next_goal = None
    shoot = False

    score_move = -1
    score_gold = 100
    score = 0
    steps = 0
    prev_pos = (0, 0)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not running: break

        x, y = agent.pos
        direction = agent.direction

        world[y][x]["visited"] = True

        # Nếu thấy rủi ro, cụ thể là thấy stench
        # Nếu mới bắn ở hướng này rồi thì không bắn nữa
        if world[y][x]["stench"]:
            print("🚨 Danger! Stench detected.")
            # For advance
            # Xoá hết ký ức về stench
            if mode == "advance":
                inference.remove_old_stench_from_KB(KB)
                path = []

            if not shoot and agent.num_arrow > 0:
                # Đập mặt vô tường thì không bắn
                if not agent.facing_to_wall():
                    path.insert(0, ((x, y), direction, True)) # path = [pos, direction, shoot]

        percept = {
            "breeze": world[y][x]["breeze"],
            "stench": world[y][x]["stench"],
            "glitter": world[y][x]["glitter"]
        }

        # Cập nhật KB
        inference.update_KB(x, y, percept, KB, N)
        
        # Chạy inference
        debug_info = wumpus_world.update_world_with_inference(world, KB, prev_pos, (x, y), mode)

        # In thông tin với debug
        inference.print_KB_with_inference(KB, x, y, percept, debug_info)

        # Vẽ world với inference visualization
        draw_world_with_inference(screen, world, x, y, font, direction, shoot)

        # Tạo stats từ world (đảm bảo các cell có keys 'visited','safe','uncertain','dangerous')
        visited_count   = sum(1 for row in world for cell in row if cell.get("visited"))
        safe_count      = sum(1 for row in world for cell in row if cell.get("safe"))
        uncertain_count = sum(1 for row in world for cell in row if cell.get("uncertain"))
        dangerous_count = sum(1 for row in world for cell in row if cell.get("dangerous"))

        stats = {
            "score": score,
            "gold": agent.gold_collected,
            "steps": steps,
            "pos": (x, y),
            "visited_count": visited_count,
            "safe_count": safe_count,
            "uncertain_count": uncertain_count,
            "dangerous_count": dangerous_count
        }
        
        # Vẽ sidebar (sau draw_world_with_inference)
        draw_sidebar(agent, screen, font_title, font_text, stats, direction, percept)

        pygame.display.flip()

        # Kiểm tra agent có bị wumpus ăn không
        if world[y][x]["wumpus"]:
            msg = f"🚨 Agent eaten by Wumpus at ({x}, {y})! Game Over."
            print(msg)
            # Hiển thị lên màn hình bằng pygame
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            font_end = pygame.font.Font(None, 60)
            text_surf = font_end.render(msg, True, (255, 0, 0))
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(text_surf, text_rect)
            pygame.display.flip()
            time.sleep(2)
            break

        # Nếu mục đích là đi về
        if next_goal is not None and next_goal == (0, 0):
            # Nếu có vàng
            if agent.gold_collected:
                if (x, y) == (0, 0):
                    print("Climbing out of the dungeon with gold!")
                    break
            else:
                # Tìm lại coi còn ô safe nào chưa khám phá sao khi đi về không, xảy ra khi có wumpus chặn đường và đã xử được con wumpus đó
                next_goal = solver.choose_next_goal(state.State(agent), world)
                if next_goal != (0, 0):
                    path = solver.a_star(state.State(agent), next_goal)
                elif (x, y) == (0, 0):
                    print("Climbing out of the dungeon!")
                    break

        if path == []:
            next_goal = solver.choose_next_goal(state.State(agent), world)
            path = solver.a_star(state.State(agent), next_goal)
            if path == []:
                continue

        time.sleep(DELAY)
        next_step = path.pop(0)
        if len(next_step) > 2:
            shoot = next_step[2]
        else:
            shoot = False

        # Action
        # Chỉ thực hiện 1 trong 3 action sau:
        if shoot:
            if agent.shoot_arrow():
                percept = {
                    "breeze": world[y][x]["breeze"],
                    "stench": world[y][x]["stench"],
                    "glitter": world[y][x]["glitter"]
                }

                # Cập nhật KB
                inference.update_KB(x, y, percept, KB, N)

                # Cập nhập KB sau khi bắn
                inference.update_KB_after_shot(agent, KB, N)
                
                # BỔ SUNG: Chạy inference engine
                wumpus_world.update_world_with_inference(world, KB, prev_pos, (x, y), advance_mode)

                next_goal = solver.choose_next_goal(state.State(agent), world)
                path = solver.a_star(state.State(agent), next_goal)
        elif world[y][x]["glitter"]:
            agent.grab_gold()
            print("💰 Collected gold! Climbing out of the dungeon...")
            next_goal = (0, 0)  # Đặt mục tiêu là về đích
            path = solver.a_star(state.State(agent), next_goal)
            world[y][x]["glitter"] = False
        else:
            # Cập nhật trạng thái
            new_x = next_step[0][0]
            new_y = next_step[0][1]

            if (new_x, new_y) != (x, y):
                prev_pos = (x, y)

            x = new_x
            y = new_y

            direction = next_step[1]
            agent.update((x, y), direction)

            # cập nhập điểm
            steps += 1
            score += score_move

        # Nếu đạp trúng wumpus, die
        if world[y][x]["wumpus"]:
            msg = f"Agent stepped on Wumpus at ({x}, {y})! Game Over."
            print(msg)

            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            font_end = pygame.font.Font(None, 60)
            text_surf = font_end.render(msg, True, (255, 0, 0))
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(text_surf, text_rect)
            pygame.display.flip()
            # Chờ người dùng đóng
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        running = False
                        break
                if not running:
                    break

            break

        # advance
        if mode == "advance":
            cnt += 1
            if cnt % 5 == 0:
                wumpus_world.wumpus_move()

    print("Simulation ended.")
    time.sleep(3)  # Chờ trước khi đóng
    pygame.quit()