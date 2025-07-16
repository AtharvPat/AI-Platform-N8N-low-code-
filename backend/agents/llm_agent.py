# backend/agents/llm_agent.py - FIXED VERSION
import json
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI
from models.schemas import AgentState, LLMModel
from agents.prompts import get_system_prompt, get_user_prompt
from config import config

class LLMAgent:
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model_mapping = {
            LLMModel.GPT_35_TURBO: "gpt-3.5-turbo",
            LLMModel.GPT_4O_MINI: "gpt-4o-mini",
            LLMModel.GPT_4O: "gpt-4o"
        }
    
    def process_batch_sync(self, state: AgentState) -> AgentState:
        """Process data synchronously (FIXED - no async issues)."""
        if state.error or not state.processed_data or not state.task_config:
            return state
        
        try:
            print(f"🤖 Processing {len(state.processed_data)} items with {state.task_config.llm_model}")
            
            results = []
            batch_size = state.task_config.batch_size or 10
            data = state.processed_data
            
            # Process in batches
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                print(f"📦 Processing batch {i//batch_size + 1}: {len(batch)} items")
                
                batch_results = self._process_batch_sync(batch, state.task_config)
                results.extend(batch_results)
                
                # Add small delay between batches to avoid rate limits
                if i + batch_size < len(data):
                    time.sleep(1)
            
            return AgentState(
                file_path=state.file_path,
                data=state.data,
                processed_data=state.processed_data,
                task_config=state.task_config,
                results=results,
                metadata={
                    **state.metadata,
                    "llm_model": state.task_config.llm_model,
                    "task_type": state.task_config.task,
                    "results_count": len(results)
                }
            )
            
        except Exception as e:
            error_msg = f"LLM processing error: {str(e)}"
            print(f"❌ {error_msg}")
            return AgentState(
                **state.dict(),
                error=error_msg
            )
    
    def _process_batch_sync(self, batch: List[Dict[str, Any]], config) -> List[Dict[str, Any]]:
        """Process a single batch synchronously."""
        system_prompt = get_system_prompt(config.task.value)
        model_name = self.model_mapping[config.llm_model]
        
        processed_results = []
        
        for i, item in enumerate(batch):
            print(f"  🔄 Processing item {i+1}/{len(batch)}: {item.get('PRODUCT_NAME', 'Unknown')}")
            
            try:
                result = self._process_single_item_sync(item, system_prompt, model_name)
                processed_results.append({
                    **item,
                    "llm_result": result,
                    "error": None
                })
                print(f"  ✅ Item {i+1} completed")
                
            except Exception as e:
                error_msg = f"Item processing error: {str(e)}"
                print(f"  ❌ Item {i+1} failed: {error_msg}")
                processed_results.append({
                    **item,
                    "llm_result": None,
                    "error": error_msg
                })
        
        return processed_results
    
    def _process_single_item_sync(self, item: Dict[str, Any], system_prompt: str, model_name: str) -> Dict[str, Any]:
        """Process a single item synchronously."""
        user_prompt = get_user_prompt(item)
        
        try:
            # Make synchronous API call
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Try to parse JSON response
            try:
                parsed_result = json.loads(content)
                return parsed_result
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw content
                return {"raw_response": content}
                
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    # Keep the async version for backwards compatibility (but don't use it)
    async def process_batch(self, state: AgentState) -> AgentState:
        """Async version - DON'T USE THIS (causes event loop issues)."""
        return self.process_batch_sync(state)