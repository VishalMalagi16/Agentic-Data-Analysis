# analysis_state.py
import pandas as pd
import json

class AnalysisState:
    """
    A centralized class to hold the state of the analysis.
    It tracks the user prompt, DataFrame versions, logs, results, and any artifacts.
    """
    def __init__(self, user_prompt: str, df: pd.DataFrame):
        self.user_prompt = user_prompt
        self.original_df = df.copy()
        self.current_df = df.copy()
        self.plan = []
        self.log = [f"Analysis initiated for user prompt: '{user_prompt}'"]
        self.results = {
            "summary": {},
            "preprocessing": [],
            "univariate": {},
            "bivariate": {},
        }
        # SOLUTION: Add a dedicated key for dataset artifacts
        self.artifacts = {
            "plots": [],
            "datasets": [] # Will store objects like {"filename": "...", "url": "..."}
        }

    def add_log(self, message: str):
        self.log.append(f"LOG: {message}")

    def add_result(self, agent: str, key: str, value: any):
        if agent not in self.results:
            self.results[agent] = {}
        self.results[agent][key] = value

    def add_artifact(self, plot_path: str):
        if plot_path not in self.artifacts["plots"]:
            self.artifacts["plots"].append(plot_path)

    # SOLUTION: Add a new method for dataset artifacts
    def add_dataset_artifact(self, filename: str, url: str):
        self.artifacts["datasets"].append({"filename": filename, "url": url})

    def update_dataframe(self, new_df: pd.DataFrame):
        self.current_df = new_df

    def get_state_summary_for_llm(self) -> str:
        summary = {
            "user_prompt": self.user_prompt,
            "plan_so_far": self.plan,
            "recent_logs": self.log[-5:],
            "results_summary": {
                "summary_keys": list(self.results.get("summary", {}).keys()),
                "preprocessing_actions_count": len(self.results.get("preprocessing", [])),
                "univariate_columns_analyzed": list(self.results.get("univariate", {}).keys()),
                "plot_count": len(self.artifacts.get("plots", [])),
                "dataset_count": len(self.artifacts.get("datasets", [])), # Add new count
            }
        }
        return json.dumps(summary, indent=2)

    def pretty_print(self):
        print("\n" + "="*20 + " CURRENT ANALYSIS STATE " + "="*20)
        print(f"\n[User Prompt]: {self.user_prompt}")
        print("\n[Plan]:")
        for i, step in enumerate(self.plan): print(f"  {i+1}. {step}")
        print("\n[Logs]:")
        for entry in self.log: print(f"  - {entry}")
        print("\n[Results]:")
        print(json.dumps(self.results, indent=2, default=str))
        print("\n[Artifacts]:")
        print(json.dumps(self.artifacts, indent=2, default=str))
        print("\n[Current DataFrame Preview]:")
        try:
            print(self.current_df.head().to_string())
        except Exception as e:
            print(f"  Could not display DataFrame head: {e}")
        print("\n" + "="*60 + "\n")