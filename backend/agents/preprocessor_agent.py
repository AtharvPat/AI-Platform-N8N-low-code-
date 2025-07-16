# backend/agents/preprocessor_agent.py
import pandas as pd
from typing import List, Dict, Any, Optional
from models.schemas import AgentState, ProcessingRequest, ProcessingMode

class PreprocessorAgent:
    def __init__(self):
        pass
    
    def preprocess(self, state: AgentState) -> AgentState:
        """Preprocess data based on task configuration."""
        if state.error or not state.data:
            return state
        
        try:
            # Create product ID index for faster lookups
            product_index = {str(row['PRODUCT_ID']): idx for idx, row in enumerate(state.data)}
            
            # Filter data based on processing mode
            if state.task_config:
                filtered_data = self._filter_data(state.data, state.task_config, product_index)
            else:
                filtered_data = state.data
            
            # Clean and normalize data
            processed_data = self._clean_data(filtered_data)
            
            return AgentState(
                file_path=state.file_path,
                data=state.data,
                processed_data=processed_data,
                task_config=state.task_config,
                metadata={
                    **state.metadata,
                    "product_index": product_index,
                    "processed_count": len(processed_data),
                    "original_count": len(state.data)
                }
            )
            
        except Exception as e:
            return AgentState(
                **state.dict(),
                error=f"Preprocessing error: {str(e)}"
            )
    
    def _filter_data(self, data: List[Dict[str, Any]], config: ProcessingRequest, 
                    product_index: Dict[str, int]) -> List[Dict[str, Any]]:
        """Filter data based on processing configuration."""
        
        if config.mode == ProcessingMode.PRODUCT_ID_LOOKUP and config.product_ids:
            # Filter by specific product IDs
            filtered_data = []
            for product_id in config.product_ids:
                if product_id in product_index:
                    filtered_data.append(data[product_index[product_id]])
            return filtered_data
        
        elif config.row_range:
            # Filter by row range
            start = config.row_range.get("start", 0)
            end = config.row_range.get("end", len(data))
            return data[start:end]
        
        return data
    
    def _clean_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and normalize data."""
        cleaned_data = []
        
        for row in data:
            cleaned_row = {}
            for key, value in row.items():
                # Handle NaN values
                if pd.isna(value):
                    cleaned_row[key] = ""
                else:
                    cleaned_row[key] = str(value).strip()
            cleaned_data.append(cleaned_row)
        
        return cleaned_data