import sys

# --- Configuration ---
# Standard MovingAI characters
TRAVERSABLE_CHARS = {'.', 'G', 'W'} # Common traversable
OBSTACLE_CHARS = {'@', 'O', 'T'}       # Common obstacles

# You can extend this map if you have custom characters for specific types/stations
# For example, if 'E' in your .map file means "Eject" with station "10000"
# CHAR_TO_TYPE_STATION_MAP = {
#     'E': ("Eject", "10000")
# }
# For now, we'll only handle standard Obstacle/Travel based on above sets.
# If you need "Eject", you'll need to define how it's identified from the .map.
# Let's assume for the sake of getting close to your example, 'E' maps to Eject.
# And let's assume 'S' (Swamp) and 'W' (Water) are traversable with cost 1.
# The example shows (x=1, y=3) as Eject. If map_data[3][1] was 'E', this would work.

DEFAULT_TYPE_STATION_MAP = {
   # Default for traversable
   "__traversable__": ("Travel", "None"),
   # Default for obstacle
   "__obstacle__": ("Obstacle", "None"),
   # --- Add your custom character mappings here ---
        'r': ("Induct", "1000"),
        'S': ("Induct", "1000")
   #      'P': ("Pickup", "P123"),
}

# To match the example output's Eject cell, we need a way to specify it.
# If map_data[3][1] (row 3, col 1) has a unique character, say 'X',
# then we could add 'X': ("Eject", "10000") to DEFAULT_TYPE_STATION_MAP.
# Or, we can hardcode a coordinate-based override for this example.
# For this script, I'll show how to use a special character. Let's use 'E'.
# If you don't have 'E' in your map, then the Eject line won't be produced as in the example.
CUSTOM_CHAR_MAP = {
   'E': ("Eject", "10000"),
    'S': ("Induct", "1000") # As per example for cell (1,3)
}
# Merge custom chars into traversable/obstacle logic
# For simplicity, we'll assume custom types are "traversable" in principle,
# meaning they are nodes in the graph, not voids.
# Their specific interactions (weights) are handled by the type.

def parse_movingai_map(filepath):
   """Parses a MovingAI .map file."""
   map_data = []
   height = 0
   width = 0
   try:
       with open(filepath, 'r') as f:
           lines = [line.strip() for line in f.readlines()]
           
           if not lines[0].startswith("type"):
               raise ValueError("Missing 'type' line in map header.")
           # type_line = lines.pop(0) # e.g. "type octile" - often ignored

           height_line = next(line for line in lines if line.startswith("height"))
           height = int(height_line.split()[1])
           
           width_line = next(line for line in lines if line.startswith("width"))
           width = int(width_line.split()[1])
           
           map_keyword_index = -1
           for i, line in enumerate(lines):
               if line == "map":
                   map_keyword_index = i
                   break
           
           if map_keyword_index == -1:
               raise ValueError("Missing 'map' keyword in map file.")

           map_data_lines = lines[map_keyword_index+1 : map_keyword_index+1+height]
           
           if len(map_data_lines) != height:
               raise ValueError(f"Map data has {len(map_data_lines)} rows, expected {height}.")

           for r, line in enumerate(map_data_lines):
               if len(line) != width:
                   raise ValueError(f"Map row {r} has {len(line)} columns, expected {width}.")
               map_data.append(list(line))
               
   except FileNotFoundError:
       print(f"Error: File not found at {filepath}", file=sys.stderr)
       return None, 0, 0
   except Exception as e:
       print(f"Error parsing map file {filepath}: {e}", file=sys.stderr)
       return None, 0, 0
       
   return map_data, height, width

