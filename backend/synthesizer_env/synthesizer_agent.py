
# synthesizer_agent.py
import os
import json
import time
import google.generativeai as genai

from analysis_state import AnalysisState
from synthesizer_env.synthesizer_agent_prompt import get_synthesizer_agent_prompt

# Configure the Gemini API
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

class SynthesizerAgent:
    def __init__(self):
        self.llm = genai.GenerativeModel('gemini-2.0-flash-lite')
        self.prompt_template = get_synthesizer_agent_prompt()

    def _get_state_as_json(self, state: AnalysisState) -> str:
        """Converts the full state object to a JSON string for the LLM."""
        # A custom serializer to handle pandas DataFrame if it were ever needed
        def custom_serializer(obj):
            if isinstance(obj, pd.DataFrame):
                return obj.to_dict()
            return str(obj)

        state_dict = {
            "user_prompt": state.user_prompt,
            "plan": state.plan,
            "log": state.log,
            "results": state.results,
            "artifacts": state.artifacts
        }
        return json.dumps(state_dict, indent=2, default=custom_serializer)


    def run(self, state: AnalysisState, task_prompt: str) -> str:
        """
        Runs the synthesis process.
        Returns the final report as a markdown string.
        """
        print(f"\n--- Running SynthesizerAgent for task: '{task_prompt}' ---")
        
        state_json = self._get_state_as_json(state)
        
        # The prompt includes the full state
        full_prompt = self.prompt_template + f"\n\nCURRENT_ANALYSIS_STATE:\n{state_json}"+f"\n\nUSER_PROMPT:\n{task_prompt}"
        
        response = None  # Initialize response to None before the try block
        try:
            # This is the line that can fail
            response = self.llm.generate_content(full_prompt) 
            
            cleaned_response_text = response.text.strip().replace('```json', '').replace('```', '')
            cleaned_response_text = cleaned_response_text.replace('\\_', '_')
            parsed_response = json.loads(cleaned_response_text)
            
            thought = parsed_response.get("thought", "No thought provided.")
            action = parsed_response.get("action", {})
            
            print(f"\nThought: {thought}")

            if action.get("tool_name") == "finish":
                final_report = action.get("parameters", {}).get("report", "No report was generated.")
                print("--- SynthesizerAgent Finished ---")
                return final_report
            else:
                return "Error: Synthesizer agent did not call the 'finish' tool correctly."

        except Exception as e: # Catch a broader range of exceptions
            print(f"--- ERROR in SynthesizerAgent ---")
            print(f"An exception occurred: {e}")

            # Only try to print the response text if the response object was successfully created
            if response and hasattr(response, 'text'):
                print(f"LLM Raw Response Text: \n---\n{response.text}\n---")
            else:
                print("Could not get a valid response from the LLM. It likely failed due to a connection or quota error.")
            
            return f"Error: Could not generate final report. The final synthesis step failed with error: {e}"


# --- Test Block ---
if __name__ == '__main__':
    if "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("Please set the GOOGLE_API_KEY environment variable.")

    # Create a realistic-looking final state object for testing
    import pandas as pd
    test_state = AnalysisState("Analyze my employee data", pd.DataFrame())
    test_state.log = [
        "Analysis initiated for user prompt: 'Analyze my employee data'",
        "LOG: DataSummaryAgent: Found columns and noted some missing values.",
        "LOG: PreprocessingAgent: Handled outliers in 'age' column.",
        "LOG: Univariate Agent finished its task: Completed full univariate analysis for columns: age, salary."
    ]
    test_state.results = {
        "summary": {
            "get_shape": {"rows": 11, "columns": 3},
            "identify_column_types": {"numerical": ["age", "salary"], "categorical": ["department"]}
        },
        "preprocessing": [{"action": "Handled outliers in 'age' column", "details": "Clipped values > 90."}],
        "univariate": {
            "age": {
                "calculate_descriptive_stats": {"mean": 40.45, "median": 35.0, "std": 18.22, "min": 25, "max": 90}
            },
            "salary": {
                "calculate_descriptive_stats": {"mean": 67900, "median": 66000, "std": 14216}
            }
        }
    }
    test_state.artifacts = {
        "plots": ["plots/histogram_age.png", "plots/histogram_salary.png"]
    }

    synthesizer = SynthesizerAgent()
    final_report_markdown = synthesizer.run(test_state, "Create a final report from the analysis.")

    print("\n\n--- FINAL GENERATED REPORT ---")
    print(final_report_markdown)