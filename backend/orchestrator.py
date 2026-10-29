# orchestrator.py
import os
import json
import pandas as pd
import pickle
import google.generativeai as genai
import time
import re
from analysis_state import AnalysisState
from summary_env.summary import DataSummaryAgent
from preprocessing_env.preprocessing import PreprocessingAgent
from synthesizer_env.synthesizer_agent import SynthesizerAgent
from univariate_env.univariate_agent import UnivariateAgent
from bivariate_env.bivariate_agent import BivariateAgent
from orchestrator_agent_prompt import get_orchestrator_prompt
from code_execution_env.code_execution_agent import CodeExecutionAgent

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

class OrchestratorAgent:
    def __init__(self):
        self.llm = genai.GenerativeModel('gemini-2.0-flash-lite')
        self.prompt_template = get_orchestrator_prompt()
        self.summary_agent = DataSummaryAgent()
        self.preprocessing_agent = PreprocessingAgent()
        self.univariate_agent = UnivariateAgent()
        self.bivariate_agent = BivariateAgent()
        self.synthesizer_agent = SynthesizerAgent()
        self.code_execution_agent = CodeExecutionAgent()
        self.tools = {
            "call_summary_agent": (self.summary_agent.run, "Data Summary Agent"),
            "call_preprocessing_agent": (self.preprocessing_agent.run, "Preprocessing Agent"),
            "call_univariate_agent": (self.univariate_agent.run, "Univariate Analysis Agent"),
            "call_bivariate_agent": (self.bivariate_agent.run, "Bivariate Analysis Agent"),
            "call_code_execution_agent": (self.code_execution_agent.run, "Code Execution Agent"),
        }

    def run(self, state: AnalysisState, user_prompt: str, session_id: str, redis_state_client, redis_pubsub_client, is_initial_run: bool):
        channel = f"session-updates:{session_id}"
        ready_key = f"session-ready:{session_id}"
        
        try:
            if is_initial_run:
                print(f"Orchestrator for session {session_id} is waiting for initial frontend connection...")
                for _ in range(20):
                    if redis_state_client.exists(ready_key):
                        print("Frontend subscriber is ready. Starting orchestration.")
                        redis_state_client.delete(ready_key)
                        break
                    time.sleep(0.5)
                else:
                    print(f"Orchestrator for session {session_id} timed out waiting for frontend.")
                    redis_pubsub_client.publish(channel, json.dumps({"event": "error", "data": "Client connection timed out."}))
                    return

            state.add_log(f"Received new user prompt: '{user_prompt}'")
            conversation_history = [f"User's new request: {user_prompt}"]
            
            for i in range(10):
                print(f"\n================ Orchestrator Step {i+1} ================")
                state_summary = state.get_state_summary_for_llm()
                full_prompt = self.prompt_template + state_summary + "\n\nConversation History:\n" + "\n".join(conversation_history)
                response = self.llm.generate_content(full_prompt)
                try:
                    cleaned_response_text = response.text.strip().replace('```json', '').replace('```', '')
                    parsed_response = json.loads(cleaned_response_text)
                    thought, action = parsed_response.get("thought"), parsed_response.get("action")
                except Exception as e:
                    print(f"Error parsing Orchestrator LLM response: {response.text}\nError: {e}")
                    raise

                state.plan.append(f"Step {i+1}: {thought}")
                tool_name = action.get("tool_name")
                parameters = action.get("parameters", {})

                if tool_name == "finish":
                    print("Orchestrator Action: Plan complete. Synthesizing final report.")
                    redis_pubsub_client.publish(channel, json.dumps({"event": "status_update", "data": "Synthesizing final report..."}))
                    final_report = self.synthesizer_agent.run(state, user_prompt)
                    redis_pubsub_client.publish(channel, json.dumps({"event": "final_report", "data": final_report, "artifacts": state.artifacts}))
                    break

                if tool_name in self.tools:
                    tool_function, agent_name = self.tools[tool_name]
                    print(f"Orchestrator Action: Delegating to '{agent_name}'")
                    redis_pubsub_client.publish(channel, json.dumps({"event": "status_update", "data": f"Running {agent_name}..."}))
                    state = tool_function(state=state, **parameters)
                    observation = f"Successfully executed {agent_name}."
                else:
                    observation = f"Error: Agent '{tool_name}' not found."
                
                conversation_history.extend([f"Thought: {thought}", f"Action: Called {tool_name}", f"Observation: {observation}"])

        except Exception as e:
            print(f"An error occurred in orchestration for session {session_id}: {e}")
            error_message = f"An unexpected error occurred during analysis: {str(e)}"
            redis_pubsub_client.publish(channel, json.dumps({"event": "error", "data": error_message}))
        
        finally:
            redis_pubsub_client.publish(channel, json.dumps({"event": "end"}))
            print(f"--- Orchestration finished for session: '{session_id}' ---")
            redis_state_client.set(session_id, pickle.dumps(state), ex=3600)