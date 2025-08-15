import wumpus_graphics as graphics
import wumpus_world

world = wumpus_world.world

NUM_WUMPUS = wumpus_world.NUM_WUMPUS
PIT_PROB = wumpus_world.PIT_PROB
MODE = wumpus_world.MODE

# ===== Main =====
if __name__ == "__main__":
    print("🎮 Initializing Wumpus World with Inference Engine...")
    wumpus_world.place_feature("wumpus", count=2)
    wumpus_world.place_feature("pit", pit_prob=0.1)
    wumpus_world.place_feature("glitter", count=1)
    print(f"📍 Placed {NUM_WUMPUS} Wumpuses and {PIT_PROB} Pits appear in cell")
    print("🚀 Starting simulation...")
    graphics.simulate_agent(world, True if MODE == "advance" else False)