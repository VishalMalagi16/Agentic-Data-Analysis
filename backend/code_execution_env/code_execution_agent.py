import os
import pandas as pd
import docker
from analysis_state import AnalysisState
import google.generativeai as genai
from .code_execution_prompt import get_code_execution_prompt
import tempfile
import pickle
import textwrap

class CodeExecutionAgent:
    def __init__(self):
        # This agent needs its own LLM to write code
        self.llm = genai.GenerativeModel('gemini-2.0-flash-lite') # Use a strong model for coding
        self.prompt_template = get_code_execution_prompt()
        try:
            print("Connecting to Docker daemon...")
            self.docker_client = docker.from_env()
            # Ping the server to confirm the connection works.
            self.docker_client.ping()
            print("Successfully connected to Docker daemon.")
        except docker.errors.DockerException as e:
            print("\n" + "="*50)
            print("FATAL ERROR: Could not connect to the Docker daemon.")
            print("Please make sure Docker Desktop is running.")
            print(f"Original error: {e}")
            print("="*50 + "\n")
            raise
        try:
            self.docker_client.images.get("python-datasci-sandbox")
            print("Docker image 'python-datasci-sandbox' found.")
        except docker.errors.ImageNotFound:
            print("\n" + "="*50)
            print("FATAL ERROR: Docker image 'python-datasci-sandbox' not found.")
            print("Please build it first by running this command in your terminal:")
            print("docker build -t python-datasci-sandbox .")
            print("="*50 + "\n")
            raise

    def _execute_code_in_sandbox(self, code: str, df: pd.DataFrame) -> (str, str, str, pd.DataFrame):
        """Executes code in a secure Docker container."""
        indented_code = textwrap.indent(code, '    ')
        # Create a temporary directory on the host
        with tempfile.TemporaryDirectory() as temp_dir:
            host_input_path = os.path.join(temp_dir, "input.pkl")
            host_output_path = os.path.join(temp_dir, "output.pkl")
            host_artifacts_path = os.path.join(temp_dir, "artifacts")
            os.makedirs(host_artifacts_path)

            # Save the incoming DataFrame to the temp directory
            with open(host_input_path, "wb") as f:
                pickle.dump(df, f)

            # Define container paths
            container_data_path = "/app/data"
            container_artifacts_path = "/app/artifacts"

            # The Python script to be run inside the container
            script = f"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pickle

# Load the DataFrame
with open('{container_data_path}/input.pkl', 'rb') as f:
    df = pickle.load(f)

# --- LLM Generated Code ---
try:
    {indented_code}
except Exception as e:
    print(f"CODE_EXECUTION_ERROR: {{e}}") # Use a specific prefix for errors

# ------------------------

# Save the potentially modified DataFrame
with open('{container_data_path}/output.pkl', 'wb') as f:
    pickle.dump(df, f)
"""
            # Run the container
            try:
                container = self.docker_client.containers.run(
                    image="python-datasci-sandbox",
                    command=["python", "-c", script],
                    volumes={
                    temp_dir: {'bind': container_data_path, 'mode': 'rw'},
                    host_artifacts_path: {'bind': container_artifacts_path, 'mode': 'rw'},
                    },
                    network_mode='none',  # Disable networking for security
                    mem_limit='512m',     # Limit memory
                    cpu_period=100000,
                    cpu_quota=50000,      # Limit CPU to 0.5 cores
                    working_dir="/app",
                    detach=True,
                )
                # Wait for container to finish, with a timeout
                result = container.wait(timeout=30)
                stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
                stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
                container.remove()
            except Exception as e:
                return "", f"DOCKER_RUNTIME_ERROR: {e}", [], df # Return original df

            # Load the modified DataFrame
            if os.path.exists(host_output_path):
                with open(host_output_path, "rb") as f:
                    modified_df = pickle.load(f)
            else:
                modified_df = df # If output wasn't created, return original

            # Collect, move, and standardize artifact paths
            url_paths = []
            final_plot_dir = os.path.join("artifacts", "plots")
            os.makedirs(final_plot_dir, exist_ok=True)
            
            if os.path.exists(host_artifacts_path):
                for filename in os.listdir(host_artifacts_path):
                    temp_file_path = os.path.join(host_artifacts_path, filename)
                    final_file_path = os.path.join(final_plot_dir, filename)
                    
                    # Move the file from the temp docker volume to the final artifacts dir
                    os.rename(temp_file_path, final_file_path)
                    url_path = os.path.join("plots", filename).replace('\\', '/')
                    url_paths.append(url_path)
                    # Create the relative path for the state and frontend URL
                    url_paths.append(os.path.join("plots", filename))

            return stdout, stderr, url_paths, modified_df

    def run(self, state: AnalysisState, task_prompt: str) -> AnalysisState:
        """The main ReAct loop for the Code Execution Agent."""
        print(f"\n--- Activating Code Execution Agent ---")
        print(f"Task: {task_prompt}")

        # The ReAct loop for this agent
        for i in range(5): # Allow for a few steps of thought/correction
            full_prompt = self.prompt_template.format(
                task=task_prompt,
                dataframe_summary=state.get_state_summary_for_llm()
            )

            response = self.llm.generate_content(full_prompt)
            # This agent doesn't need a complex JSON response, just the code block
            code_to_run = response.text.strip().replace('```python', '').replace('```', '')

            print(f"Code Agent Thought/Code:\n{code_to_run}")

            # Execute the code
            stdout, stderr, artifact_paths, modified_df = self._execute_code_in_sandbox(code_to_run, state.current_df)

            # Update state
            state.current_df = modified_df # Always update with the latest df
            log_message = f"Code Execution Agent ran code. Task: '{task_prompt}'."
            if stdout:
                print(f"STDOUT:\n{stdout}")
                log_message += f"\nOutput:\n{stdout}"
            if stderr:
                print(f"STDERR:\n{stderr}")
                log_message += f"\nErrors:\n{stderr}"
            if artifact_paths:
                print(f"Artifacts Created: {artifact_paths}")
                state.artifacts['plots'].extend(artifact_paths)
                log_message += f"\nCreated artifacts: {artifact_paths}"

            state.log.append(log_message)

            # For this simple implementation, we'll just run once and return.
            # A more advanced version would have the LLM analyze the stdout/stderr
            # and decide if it needs to run more code.
            break

        print(f"--- Deactivating Code Execution Agent ---")
        return state