import matplotlib.pyplot as plt
import numpy as np

def parse_grid(file_path):
    grid_data = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        # Skip the first two lines (metadata)
        for line in lines[2:]:
            parts = line.strip().split(',')
            # Ensure the line has enough parts and valid numeric data
            if len(parts) < 5 or not parts[3].isdigit() or not parts[4].isdigit():
                continue  # Skip invalid lines
            x, y = int(parts[3]), int(parts[4])
            cell_type = parts[1]
            # Assign a numeric value based on the cell type
            if cell_type == "Obstacle":
                value = -1  # Obstacles
            elif cell_type == "Travel":
                value = 0  # Traversable cells
            elif cell_type == "Eject":
                value = 1  # Eject points
            elif cell_type == "Induct":
                value = 2  # Induct points
            else:
                value = 0  # Default for unknown types
            # Ensure the grid is large enough
            while len(grid_data) <= y:
                grid_data.append([])
            while len(grid_data[y]) <= x:
                grid_data[y].append(0)
            grid_data[y][x] = value
    return grid_data

def visualize_grid(grid_data):
    # Convert to a numpy array for visualization
    grid_array = np.array(grid_data)
    plt.figure(figsize=(10, 10))
    plt.imshow(grid_array, cmap="viridis", origin="upper")
    plt.colorbar(label="Cell Type")
    plt.title("Grid Visualization")
    plt.xlabel("X-axis")
    plt.ylabel("Y-axis")
    plt.show()

if __name__ == "__main__":
    file_path = "maps/sorting_map.grid"
    grid_data = parse_grid(file_path)
    visualize_grid(grid_data)