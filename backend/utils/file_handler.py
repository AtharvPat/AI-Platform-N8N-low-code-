# backend/utils/file_handler.py
import uuid
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import UploadFile
from config import config

class FileHandler:
    def __init__(self):
        self.upload_dir = config.UPLOAD_DIR
        self.allowed_extensions = config.ALLOWED_EXTENSIONS
        self.max_file_size = config.MAX_FILE_SIZE
        
    def save_upload_file(self, file: UploadFile) -> Dict[str, Any]:
        """Save uploaded file and return file info."""
        try:
            # Validate file extension
            file_extension = Path(file.filename).suffix.lower().lstrip('.')
            if file_extension not in self.allowed_extensions:
                raise ValueError(f"Unsupported file extension: {file_extension}")
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            filename = f"{file_id}_{file.filename}"
            file_path = self.upload_dir / filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Check file size
            if file_path.stat().st_size > self.max_file_size:
                file_path.unlink()  # Delete file
                raise ValueError(f"File size exceeds maximum allowed size: {self.max_file_size} bytes")
            
            return {
                "file_id": file_id,
                "filename": file.filename,
                "file_path": str(file_path),
                "size": file_path.stat().st_size
            }
            
        except Exception as e:
            raise Exception(f"File upload error: {str(e)}")
    
    def get_file_path(self, file_id: str) -> Optional[str]:
        """Get file path by file ID."""
        for file_path in self.upload_dir.glob(f"{file_id}_*"):
            if file_path.is_file():
                return str(file_path)
        return None
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old uploaded files."""
        import time
        current_time = time.time()
        
        for file_path in self.upload_dir.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > (max_age_hours * 3600):
                    file_path.unlink()
    
    def validate_csv_structure(self, file_path: str) -> Dict[str, Any]:
        """Validate CSV file structure and return metadata."""
        try:
            import pandas as pd
            
            # Try to read the file
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format")
            
            # Check required columns
            required_columns = ['PRODUCT_ID', 'PRODUCT_NAME', 'PRODUCT_DESCRIPTION']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Get file metadata
            metadata = {
                "row_count": len(df),
                "columns": list(df.columns),
                "file_size_mb": round(Path(file_path).stat().st_size / (1024 * 1024), 2),
                "sample_data": df.head(3).to_dict('records'),
                "has_required_columns": True,
                "missing_columns": [],
                "data_types": df.dtypes.to_dict()
            }
            
            return metadata
            
        except Exception as e:
            return {
                "error": str(e),
                "has_required_columns": False,
                "missing_columns": missing_columns if 'missing_columns' in locals() else [],
            }
    
    def get_file_stats(self) -> Dict[str, Any]:
        """Get statistics about uploaded files."""
        files = list(self.upload_dir.glob("*"))
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        
        return {
            "total_files": len([f for f in files if f.is_file()]),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "upload_dir": str(self.upload_dir),
            "max_file_size_mb": round(self.max_file_size / (1024 * 1024), 2),
            "allowed_extensions": self.allowed_extensions
        }