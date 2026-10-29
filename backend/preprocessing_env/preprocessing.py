# preprocessing_env/preprocessing.py
import os
import json
import uuid # For unique filenames
import pandas as pd
import google.generativeai as genai
import re

from preprocessing_env.preprocessing_agent_tools import PreprocessingTools
from preprocessing_env.preprocessing_agent_prompt import get_preprocessing_agent_prompt
from analysis_state import AnalysisState

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", "fake-key-for-testing"))
model = genai.GenerativeModel('gemini-2.0-flash-lite')

# SOLUTION: Define the save directory for cleaned datasets
DATASET_SAVE_DIR = os.path.join("artifacts", "datasets")
os.makedirs(DATASET_SAVE_DIR, exist_ok=True)

class PreprocessingAgent:
    def __init__(self):
        self.llm = model
        self.tools = PreprocessingTools()
        self.prompt_template = get_preprocessing_agent_prompt()

    def run(self, state: AnalysisState, task_prompt: str) -> AnalysisState:
        print(f"--- Running Preprocessing Agent for task: '{task_prompt}' ---")
        conversation_history = [
            f"Task from Orchestrator: {task_prompt}",
            "Begin the standard preprocessing workflow now."
        ]
        state_summary_for_llm = state.get_state_summary_for_llm()

        for step in range(10): # Max steps
            context_header = f"Task: {task_prompt}\nANALYSIS_STATE_SUMMARY:\n{state_summary_for_llm}"
            full_prompt = self.prompt_template + "\n--- YOUR CURRENT CONTEXT ---\n" + context_header + "\n\n--- CONVERSATION HISTORY ---\n" + "\n".join(conversation_history)
            
            response = self.llm.generate_content(full_prompt)
            action_json = response.text.strip()
            
            if action_json.startswith("```"):
                action_json = re.search(r'\{[\s\S]*\}', action_json).group(0)

            try:
                plan = json.loads(action_json)
            except json.JSONDecodeError:
                continue

            conversation_history.append(action_json)
            
            if not plan.get("action"): break

            for action in plan["action"]:
                tool_name = action["tool_name"]
                if tool_name == 'finish':
                    # --- SOLUTION: SAVE THE FILE ON FINISH ---
                    try:
                        # Generate a unique filename to prevent collisions
                        unique_id = str(uuid.uuid4())[:8]
                        filename = f"cleaned_data_{unique_id}.csv"
                        save_path = os.path.join(DATASET_SAVE_DIR, filename)
                        
                        # Save the cleaned DataFrame
                        state.current_df.to_csv(save_path, index=False)
                        url = os.path.join("/datasets", filename).replace('\\', '/')
                        # Add the artifact to the state
                        # The URL will be constructed by the frontend
                        state.add_dataset_artifact(filename=filename, url=url)
                        
                        print(f"--- Preprocessing Complete. Cleaned data saved to {save_path} ---")
                    except Exception as e:
                        print(f"Error saving cleaned dataset: {e}")
                    
                    return state # Exit the run method
                
                params = action.get("parameters", {})
                if tool_name == "impute_column" and "is_categorical" not in params:
                    params["is_categorical"] = False

                if "column" in params and params["column"] not in state.current_df.columns:
                    print(f"[WARNING] Skipping action: {tool_name} on non-existent column '{params['column']}'")
                    continue

                if hasattr(self.tools, tool_name):
                    tool = getattr(self.tools, tool_name)
                    result = tool(state.current_df, **params)
                    conversation_history.append(f"TOOL RESULT for {tool_name}({params}): {result}")
                    if isinstance(result, pd.DataFrame):
                        state.update_dataframe(result)
                    else:
                        print(f"[INFO] Tool '{tool_name}' returned: {result}")
                else:
                    print(f"❌ Unknown tool: {tool_name}")

        print("--- Preprocessing Agent finished (max steps reached) ---")
        return state