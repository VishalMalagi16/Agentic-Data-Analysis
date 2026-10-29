# univariate_agent.py
import os
import json
import time
import pandas as pd
import google.generativeai as genai
from univariate_env.univariate_tools import AVAILABLE_TOOLS
from univariate_env.univariate_agent_prompt import get_univariate_agent_prompt

# --- Load the Agent's Knowledge Base ---
try:
    with open('univariate_env/univariate_rules.json', 'r') as f:
        RULES = f.read()
    with open('univariate_env/method_details.json', 'r') as f:
        METHODS = f.read()
except FileNotFoundError as e:
    print(f"Error: Knowledge base file not found. Make sure 'univariate_rules.json' and 'method_details.json' are in the same directory.")
    print(e)
    exit()

# Configure the Gemini API
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash-lite')


# Placeholder for the shared AnalysisState class
class AnalysisState:
    def __init__(self, user_prompt, df):
        self.user_prompt = user_prompt
        self.current_df = df
        self.log = [f"Analysis initiated for: '{user_prompt}'"]
        self.results = {"univariate": {}} 
        self.artifacts = {"plots": []}
    
    def add_log(self, message: str): self.log.append(message)
    
    def add_result(self, column: str, analysis_type: str, result: dict):
        if column not in self.results["univariate"]: self.results["univariate"][column] = {}
        self.results["univariate"][column][analysis_type] = result

    def add_artifact(self, plot_path: str): self.artifacts["plots"].append(plot_path)

class UnivariateAgent:
    def __init__(self):
        self.llm = model
        self.tools = AVAILABLE_TOOLS
        # Generate the prompt with the loaded knowledge
        self.prompt_template = get_univariate_agent_prompt(RULES, METHODS)
    @staticmethod    
    def add_univariate_result(state: AnalysisState, column: str, analysis_type: str, result: dict):
        """Safely adds a result to the state under the 'univariate' key."""
        if "univariate" not in state.results:
            state.results["univariate"] = {}
        if column not in state.results["univariate"]:
            state.results["univariate"][column] = {}
        state.results["univariate"][column][analysis_type] = result

    def run(self, state: AnalysisState, task_prompt: str) -> AnalysisState:
        print(f"--- Running Univariate Agent for task: '{task_prompt}' ---")
        conversation_history = [f"Task from Orchestrator: {task_prompt}"]
        
        for i in range(25): # Increased steps for more complex reasoning
            full_prompt = self.prompt_template + "\n\nANALYSIS HISTORY:\n" + "\n".join(conversation_history)

            response = self.llm.generate_content(full_prompt)
            
            try:
                cleaned_response_text = response.text.strip().replace('```json', '').replace('```', '')
                parsed_response = json.loads(cleaned_response_text)
                thought, action = parsed_response.get("thought"), parsed_response.get("action")
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"Error parsing LLM response: {response.text}\nError: {e}")
                error_feedback = (
                    "Observation: Your last response was not a single, valid JSON object. "
                    f"The parser failed with error: '{e}'. "
                    "You MUST respond with only one JSON object containing a 'thought' and an 'action'."
                )
                conversation_history.append(error_feedback)
                continue

            print(f"\nStep {i+1}:\nThought: {thought}")
            conversation_history.append(f"Thought: {thought}")
            
            tool_name = action.get("tool_name")
            parameters = action.get("parameters", {})
            
            if tool_name == "finish":
                summary = parameters.get("summary", "Task completed.") # Provide a default
                print(f"Action: Finish. Summary: {summary}")
                state.add_log(f"Univariate Agent finished: {action.get('summary')}")
                break

            print(f"Action: Calling tool '{tool_name}' with params {parameters}")
            
            if tool_name in self.tools:
                tool_function = self.tools[tool_name]
                try:
                    observation_json = tool_function(df=state.current_df, **parameters)
                    observation_data = json.loads(observation_json)

                    # Log results and artifacts to the state
                    column = parameters.get('column')
                    if "plot_path" in observation_data:
                        state.add_artifact(observation_data["plot_path"])
                    elif "error" not in observation_data and column:
                        # Use the new, safe helper function
                        self.add_univariate_result(state, column, tool_name, observation_data)

                    print(f"Observation: {observation_json}")
                    conversation_history.append(f"Action: Called {tool_name} with {parameters}")
                    conversation_history.append(f"Observation: {observation_json}")
                except Exception as e:
                    print(f"Error executing tool {tool_name}: {e}")
                    conversation_history.append(f"Observation: Error executing tool: {e}")
            else:
                print(f"Error: Tool '{tool_name}' not found.")
                conversation_history.append(f"Observation: Tool '{tool_name}' is not a valid tool.")
            print("\nPausing for a moment to respect API rate limits...")
            time.sleep(5)
        print("--- Univariate Agent Finished ---")
        return state

# --- Test Block ---
if __name__ == '__main__':
    data = {
        'age': [25, 30, 35, 40, 45, 50, 25, 30, 35, 40, 95], # Added outlier
        'department': ['HR', 'IT', 'IT', 'HR', 'Sales', 'Sales', 'IT', 'HR', 'IT', 'Sales','Sales'],
        'salary': [50000, 60000, 70000, 65000, 80000, 90000, 55000, 62000, 75000, 85000, 52000]
    }
    sample_df = pd.DataFrame(data)
    initial_state = AnalysisState(user_prompt="Analyze my employee data", df=sample_df)
    orchestrator_task = "Perform a full univariate analysis on the 'age' and 'department' columns."

    univariate_agent = UnivariateAgent()
    final_state = univariate_agent.run(initial_state, orchestrator_task)

    print("\n--- Final Analysis State ---")
    print("Log:"); [print(f"- {log}") for log in final_state.log]
    print("\nResults:"); print(json.dumps(final_state.results, indent=2))
    print("\nArtifacts:"); print(json.dumps(final_state.artifacts, indent=2))