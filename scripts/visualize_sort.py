import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.colors as mcolors
import numpy as np
import os

# --- Configuration ---
MAP_FILE = 'sorting_map.grid'
TASKS_FILE = 'centre_10/tasks.txt' # Adjusted path for potential subfolder
# If tasks.txt is in the same directory as the script, use:
# TASKS_FILE = 'centre_10_tasks.txt' # Assuming you rename or place it accordingly

# --- 1. Parse Map File ---
def parse_map(filepath):
    """Parses the .grid file."""
    nodes = {}
    grid_dim = (0, 0)
    with open(filepath, 'r') as f:
        lines = f.readlines()
        grid_dim_str = lines[0].strip().split('(')[1].split(')')[0].split(',')
        grid_dim = (int(grid_dim_str[0]), int(grid_dim_str[1]))
        
        # Header: id,type,station,x,y,weight_to_NORTH,weight_to_WEST,weight_to_SOUTH,weight_to_EAST,weight_for_WAIT
        for line in lines[2:]: # Skip first two lines (grid_dim, header)
            parts = line.strip().split(',')
            node_id = int(parts[0])
            node_type = parts[1]
            station_str = parts[2]
            station_id = int(station_str) if station_str != 'None' else None
            x, y = int(parts[3]), int(parts[4])
            
            nodes[node_id] = {
                'id': node_id,
                'type': node_type,
                'station_id': station_id,
                'x': x,
                'y': y
            }
    return grid_dim, nodes

