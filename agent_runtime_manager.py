import subprocess
import os
import argparse

class LifelongLauncher:
    """
    A class to configure and launch the 'lifelong' C++ simulation engine.
    It acts as a launcher, not a real-time manager.
    """
    def __init__(self, lifelong_path, map_file, output_folder,
                 num_agents, scenario_name, solver,
                 simulation_time=5000, simulation_window=5, planning_window=100,
                 task_file=None, seed=0, suboptimality=1.1, extra_args=None):
        """
        Initializes the LifelongLauncher.

        :param lifelong_path: Path to the compiled 'lifelong' executable.
        :param map_file: Path to the map file for the planner.
        :param output_folder: Path to the folder for output files.
        :param num_agents: The number of agents to simulate (-k).
        :param scenario_name: The simulation scenario name (e.g., "SORTING").
        :param solver: The solver to use (e.g., "PBS").
        :param simulation_time: Total simulation time.
        :param simulation_window: Replanning period, h.
        :param planning_window: Planning window, w.
        :param task_file: Optional path to a pre-generated task file.
        :param seed: The random seed.
        :param suboptimality: The suboptimality factor for the solver.
        :param extra_args: A list of additional command-line arguments.
        """
        self.lifelong_path = lifelong_path
        self.map_file = map_file
        self.output_folder = output_folder
        self.num_agents = num_agents
        self.scenario_name = scenario_name
        self.solver = solver
        self.simulation_time = simulation_time
        self.simulation_window = simulation_window
        self.planning_window = planning_window
        self.task_file = task_file
        self.seed = seed
        self.suboptimality = suboptimality
        self.extra_args = extra_args if extra_args is not None else []
        
        self.process = None

    def run_simulation(self):
        """
        Calls the external 'lifelong' simulation engine once with all parameters.
        """
        print("--- Launching 'lifelong' simulation engine ---")
        
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            print(f"Created output directory: {self.output_folder}")

        try:
            command = [
                self.lifelong_path,
                "-m", self.map_file,
                "-o", self.output_folder,
                "-k", str(self.num_agents),
                "--scenario", self.scenario_name,
                "--solver", self.solver,
                "--simulation_time", str(self.simulation_time),
                "--simulation_window", str(self.simulation_window),
                "--planning_window", str(self.planning_window),
                "-d", str(self.seed),
                "--suboptimal_bound", str(self.suboptimality)
            ]
            
            if self.task_file:
                command.extend(["--task", self.task_file])

            command.extend(self.extra_args)

            print(f"Executing command: {' '.join(command)}")
            
            # This runs the command and waits for it to complete.
            # The output of the C++ program will be streamed to the console.
            self.process = subprocess.run(command, check=True)
            
            print("\n--- 'lifelong' simulation finished. ---")

        except FileNotFoundError:
            print(f"Error: The executable was not found at '{self.lifelong_path}'")
        except subprocess.CalledProcessError as e:
            print(f"Error: 'lifelong' exited with a non-zero status code: {e.returncode}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Launch the 'lifelong' MAPF simulation engine.")
    
    parser.add_argument("lifelong_path", help="Path to the compiled 'lifelong' executable.")
    parser.add_argument("-m", "--map_file", required=True, help="Path to the map file.")
    parser.add_argument("-o", "--output_folder", required=True, help="Path to the folder for output files.")
    parser.add_argument("-k", "--num_agents", required=True, type=int, help="The number of agents to simulate.")
    parser.add_argument("--scenario", required=True, help="The simulation scenario name (e.g., 'SORTING').")
    parser.add_argument("--solver", required=True, help="The solver to use (e.g., 'PBS').")
    parser.add_argument("--simulation_time", type=int, default=5000, help="Total simulation time.")
    parser.add_argument("--simulation_window", type=int, default=5, help="Replanning period (h).")
    parser.add_argument("--planning_window", type=int, default=100, help="Planning window (w).")
    parser.add_argument("--task", dest="task_file", help="Optional path to a pre-generated task file.")
    parser.add_argument("-d", "--seed", type=int, default=0, help="The random seed.")
    parser.add_argument("--suboptimal_bound", dest="suboptimality", type=float, default=1.1, help="The suboptimality factor for the solver.")
    
    args, unknown = parser.parse_known_args()

    launcher = LifelongLauncher(
        lifelong_path=args.lifelong_path,
        map_file=args.map_file,
        output_folder=args.output_folder,
        num_agents=args.num_agents,
        scenario_name=args.scenario,
        solver=args.solver,
        simulation_time=args.simulation_time,
        simulation_window=args.simulation_window,
        planning_window=args.planning_window,
        task_file=args.task_file,
        seed=args.seed,
        suboptimality=args.suboptimality,
        extra_args=unknown
    )

    launcher.run_simulation()

    print(f"\nSimulation complete. Check the output files in '{args.output_folder}'.")
    try:
        output_files = os.listdir(args.output_folder)
        if output_files:
            print("Generated files:", output_files)
        else:
            print("No files were generated in the output directory.")
    except FileNotFoundError:
        print(f"Output directory '{args.output_folder}' not found.")
