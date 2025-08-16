import wumpus_graphics as graphics
import wumpus_world

world = wumpus_world.world

NUM_WUMPUS = wumpus_world.NUM_WUMPUS
PIT_PROB = wumpus_world.PIT_PROB
ADVANCED_MODE = True if wumpus_world.MODE == "advanced" else False
SMART_AGENT = True if wumpus_world.AGENT == "smart" else False

# ===== Main =====
if __name__ == "__main__":
    print("🎮 Initializing Wumpus World with Inference Engine...")
    wumpus_world.place_feature("wumpus", count=NUM_WUMPUS)
    wumpus_world.place_feature("pit", pit_prob=PIT_PROB)
    wumpus_world.place_feature("glitter", count=1)
    print(f"📍 Placed {NUM_WUMPUS} Wumpuses and {PIT_PROB} Pits appear in cell")
    print("🚀 Starting simulation...")
    graphics.simulate_agent(world, ADVANCED_MODE, SMART_AGENT)