# --- 2. Parse Tasks File and Reconstruct Paths ---
def parse_tasks_and_reconstruct_paths(filepath, nodes_map):
    """
    Parses the tasks.txt file and reconstructs agent paths.
    A path is a dictionary: {time_step: (x, y)}
    """
    agents_data = {} # {agent_id: {'tasks': [], 'path': {time: (x,y)}, 'initial_pos_id': id}}
    max_time = 0

    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()] # Read non-empty lines
        
        num_agents = int(lines[0]) # First line is number of agents
        
        for i in range(1, num_agents + 1):
            agent_line = lines[i]
            parts = agent_line.split(';', 1) # Split only on the first semicolon
            header_part = parts[0].split(',')
            
            agent_id = int(header_part[0])
            initial_pos_id = int(header_part[1])
            
            agents_data[agent_id] = {'tasks': [], 'path': {}, 'initial_pos_id': initial_pos_id}
            
            current_node_id = initial_pos_id
            # Agent is at initial_pos_id at time 0
            initial_x, initial_y = nodes_map[initial_pos_id]['x'], nodes_map[initial_pos_id]['y']
            agents_data[agent_id]['path'][0] = (initial_x, initial_y)
            
            # This is the time when the agent *finishes* its previous action (or starts at t=0)
            # and is ready to travel to the next task's end_node_id.
            time_ready_for_travel = 0 

            if len(parts) > 1 and parts[1]: # Check if there are tasks
                task_strings = parts[1].strip(';').split(';')
                
                for task_str in task_strings:
                    if not task_str: continue # Skip empty task strings if any

                    task_parts = task_str.split(',')
                    end_node_id_str = task_parts[0]
                    
                    if end_node_id_str == "-1": # End of operations
                        # Agent stays at its current location indefinitely from time_ready_for_travel
                        # This will be handled by get_agent_position_at_time if no further path points
                        agents_data[agent_id]['tasks'].append({
                            'start_node_id': current_node_id,
                            'end_node_id': -1,
                            'arrival_time': time_ready_for_travel, # Effectively arrives at "end task"
                            'task_duration': 0, # No specific duration for this marker
                            'is_final': True
                        })
                        # Ensure path has current pos up to a reasonable max_time if this is the last task
                        # This will be handled by max_time later.
                        break # No more tasks for this agent

                    end_node_id = int(end_node_id_str)
                    arrival_time = int(task_parts[1])
                    task_duration = int(task_parts[2])

                    task_info = {
                        'start_node_id': current_node_id,
                        'end_node_id': end_node_id,
                        'arrival_time': arrival_time,
                        'task_duration': task_duration,
                        'is_final': False
                    }
                    agents_data[agent_id]['tasks'].append(task_info)

                    # --- Path Reconstruction ---
                    start_x, start_y = nodes_map[current_node_id]['x'], nodes_map[current_node_id]['y']
                    end_x, end_y = nodes_map[end_node_id]['x'], nodes_map[end_node_id]['y']

                    # Travel phase: from time_ready_for_travel to arrival_time - 1
                    travel_duration = arrival_time - time_ready_for_travel
                    
                    for t_offset in range(travel_duration):
                        t = time_ready_for_travel + t_offset
                        if travel_duration == 0: # Should not happen if arrival_time > time_ready_for_travel
                             # If it does, agent is already at start_x, start_y
                            agents_data[agent_id]['path'][t] = (start_x, start_y)
                        else:
                            ratio = t_offset / travel_duration # How far along the travel
                            # Linear interpolation for visualization
                            # At t_offset = 0, ratio = 0, pos = start_x, start_y
                            # As t_offset approaches travel_duration, ratio approaches 1
                            # We want agent to be at start_x, start_y for t_offset=0
                            # and arrive at end_x, end_y at arrival_time
                            # So, for t in [time_ready_for_travel, arrival_time-1]
                            # pos(t) = start + (end-start) * ( (t - time_ready_for_travel + 1) / (arrival_time - time_ready_for_travel) )
                            # Simpler: for each step, move a fraction of the way
                            # For t = time_ready_for_travel ... arrival_time -1
                            # current_travel_step = t - time_ready_for_travel
                            # interp_x = start_x + (end_x - start_x) * (current_travel_step / travel_duration)
                            # interp_y = start_y + (end_y - start_y) * (current_travel_step / travel_duration)
                            # This makes it reach end_x, end_y at arrival_time-1, which is not quite right.
                            # It should be at start_x, start_y at time_ready_for_travel
                            # and at end_x, end_y at arrival_time.

                            # Let's fill path from time_ready_for_travel up to arrival_time
                            # The agent is at start_x, start_y at time_ready_for_travel
                            # It arrives at end_x, end_y at arrival_time
                            # So for t in (time_ready_for_travel, arrival_time):
                            #    pos is interpolated
                            # agents_data[agent_id]['path'][time_ready_for_travel] = (start_x, start_y) # Already set or will be
                            
                            # For visualization, let's assume it moves one grid step per time unit if possible,
                            # or interpolates if travel_duration is less than Manhattan distance.
                            # For simplicity here, we'll just show it at start_node during travel, then jump.
                            # A better interpolation:
                            if t not in agents_data[agent_id]['path']: # Don't overwrite if already set by previous task end
                                agents_data[agent_id]['path'][t] = (start_x, start_y) # Stays at start during travel for now
                                                                                    # This is a simplification.
                                                                                    # A true interpolation would be:
                            # if travel_duration > 0:
                            #     current_progress = t_offset / travel_duration
                            #     interp_x = start_x * (1 - current_progress) + end_x * current_progress
                            #     interp_y = start_y * (1 - current_progress) + end_y * current_progress
                            #     agents_data[agent_id]['path'][t] = (interp_x, interp_y)
                            # else: # Instantaneous travel or already there
                            #     agents_data[agent_id]['path'][t] = (start_x, start_y)


                    # Task execution phase: from arrival_time to arrival_time + task_duration - 1
                    for t_offset in range(task_duration):
                        t = arrival_time + t_offset
                        agents_data[agent_id]['path'][t] = (end_x, end_y)
                        if t > max_time:
                            max_time = t
                    
                    # Update for next task
                    current_node_id = end_node_id
                    time_ready_for_travel = arrival_time + task_duration
            
            # Ensure agent path extends to max_time if it finishes early
            if time_ready_for_travel <= max_time:
                last_pos = agents_data[agent_id]['path'].get(
                    time_ready_for_travel -1 , 
                    (nodes_map[agents_data[agent_id]['initial_pos_id']]['x'], nodes_map[agents_data[agent_id]['initial_pos_id']]['y'])
                )
                if time_ready_for_travel -1 not in agents_data[agent_id]['path']: # if agent had no tasks
                     last_pos = agents_data[agent_id]['path'][0]


                for t in range(time_ready_for_travel, max_time + 1):
                    if t not in agents_data[agent_id]['path']:
                         agents_data[agent_id]['path'][t] = last_pos


    # Second pass to ensure all paths extend to global max_time
    for agent_id in agents_data:
        agent_path_max_time = 0
        if agents_data[agent_id]['path']:
            agent_path_max_time = max(agents_data[agent_id]['path'].keys())
        
        if not agents_data[agent_id]['path']: # Agent never moved
            initial_x, initial_y = nodes_map[agents_data[agent_id]['initial_pos_id']]['x'], nodes_map[agents_data[agent_id]['initial_pos_id']]['y']
            for t_step in range(max_time + 1):
                agents_data[agent_id]['path'][t_step] = (initial_x, initial_y)
            if max_time == 0 and not agents_data[agent_id]['path']: # Edge case: no tasks, no time
                 agents_data[agent_id]['path'][0] = (initial_x, initial_y)


        elif agent_path_max_time < max_time:
            last_pos = agents_data[agent_id]['path'][agent_path_max_time]
            for t_step in range(agent_path_max_time + 1, max_time + 1):
                agents_data[agent_id]['path'][t_step] = last_pos
        
        # Ensure path starts at t=0 if it somehow doesn't
        if 0 not in agents_data[agent_id]['path']:
            initial_x, initial_y = nodes_map[agents_data[agent_id]['initial_pos_id']]['x'], nodes_map[agents_data[agent_id]['initial_pos_id']]['y']
            agents_data[agent_id]['path'][0] = (initial_x, initial_y)


    return agents_data, max_time

