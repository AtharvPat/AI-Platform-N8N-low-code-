# backend/agents/csv_loader_agent.py
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from models.schemas import AgentState

class CSVLoaderAgent:
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx']
    
    def load_file(self, file_path: str) -> AgentState:
        """Load and parse CSV/Excel file."""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return AgentState(error=f"File not found: {file_path}")
            
            if path.suffix.lower() == '.csv':
                df = pd.read_csv(path)
            elif path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(path)
            else:
                return AgentState(error=f"Unsupported file format: {path.suffix}")
            
            # Convert to list of dictionaries
            data = df.to_dict('records')
            
            # Validate required columns
            required_columns = ['PRODUCT_ID', 'PRODUCT_NAME', 'PRODUCT_DESCRIPTION']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return AgentState(error=f"Missing required columns: {missing_columns}")
            
            return AgentState(
                file_path=file_path,
                data=data,
                metadata={
                    "row_count": len(data),
                    "columns": list(df.columns),
                    "file_size": path.stat().st_size
                }
            )
            
        except Exception as e:
            return AgentState(error=f"Error loading file: {str(e)}")
