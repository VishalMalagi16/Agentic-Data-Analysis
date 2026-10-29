# summary_agent.py
import os
import json
import time
import pandas as pd
import re
import google.generativeai as genai

from analysis_state import AnalysisState
from summary_env.summary_agent_prompt import get_summary_agent_prompt
from summary_env.summary_tools import AVAILABLE_SUMMARY_TOOLS

# Configure the Gemini API
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
def extract_json_from_string(text: str) -> str:
    """
    Finds and extracts the first valid JSON object from a string.
    Handles cases where the LLM might add extra text before or after the JSON block.
    """
    # This regex finds a substring that starts with '{' and ends with '}'
    # It's non-greedy and handles nested structures.
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    # If no JSON object is found, return the original text or an empty object string
    return "{}"

class DataSummaryAgent:
    
    def __init__(self):
        self.llm = genai.GenerativeModel('gemini-2.0-flash-lite')
        self.tools = AVAILABLE_SUMMARY_TOOLS
        self.prompt_template = get_summary_agent_prompt()

    def run(self, state: AnalysisState, task_prompt: str) -> AnalysisState:
        print(f"\n--- Running DataSummaryAgent for task: '{task_prompt}' ---")
        conversation_history = [f"Task from Orchestrator: {task_prompt}"]
        
        # This agent usually needs fewer steps
        for i in range(10):
            full_prompt = self.prompt_template + "\n\nANALYSIS HISTORY:\n" + "\n".join(conversation_history)

            try:
                response = self.llm.generate_content(full_prompt)
                json_part = extract_json_from_string(response.text)
                parsed_response = json.loads(json_part)
                thought, action = parsed_response.get("thought"), parsed_response.get("action")
            except (json.JSONDecodeError, AttributeError, ValueError, Exception) as e:
                # This error handling is now more robust.
                print(f"Error parsing or generating LLM response: {e}")
                print(f"LLM Raw Response Text: \n---\n{response.text}\n---")
                error_feedback = f"Observation: Your last response was invalid or could not be parsed. Error: {e}. You MUST respond with a single, valid JSON object."
                conversation_history.append(error_feedback)
                continue

            print(f"\nStep {i+1}:\nThought: {thought}")
            conversation_history.append(f"Thought: {thought}")
            
            tool_name = action.get("tool_name")
            parameters = action.get("parameters", {})
            
            if tool_name == "finish":
                summary = parameters.get("summary", "Summary task completed.")
                print(f"Action: Finish. Summary: {summary}")
                state.add_log(f"DataSummaryAgent finished: {summary}")
                break

            print(f"Action: Calling tool '{tool_name}' with params {parameters}")
            
            if tool_name in self.tools:
                tool_function = self.tools[tool_name]
                try:
                    # Pass the DataFrame to the tool function
                    observation_json = tool_function(df=state.current_df, **parameters)
                    observation_data = json.loads(observation_json)

                    # Add the result to the 'summary' section of the state
                    state.add_result(agent="summary", key=tool_name, value=observation_data)

                    print(f"Observation: {observation_json}")
                    conversation_history.append(f"Action: Called {tool_name} with {parameters}")
                    conversation_history.append(f"Observation: {observation_json}")
                except Exception as e:
                    print(f"Error executing tool {tool_name}: {e}")
                    error_msg = f"Observation: Error executing tool: {e}."
                    conversation_history.append(error_msg)
            else:
                print(f"Error: Tool '{tool_name}' not found.")
                available_tools = list(self.tools.keys())
                error_feedback = f"Observation: Tool '{tool_name}' not found. You must choose from: {available_tools}"
                conversation_history.append(error_feedback)
            
            time.sleep(5) # API rate limiting

        if i == 9:
             print("Warning: Summary Agent reached maximum steps.")
             state.add_log("Summary Agent finished due to reaching max steps.")

        print("--- DataSummaryAgent Finished ---")
        return state

# --- Test Block ---
if __name__ == '__main__':
    if "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("Please set the GOOGLE_API_KEY environment variable.")

    data = {
        'age': [25, 30, 35, 40, 45, None],
        'department': ['HR', 'IT', 'IT', 'HR', 'Sales', 'Sales'],
        'salary': [50000, 60000, 70000, 65000, 80000, 90000],
        'start_date': pd.to_datetime(['2020-01-15', '2019-03-12', '2021-07-20', '2020-05-01', '2018-11-11', '2022-02-01'])
    }
    sample_df = pd.DataFrame(data)
    initial_state = AnalysisState(user_prompt="Summarize my new employee dataset.", df=sample_df)
    
    orchestrator_task = "Provide a comprehensive initial summary of the dataset. I need to know its dimensions, column types, see if there's missing data, and get a classification of the columns."

    summary_agent = DataSummaryAgent()
    final_state = summary_agent.run(initial_state, orchestrator_task)

    print("\n--- Final Analysis State After Summary ---")
    final_state.pretty_print()