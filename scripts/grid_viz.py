import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Load .map file
def load_map(map_path):
    with open(map_path, 'r') as f:
        lines = [line.strip() for line in f.readlines()]
    
    # First line is: height,width
    height, width = map(int, lines[0].split(','))

    # The grid starts from line 4 onwards
    grid_lines = lines[4:]

    # Confirm that the number of lines matches height
    assert len(grid_lines) == height, "Grid height does not match map file metadata"

    grid = []
    for line in grid_lines:
        row = [1 if char == '.' else 0 for char in line]
        grid.append(row)

    return np.array(grid), width


# Convert flat location ID to (x, y)
def id_to_xy(loc_id, width):
    return loc_id % width, loc_id // width

# Parse RHCR path file
def parse_paths(path_file, width):
    with open(path_file, 'r') as f:
        lines = f.readlines()
    num_agents = int(lines[0])
    all_paths = []

    for line in lines[1:num_agents+1]:
        path = []
        entries = line.strip().split(';')
        for entry in entries:
            if not entry: continue
            loc_id, _, _ = entry.split(',')
            x, y = id_to_xy(int(loc_id), width)
            path.append((x, y))
        all_paths.append(path)
    return all_paths

# Animate paths
def animate_paths(grid, agents_paths):
    fig, ax = plt.subplots()
    ax.set_xlim(0, grid.shape[1])
    ax.set_ylim(0, grid.shape[0])
    ax.set_xticks(np.arange(0, grid.shape[1]+1, 1))
    ax.set_yticks(np.arange(0, grid.shape[0]+1, 1))
    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.grid(True, color='gray', linestyle='-', linewidth=0.5)

    # Draw walls
    for y in range(grid.shape[0]):
        for x in range(grid.shape[1]):
            if grid[y, x] == 0:
                ax.add_patch(plt.Rectangle((x, y), 1, 1, color='black'))

    # Agent markers
    colors = plt.cm.get_cmap('tab20', len(agents_paths))
    markers = []
    for i, path in enumerate(agents_paths):
        x, y = path[0]
        marker, = ax.plot(x + 0.5, y + 0.5, 'o', markersize=8, color=colors(i))
        markers.append(marker)

    # Collision tracking
    collision_counter = [0]
    collision_frames = set()

    # Animation update
    def update(frame):
        positions = {}
        for i, path in enumerate(agents_paths):
            if frame < len(path):
                x, y = path[frame]
                pos = (x, y)
                if pos not in positions:
                    positions[pos] = [i]
                else:
                    positions[pos].append(i)

        # Count collisions
        for agents in positions.values():
            if len(agents) > 1 and frame not in collision_frames:
                collision_counter[0] += 1
                collision_frames.add(frame)

        # Move agents
        for i, path in enumerate(agents_paths):
            if frame < len(path):
                x, y = path[frame]
                offset = positions[(x, y)].index(i) * 0.1 if len(positions[(x, y)]) > 1 else 0
                markers[i].set_data(x + 0.5 + offset, y + 0.5 + offset)

        return markers

    max_frames = max(len(p) for p in agents_paths)
    ani = animation.FuncAnimation(fig, update, frames=max_frames, interval=500, blit=True)
    plt.show()

    print(f"Total number of collision frames: {collision_counter[0]}")


# === MAIN ===
if __name__ == "__main__":
    map_path = "maps/kiva.map"
    path_file = "paths.txt"
    grid, width = load_map(map_path)
    agents_paths = parse_paths(path_file, width)
    animate_paths(grid, agents_paths)
