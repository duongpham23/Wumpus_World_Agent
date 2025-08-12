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
def draw_world_with_inference(screen, world, agent_x, agent_y, font, direction, shoot):
    screen.fill(BLACK)
    for y in range(N):
        for x in range(N):
            rect = pygame.Rect(x * CELL_SIZE, (N - 1 - y) * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            cell = world[y][x]
            
            # Chọn màu dựa trên trạng thái inference
            if cell["visited"]:
                color = DARK_GRAY
            elif cell["safe"]:
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
                if shoot:
                    text = font.render("shoot", True, PURPLE)
                elif direction == 'N':
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

# ===== Simulation =====
def simulate_agent(world, advance_mode=False):
    import solver
    import state
    import agent as Agent

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Wumpus World with Inference Engine")
    font = pygame.font.Font(None, 36)

    agent = Agent.Agent((0, 0), 'E')
    running = True
    path = []
    cnt = 0
    collect_gold = False
    next_goal = None
    shoot = False
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
            if advance_mode:
                inference.remove_old_stench_from_KB(KB)
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
        debug_info = wumpus_world.update_world_with_inference(world, KB)
        
        # In thông tin với debug
        # inference.print_KB_with_inference(KB, x, y, percept, debug_info)

        # Vẽ world với inference visualization
        draw_world_with_inference(screen, world, x, y, font, direction, shoot)

        pygame.display.flip()

        # Kiểm tra agent có bị wumpus ăn không
        if world[y][x]["wumpus"]:
            print("🚨 Agent eaten by Wumpus! Game Over.")
            break

        # Nếu mục đích là đi về
        if next_goal is not None and next_goal == (0, 0):
            # Nếu có vàng
            if collect_gold:
                if (x, y) == (0, 0):
                    print("Climbing out of the dungeon with gold!")
                    break
            else:
                # Tìm lại coi còn ô safe nào chưa khám phá sao khi đi về không, xảy ra khi có wumpus chặn đường và đã xử được con wumpus đó
                next_goal = solver.choose_next_goal(state.State(agent), world)
                if next_goal != (0, 0):
                    path = solver.a_star(state.State(agent), next_goal)
                elif (x, y) == (0, 0):
                    # Nếu có con wumpus chặn đường, ná nó luôn
                    if world[y][x]["stench"]:
                        agent.turn_left()
                        if agent.facing_to_wall():
                            agent.turn_left()
                            agent.turn_left()
                        path.insert(0, ((x, y), agent.direction))
                    else:
                        print("Climbing out of the dungeon!")
                        break

        if path != []:
            time.sleep(DELAY)
            next_step = path.pop(0)
            if len(next_step) > 2:
                shoot = next_step[2]
            else:
                shoot = False

            # Action
            # Chỉ thực hiện 1 trong 3 action sau:
            if shoot:
                # For advance
                if agent.shoot_arrow():
                    percept = {
                        "breeze": world[y][x]["breeze"],
                        "stench": world[y][x]["stench"],
                        "glitter": world[y][x]["glitter"]
                    }

                    inference.update_KB_after_shot(agent, KB, N)

                    # Cập nhật KB
                    inference.update_KB(x, y, percept, KB, N)
                    
                    # BỔ SUNG: Chạy inference engine
                    wumpus_world.update_world_with_inference(world, KB)

                    next_goal = solver.choose_next_goal(state.State(agent), world)
                    path = solver.a_star(state.State(agent), next_goal)
            elif world[y][x]["glitter"]:
                collect_gold = agent.grab_gold()
                print("💰 Collected gold! Climbing out of the dungeon...")
                next_goal = (0, 0)  # Đặt mục tiêu là về đích
                path = solver.a_star(state.State(agent), next_goal)
                world[y][x]["glitter"] = False
            else:
                # Cập nhật trạng thái
                x = next_step[0][0]
                y = next_step[0][1]
                direction = next_step[1]
                agent.update((x, y), direction)

            # Nếu đạp trúng wumpus, die
            if world[y][x]["wumpus"]:
                print("🚨 Agent stepped on Wumpus! Game Over.")
                break

            # advance
            if advance_mode:
                cnt += 1
                if cnt % 5 == 0:
                    wumpus_world.wumpus_move()
        else:
            next_goal = solver.choose_next_goal(state.State(agent), world)
            path = solver.a_star(state.State(agent), next_goal)

    print("Simulation ended.")
    time.sleep(3)  # Chờ trước khi đóng
    pygame.quit()