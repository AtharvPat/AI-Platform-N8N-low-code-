# backend/graph/workflow.py - FIXED VERSION
from typing import Dict, Any
from models.schemas import AgentState, ProcessingRequest
from agents.csv_loader_agent import CSVLoaderAgent
from agents.preprocessor_agent import PreprocessorAgent
from agents.llm_agent import LLMAgent
from agents.output_agent import OutputAgent

class HGWorkflow:
    """Fixed workflow without asyncio conflicts."""
    
    def __init__(self):
        self.csv_loader = CSVLoaderAgent()
        self.preprocessor = PreprocessorAgent()
        self.llm_agent = LLMAgent()
        self.output_agent = OutputAgent()
    
    def run_workflow_sync(self, file_path: str, config: ProcessingRequest) -> AgentState:
        """Run workflow synchronously without asyncio issues."""
        try:
            print(f"🚀 Starting workflow for file: {file_path}")
            
            # Step 1: Load CSV
            print("📁 Step 1: Loading CSV...")
            state = AgentState(file_path=file_path, task_config=config)
            state = self.csv_loader.load_file(state.file_path)
            
            if state.error:
                print(f"❌ CSV Loading failed: {state.error}")
                return state
            
            print(f"✅ CSV loaded: {len(state.data)} rows")
            
            # Step 2: Preprocess data
            print("🔄 Step 2: Preprocessing data...")
            state.task_config = config
            state = self.preprocessor.preprocess(state)
            
            if state.error:
                print(f"❌ Preprocessing failed: {state.error}")
                return state
            
            print(f"✅ Data preprocessed: {len(state.processed_data)} rows to process")
            
            # Step 3: LLM processing (FIXED - no asyncio)
            print("🤖 Step 3: AI processing...")
            state = self.llm_agent.process_batch_sync(state)  # Use sync version
            
            if state.error:
                print(f"❌ AI processing failed: {state.error}")
                return state
            
            print(f"✅ AI processing completed: {len(state.results)} results")
            
            # Step 4: Generate output
            print("💾 Step 4: Generating output...")
            state = self.output_agent.generate_output(state)
            
            if state.error:
                print(f"❌ Output generation failed: {state.error}")
                return state
            
            print("✅ Workflow completed successfully!")
            return state
            
        except Exception as e:
            error_msg = f"Workflow error: {str(e)}"
            print(f"❌ {error_msg}")
            return AgentState(
                file_path=file_path,
                task_config=config,
                error=error_msg
            )