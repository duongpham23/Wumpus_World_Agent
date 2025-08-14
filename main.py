import wumpus_graphics as graphics
import wumpus_world

world = wumpus_world.world

NUM_WUMPUS = wumpus_world.NUM_WUMPUS
NUM_PITS = wumpus_world.NUM_PITS
MODE = wumpus_world.MODE

# ===== Main =====
if __name__ == "__main__":
    print("🎮 Initializing Wumpus World with Inference Engine...")
    wumpus_world.place_feature("wumpus", 5)
    wumpus_world.place_feature("pit", NUM_PITS)
    wumpus_world.place_feature("glitter", 1)
    print(f"📍 Placed {NUM_WUMPUS} Wumpuses and {NUM_PITS} Pits")
    print("🚀 Starting simulation...")
    graphics.simulate_agent(world, MODE)