def get_agent_position_at_time(agent_path_dict, time):
    """Gets agent position. If time is beyond recorded path, returns last known position."""
    if not agent_path_dict: # Empty path
        return None 
    
    if time in agent_path_dict:
        return agent_path_dict[time]
    else:
        # Find the largest time in path <= current time
        available_times = sorted([t for t in agent_path_dict.keys() if t <= time])
        if available_times:
            return agent_path_dict[available_times[-1]]
        else: # Time is before the first recorded step (e.g. time < 0, or path starts later)
            return agent_path_dict[min(agent_path_dict.keys())] # Return earliest known position


# --- 3. Visualization ---
def visualize_map_and_paths(grid_dim, nodes_map, agents_data, max_time_steps):
    fig, ax = plt.subplots(figsize=(max(10, grid_dim[0]/5) , max(8, grid_dim[1]/5)))
    ax.set_xlim(-1, grid_dim[0])
    ax.set_ylim(-1, grid_dim[1])
    ax.set_aspect('equal', adjustable='box')
    ax.set_xticks(np.arange(-0.5, grid_dim[0], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, grid_dim[1], 1), minor=True)
    ax.grid(which='minor', color='k', linestyle='-', linewidth=0.5)
    ax.tick_params(which='minor', size=0)
    ax.set_xticks(np.arange(0, grid_dim[0], 5)) # Major ticks
    ax.set_yticks(np.arange(0, grid_dim[1], 5)) # Major ticks


    # Node type colors
    type_colors = {
        "Obstacle": "black",
        "Travel": "white",
        "Induct": "green",
        "Eject": "red"
    }

    # Draw static map elements
    for node_id, node_info in nodes_map.items():
        x, y = node_info['x'], node_info['y']
        color = type_colors.get(node_info['type'], "lightgrey")
        rect = plt.Rectangle((x - 0.5, y - 0.5), 1, 1, facecolor=color, edgecolor='gray', linewidth=0.5)
        ax.add_patch(rect)
        if node_info['station_id'] is not None:
            ax.text(x, y, str(node_info['station_id'])[-2:], ha='center', va='center', fontsize=6, color='blue')

    # Agent colors
    agent_ids = sorted(agents_data.keys())
    colors = plt.cm.get_cmap('tab20', len(agent_ids))
    agent_color_map = {agent_id: colors(i) for i, agent_id in enumerate(agent_ids)}

    agent_artists = []
    for agent_id in agent_ids:
        # Initial position, though it will be updated immediately
        pos = get_agent_position_at_time(agents_data[agent_id]['path'], 0)
        if pos is None: # Should not happen if parse_tasks_and_reconstruct_paths is correct
            print(f"Warning: Agent {agent_id} has no position at t=0. Skipping.")
            continue

        circle = plt.Circle(pos, 0.4, color=agent_color_map[agent_id], zorder=10)
        ax.add_patch(circle)
        text = ax.text(pos[0], pos[1], str(agent_id), ha='center', va='center', fontsize=7, color='white', zorder=11, fontweight='bold')
        agent_artists.append({'circle': circle, 'text': text, 'id': agent_id, 'task_line': None, 'target_marker': None})

    time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12, bbox=dict(facecolor='white', alpha=0.8))

    def get_current_task_for_agent(agent_tasks_list, current_time):
        for task in agent_tasks_list:
            if task['is_final'] and current_time >= task['arrival_time']:
                 return task # Agent is done
            if not task['is_final']:
                task_active_start = task['arrival_time']
                task_active_end = task['arrival_time'] + task['task_duration']
                # Consider travel time too for "active task"
                # travel_start_time is when it LEAVES previous node
                # arrival_time is when it REACHES current task's end_node
                # task_duration is how long it STAYS at end_node
                
                # If current_time is during travel TO this task's end_node OR during its execution
                # For simplicity, let's say a task is "active" if the agent is executing it.
                if task_active_start <= current_time < task_active_end:
                    return task
        return None


    def update(frame):
        time_text.set_text(f'Time: {frame}')
        for artist_info in agent_artists:
            agent_id = artist_info['id']
            agent_path = agents_data[agent_id]['path']
            
            pos = get_agent_position_at_time(agent_path, frame)
            if pos is None: continue # Should not happen

            artist_info['circle'].center = pos
            artist_info['text'].set_position(pos)

            # Task visualization
            current_task = get_current_task_for_agent(agents_data[agent_id]['tasks'], frame)
            
            # Remove previous task line and target marker
            if artist_info['task_line']:
                artist_info['task_line'].remove()
                artist_info['task_line'] = None
            if artist_info['target_marker']:
                artist_info['target_marker'].remove()
                artist_info['target_marker'] = None

            if current_task and not current_task['is_final']:
                # Agent is actively performing this task (at end_node_id)
                start_node_coords = (nodes_map[current_task['start_node_id']]['x'], nodes_map[current_task['start_node_id']]['y'])
                end_node_coords = (nodes_map[current_task['end_node_id']]['x'], nodes_map[current_task['end_node_id']]['y'])
                
                # Draw line from agent's current pos to task's end_node_id (destination)
                # This is more useful if we show travel interpolation.
                # For now, let's just mark the target if it's "on task"
                # line = ax.plot([pos[0], end_node_coords[0]], [pos[1], end_node_coords[1]],
                #                color=agent_color_map[agent_id], linestyle='--', linewidth=1, zorder=5)
                # artist_info['task_line'] = line[0]
                
                # Mark the target node of the current task
                marker = ax.scatter(end_node_coords[0], end_node_coords[1], s=100,
                                    facecolors='none', edgecolors=agent_color_map[agent_id],
                                    marker='s', linewidth=2, zorder=6)
                artist_info['target_marker'] = marker
                artist_info['circle'].set_radius(0.45) # Slightly larger when on task
                artist_info['circle'].set_edgecolor('yellow')
                artist_info['circle'].set_linewidth(1.5)


            elif current_task and current_task['is_final']: # Agent is done
                artist_info['circle'].set_radius(0.3) 
                artist_info['circle'].set_edgecolor(None)
                artist_info['circle'].set_linewidth(0)


            else: # Agent is traveling or idle (not actively in task_duration phase)
                artist_info['circle'].set_radius(0.4)
                artist_info['circle'].set_edgecolor(None)
                artist_info['circle'].set_linewidth(0)


        return [artist['circle'] for artist in agent_artists] + \
               [artist['text'] for artist in agent_artists] + \
               ([artist['task_line'] for artist in agent_artists if artist['task_line']] if any(a.get('task_line') for a in agent_artists) else []) + \
               ([artist['target_marker'] for artist in agent_artists if artist['target_marker']] if any(a.get('target_marker') for a in agent_artists) else []) + \
               [time_text]

    if max_time_steps == 0 and not any(agents_data[ag_id]['path'] for ag_id in agents_data) : # No tasks, no movement
        print("No tasks or movements found. Displaying static map.")
        update(0) # Draw initial state
    elif max_time_steps == 0 and any(agents_data[ag_id]['path'] for ag_id in agents_data): # Only t=0 exists
        print("Only t=0 data. Displaying static map at t=0.")
        update(0)
    else:
        print(f"Animating up to {max_time_steps} time steps.")
        ani = animation.FuncAnimation(fig, update, frames=range(max_time_steps + 1),
                                      interval=200, blit=True, repeat=False)
    plt.title("Agent Paths and Tasks Visualization")
    plt.tight_layout()
    plt.show()


