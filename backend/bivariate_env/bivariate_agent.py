# bivariate_env/bivariate_agent.py
import os
import json
import time
import pandas as pd
import google.generativeai as genai
import re # <-- SOLUTION: Import the regular expression module

from analysis_state import AnalysisState
from bivariate_env.bivariate_tools import AVAILABLE_BIVARIATE_TOOLS
from bivariate_env.bivariate_agent_prompt import get_bivariate_agent_prompt

# --- Load Knowledge Base ---
try:
    with open('bivariate_env/bivariate_rules.json', 'r') as f:
        RULES = f.read()
    with open('univariate_env/method_details.json', 'r') as f: # Reusing method details
        METHODS = f.read()
except FileNotFoundError as e:
    print(f"Error: Bivariate knowledge base file not found. {e}")
    exit()

# Configure Gemini API
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash-lite')

class BivariateAgent:
    def __init__(self):
        self.llm = model
        self.tools = AVAILABLE_BIVARIATE_TOOLS
        self.prompt_template = get_bivariate_agent_prompt(RULES, METHODS)

    def run(self, state: AnalysisState, task_prompt: str) -> AnalysisState:
        print(f"--- Running Bivariate Agent for task: '{task_prompt}' ---")
        conversation_history = [f"Task from Orchestrator: {task_prompt}"]
        
        UTILITY_TOOLS = ["get_all_column_names", "get_pair_dtypes", "get_value_counts"]
        
        for i in range(50):
            full_prompt = self.prompt_template + "\n\nANALYSIS HISTORY:\n" + "\n".join(conversation_history)

            response = self.llm.generate_content(full_prompt)
            
            try:
                cleaned_response_text = response.text.strip()
                if '```json' in cleaned_response_text:
                    json_match = re.search(r'\{[\s\S]*\}', cleaned_response_text)
                    if json_match:
                        cleaned_response_text = json_match.group(0)
                
                parsed_response = json.loads(cleaned_response_text)
                thought, action = parsed_response.get("thought"), parsed_response.get("action")
            except (json.JSONDecodeError, AttributeError, IndexError) as e:
                print(f"Error parsing Bivariate Agent LLM response: {response.text}\nError: {e}")
                conversation_history.append(f"Observation: Your last response was not valid JSON. You must respond with a single, valid JSON object containing 'thought' and 'action' keys. The LLM response was: {response.text}")
                continue

            if not thought or not action:
                print(f"Invalid response structure from LLM: {parsed_response}")
                conversation_history.append("Observation: Your last response was missing the 'thought' or 'action' key.")
                continue

            print(f"\nStep {i+1}:\nThought: {thought}")
            conversation_history.append(f"Thought: {thought}")
            
            # Handle single or multiple actions per step
            actions = action if isinstance(action, list) else [action]
            for single_action in actions:
                tool_name = single_action.get("tool_name")
                parameters = single_action.get("parameters", {})

                if tool_name == "finish":
                    summary = parameters.get("summary", "Bivariate analysis task completed.")
                    print(f"Action: Finish. Summary: {summary}")
                    state.add_log(f"Bivariate Agent finished: {summary}")
                    return state

                print(f"Action: Calling tool '{tool_name}' with params {parameters}")

                if tool_name in self.tools:
                    tool_function = self.tools[tool_name]
                    try:
                        observation_json = tool_function(df=state.current_df, **parameters)
                        observation_data = json.loads(observation_json)

                        if "plot_path" in observation_data:
                            state.add_artifact(observation_data["plot_path"])
                        elif "error" not in observation_data and tool_name not in UTILITY_TOOLS:
                            cols = [parameters.get('x_col'), parameters.get('y_col')]
                            valid_cols = sorted([c for c in cols if c is not None])
                            if len(valid_cols) == 2:
                                pair_key_str = f"{valid_cols[0]}_vs_{valid_cols[1]}"
                                if "bivariate" not in state.results:
                                    state.results["bivariate"] = {}
                                if pair_key_str not in state.results["bivariate"]:
                                    state.results["bivariate"][pair_key_str] = {}
                                state.results["bivariate"][pair_key_str][tool_name] = observation_data
                            else:
                                print(f"[Warning] Could not form a valid pair key for tool {tool_name} with params {parameters}")
                        print(f"Observation: {observation_json}")
                        conversation_history.extend([f"Action: Called {tool_name} with {parameters}", f"Observation: {observation_json}"])
                    except Exception as e:
                        error_msg = f"Observation: Error executing tool {tool_name}: {e}"
                        print(error_msg)
                        conversation_history.append(error_msg)
                else:
                    error_msg = f"Observation: Tool '{tool_name}' is not a valid tool."
                    print(error_msg)
                    conversation_history.append(error_msg)

        if i == 49:
            state.add_log("Bivariate Agent finished due to reaching max steps.")

        print("--- Bivariate Agent Finished ---")
        return state