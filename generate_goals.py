import argparse
import random
import json
import sys

def parse_map_for_traversable_cells(map_file_path):
    """
    Parses a standard .map file to find all traversable cells.
    Traversable cells are assumed to be marked with a '.' character.

    Args:
        map_file_path (str): The full path to the map file.

    Returns:
        list: A list of (x, y) tuples representing valid, non-obstacle coordinates.
    
    Raises:
        ValueError: If the 'map' keyword is not found in the file.
    """
    traversable_cells = []
    try:
        with open(map_file_path, 'r') as f:
            lines = f.readlines()

        # Find the line where the actual map grid begins
        map_start_index = -1
        for i, line in enumerate(lines):
            if line.strip().lower() == 'map':
                map_start_index = i + 1
                break
        
        if map_start_index == -1:
            raise ValueError("Map definition ('map' keyword) not found in file.")

        # Iterate over the grid portion of the map
        map_grid_lines = lines[map_start_index:]
        for y, line in enumerate(map_grid_lines):
            for x, char in enumerate(line.strip()):
                if char == '.':
                    traversable_cells.append((x, y))
                    
    except FileNotFoundError:
        print(f"Error: Map file not found at '{map_file_path}'", file=sys.stderr)
        sys.exit(1)
        
    return traversable_cells

def generate_random_goals(traversable_cells, num_goals):
    """
    Randomly selects a specified number of unique goals from the list of
    traversable cells.

    Args:
        traversable_cells (list): A list of (x, y) tuples.
        num_goals (int): The number of unique goals to generate.

    Returns:
        list: A list of (x, y) tuples selected as goals.
    
    Raises:
        ValueError: If the requested number of goals exceeds the number of
                    available traversable cells.
    """
    if num_goals > len(traversable_cells):
        raise ValueError(
            f"Cannot generate {num_goals} goals. "
            f"Only {len(traversable_cells)} traversable cells are available in the map."
        )
        
    return random.sample(traversable_cells, num_goals)

def main():
    """
    Main execution function. Parses command-line arguments, generates goals,
    and prints them to stdout or a file.
    """
    parser = argparse.ArgumentParser(
        description="Generate random, valid goal positions from a map file for the AgentRuntimeManager.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-m", "--map", 
        required=True, 
        help="Path to the map file (e.g., 'maps/sorting_map.grid')."
    )
    parser.add_argument(
        "-n", "--num-goals", 
        type=int, 
        required=True, 
        help="The number of unique goal positions to generate."
    )
    parser.add_argument(
        "-o", "--output", 
        help="Optional. Path to an output JSON file to save the goals. \nIf not provided, goals will be printed to the console."
    )

    args = parser.parse_args()

    try:
        print(f"Parsing map file: {args.map}...")
        valid_cells = parse_map_for_traversable_cells(args.map)
        print(f"Found {len(valid_cells)} traversable cells.")

        print(f"Generating {args.num_goals} random goals...")
        goals = generate_random_goals(valid_cells, args.num_goals)
        
        output_data = {"goals": goals}

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=4)
            print(f"Successfully saved {len(goals)} goals to {args.output}")
        else:
            # Print to console
            print(json.dumps(output_data, indent=4))

    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