# --- Main Execution ---
if __name__ == "__main__":
    # Check if files exist
    if not os.path.exists(MAP_FILE):
        print(f"Error: Map file '{MAP_FILE}' not found.")
        exit()
    if not os.path.exists(TASKS_FILE):
        print(f"Error: Tasks file '{TASKS_FILE}' not found.")
        print(f"Please ensure '{TASKS_FILE}' is in the correct location.")
        # Try to find it in the script's directory if the original path fails
        script_dir = os.path.dirname(os.path.abspath(__file__))
        alt_tasks_file = os.path.join(script_dir, os.path.basename(TASKS_FILE))
        if os.path.exists(alt_tasks_file):
            print(f"Found tasks file at: {alt_tasks_file}")
            TASKS_FILE = alt_tasks_file
        else:
            alt_tasks_file_direct = os.path.join(script_dir, "centre_10_tasks.txt") # common renaming
            if os.path.exists(alt_tasks_file_direct):
                 print(f"Found tasks file at: {alt_tasks_file_direct}")
                 TASKS_FILE = alt_tasks_file_direct
            else:
                exit()


    grid_dimensions, map_nodes = parse_map(MAP_FILE)
    print(f"Map parsed: {grid_dimensions[0]}x{grid_dimensions[1]} grid, {len(map_nodes)} nodes.")
    
    agents_info, max_t = parse_tasks_and_reconstruct_paths(TASKS_FILE, map_nodes)
    print(f"Tasks parsed for {len(agents_info)} agents. Max time step: {max_t}")

    # for agent_id, data in agents_info.items():
    #     print(f"Agent {agent_id} initial: {data['initial_pos_id']}")
    #     # print(f"  Tasks: {data['tasks']}")
    #     # print(f"  Path keys: {sorted(data['path'].keys())}")
    #     if not data['path']:
    #         print(f"  WARNING: Agent {agent_id} has an empty path dict.")
    #     elif 0 not in data['path']:
    #         print(f"  WARNING: Agent {agent_id} path does not start at t=0. Min t: {min(data['path'].keys()) if data['path'] else 'N/A'}")


    visualize_map_and_paths(grid_dimensions, map_nodes, agents_info, max_t)