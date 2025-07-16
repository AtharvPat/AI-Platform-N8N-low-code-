# backend/agents/output_agent.py
import json
import csv
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from models.schemas import AgentState
from config import config

class OutputAgent:
    def __init__(self):
        self.output_dir = config.OUTPUT_DIR
    
    def generate_output(self, state: AgentState) -> AgentState:
        """Generate output files and final results."""
        if state.error or not state.results:
            return state
        
        try:
            # Generate output filename
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            task_name = state.task_config.task.value if state.task_config else "processed"
            output_filename = f"{task_name}_{timestamp}.csv"
            output_path = self.output_dir / output_filename
            
            # Prepare data for CSV export
            csv_data = self._prepare_csv_data(state.results)
            
            # Write CSV file
            self._write_csv(csv_data, output_path)
            
            # Generate summary
            summary = self._generate_summary(state.results)
            
            return AgentState(
                file_path=state.file_path,
                data=state.data,
                processed_data=state.processed_data,
                task_config=state.task_config,
                results=state.results,
                metadata={
                    **state.metadata,
                    "output_file": str(output_path),
                    "summary": summary,
                    "export_timestamp": timestamp
                }
            )
            
        except Exception as e:
            return AgentState(
                **state.dict(),
                error=f"Output generation error: {str(e)}"
            )
    
    def _prepare_csv_data(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare data for CSV export."""
        csv_data = []
        
        for result in results:
            row = {}
            
            # Add original product data
            for key, value in result.items():
                if key not in ['llm_result', 'error']:
                    row[key] = value
            
            # Add LLM results
            if result.get('llm_result'):
                llm_data = result['llm_result']
                if isinstance(llm_data, dict):
                    # Flatten nested results
                    for key, value in llm_data.items():
                        if isinstance(value, list):
                            row[f"llm_{key}"] = json.dumps(value)
                        else:
                            row[f"llm_{key}"] = value
                else:
                    row['llm_result'] = str(llm_data)
            
            # Add error information
            if result.get('error'):
                row['processing_error'] = result['error']
            
            csv_data.append(row)
        
        return csv_data
    
    def _write_csv(self, data: List[Dict[str, Any]], output_path: Path):
        """Write data to CSV file."""
        if not data:
            return
        
        fieldnames = list(data[0].keys())
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate processing summary."""
        total_items = len(results)
        successful_items = sum(1 for r in results if r.get('llm_result') and not r.get('error'))
        failed_items = total_items - successful_items
        
        return {
            "total_processed": total_items,
            "successful": successful_items,
            "failed": failed_items,
            "success_rate": (successful_items / total_items * 100) if total_items > 0 else 0
        }