def convert_map_to_custom_format(map_data, height, width, output_filepath):
   """Converts parsed map data to the specified custom CSV-like format."""
   if not map_data:
       return

   output_lines = []
   output_lines.append("Grid size (x, y)")
   output_lines.append(f"{width},{height}")
   output_lines.append("id,type,station,x,y,weight_to_NORTH,weight_to_WEST,weight_to_SOUTH,weight_to_EAST,weight_for_WAIT")

   # Pre-calculate cell properties (is_obstacle) for easier neighbor checks
   is_obstacle_grid = [[False for _ in range(width)] for _ in range(height)]
   cell_types_stations = {} # Store (type, station) for each (x,y)

   for r_idx in range(height): # y
       for c_idx in range(width): # x
           char = map_data[r_idx][c_idx]
           
           # Check custom character map first
           if char in CUSTOM_CHAR_MAP:
               node_type, station = CUSTOM_CHAR_MAP[char]
               # Assume custom types are not obstacles unless explicitly defined as such
               # For weight calculation, we treat them as traversable spots.
               is_obstacle_grid[r_idx][c_idx] = False 
           elif char in OBSTACLE_CHARS:
               node_type, station = DEFAULT_TYPE_STATION_MAP["__obstacle__"]
               is_obstacle_grid[r_idx][c_idx] = True
           elif char in TRAVERSABLE_CHARS:
               node_type, station = DEFAULT_TYPE_STATION_MAP["__traversable__"]
               is_obstacle_grid[r_idx][c_idx] = False
           else:
               # Default for unknown characters: treat as obstacle
               print(f"Warning: Unknown character '{char}' at ({c_idx},{r_idx}). Treating as Obstacle.", file=sys.stderr)
               node_type, station = DEFAULT_TYPE_STATION_MAP["__obstacle__"]
               is_obstacle_grid[r_idx][c_idx] = True
           cell_types_stations[(c_idx, r_idx)] = (node_type, station)


   # Iterate column-major for ID generation
   for c_idx in range(width):    # x-coordinate
       for r_idx in range(height): # y-coordinate
           node_id = c_idx * height + r_idx
           
           current_char = map_data[r_idx][c_idx]
           node_type, station = cell_types_stations[(c_idx, r_idx)]
           current_is_obstacle = is_obstacle_grid[r_idx][c_idx]

           # --- Determine weights to neighbors ---
           # Default weight for traversable to traversable is 1
           # Default weight to obstacle or out-of-bounds is 'inf'
           # If current cell is an obstacle, all outgoing weights are 'inf'
           
           # Weight to NORTH (y-1)
           if current_is_obstacle or r_idx == 0 or is_obstacle_grid[r_idx-1][c_idx]:
               w_n = "inf"
           else:
               w_n = "1"

           # Weight to WEST (x-1)
           if current_is_obstacle or c_idx == 0 or is_obstacle_grid[r_idx][c_idx-1]:
               w_w = "inf"
           else:
               w_w = "1"

           # Weight to SOUTH (y+1)
           if current_is_obstacle or r_idx == height - 1 or is_obstacle_grid[r_idx+1][c_idx]:
               w_s = "inf"
           else:
               w_s = "1"

           # Weight to EAST (x+1)
           if current_is_obstacle or c_idx == width - 1 or is_obstacle_grid[r_idx][c_idx+1]:
               w_e = "inf"
           else:
               w_e = "1"
           
           weight_for_wait = "1" # As per example

           output_lines.append(
               f"{node_id},{node_type},{station},{c_idx},{r_idx},"
               f"{w_n},{w_w},{w_s},{w_e},{weight_for_wait}"
           )
           
   try:
       with open(output_filepath, 'w') as f:
           for line in output_lines:
               f.write(line + "\n")
       print(f"Successfully converted map to {output_filepath}")
   except IOError:
       print(f"Error: Could not write to output file {output_filepath}", file=sys.stderr)


if __name__ == "__main__":
   if len(sys.argv) != 3:
       print("Usage: python convert_map.py <input_map_file.map> <output_custom_file.txt>")
       sys.exit(1)

   input_file = sys.argv[1]
   output_file = sys.argv[2]

   # --- Example of how you might define CHAR_TO_TYPE_STATION_MAP ---
   # This would be better loaded from a config file or passed as arguments
   # if you have many special types.
   # For the 'Eject' in the example (id=40, x=1, y=3), if your .map file
   # has a special character like 'E' at map_data[3][1], this map would handle it:
   # CUSTOM_CHAR_MAP['E'] = ("Eject", "10000") # Already defined globally for demo

   # Create a dummy .map file for testing, matching the example's implied structure somewhat
   # for the Eject cell. We need height 37, width 77 for the IDs to match.
   # Let's create a small one first for easier debugging.
   # If you want to test the exact example (id=40 for Eject at x=1, y=3)
   # you'll need a map that is at least 4 rows and 2 columns.
   # And the character map_data[3][1] should be 'E' (based on CUSTOM_CHAR_MAP)
   
   # --- Create a dummy .map file for testing ---
   # To make the script runnable and testable with the "Eject" example,
   # let's assume the input .map might contain an 'E'
   dummy_map_content = """type octile
height 4
width 5
map
.S.T.
.@.E.
G.W..
...O.
"""
   # In this dummy map:
   # (0,0) '.' -> id 0
   # (0,1) '@' -> id 1
   # (0,2) 'G' -> id 2
   # (0,3) '.' -> id 3
   # (1,0) 'S' -> id 4 (x=1, y=0 -> 1*4+0=4)
   # (1,1) '.' -> id 5
   # (1,2) '.' -> id 6
   # (1,3) '.' -> id 7
   # (3,1) 'E' -> id 13 (x=3, y=1 -> 3*4+1=13) -> Eject, 10000 (height is 4 here)

   # If we use the height/width from the *example output* (77,37) for ID calculation:
   # (x=1, y=3) -> id = 1 * 37 + 3 = 40.
   # So, if our input map had map_data[3][1] = 'E', height=37, width=77,
   # it would produce the "Eject" line.
   
   # For the script to run directly:
   if input_file == "maps/kiva.map":
       print("Using kiva.map for testing...")
       with open("kiva.map", "w") as f:
           f.write(dummy_map_content)
       # Modify CUSTOM_CHAR_MAP for this dummy map if needed
       # CUSTOM_CHAR_MAP['E'] = ("Eject", "10000") # Already set

   map_grid, h, w = parse_movingai_map(input_file)
   if map_grid:
       convert_map_to_custom_format(map_grid, h, w, output_file)
   else:
       print("Failed to parse the input map. Exiting.")
       sys.exit(1)