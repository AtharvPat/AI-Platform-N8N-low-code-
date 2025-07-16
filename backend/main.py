# backend/main.py
import uvicorn
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Dict, Any, List
import uuid
from pathlib import Path

from config import config
from models.schemas import (
    FileUploadResponse, ProcessingRequest, ProcessingResult,
    TaskType, ProcessingMode, LLMModel
)
from graph.workflow import HGWorkflow
from utils.file_handler import FileHandler
from agents.csv_loader_agent import CSVLoaderAgent

# Initialize FastAPI app
app = FastAPI(
    title="HG AI Platform API",
    description="Backend API for the HG AI Platform PoC",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
file_handler = FileHandler()
workflow = HGWorkflow()
csv_loader = CSVLoaderAgent()

# In-memory storage for demo (use Redis/Database in production)
processing_jobs: Dict[str, Dict[str, Any]] = {}
uploaded_files: Dict[str, Dict[str, Any]] = {}

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "HG AI Platform API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "openai_configured": bool(config.OPENAI_API_KEY),
        "upload_dir": str(config.UPLOAD_DIR),
        "output_dir": str(config.OUTPUT_DIR)
    }

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a CSV/Excel file."""
    try:
        # Save uploaded file
        file_info = file_handler.save_upload_file(file)
        file_id = file_info["file_id"]
        file_path = file_info["file_path"]
        
        # Load and preview the file
        state = csv_loader.load_file(file_path)
        
        if state.error:
            raise HTTPException(status_code=400, detail=state.error)
        
        # Store file info
        uploaded_files[file_id] = {
            **file_info,
            "columns": state.metadata["columns"],
            "row_count": state.metadata["row_count"]
        }
        
        # Generate sample data (first 5 rows)
        sample_data = state.data[:5] if state.data else []
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            row_count=state.metadata["row_count"],
            columns=state.metadata["columns"],
            sample_data=sample_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{file_id}")
async def get_file_info(file_id: str):
    """Get information about an uploaded file."""
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    return uploaded_files[file_id]

@app.post("/process", response_model=ProcessingResult)
async def process_file(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """Process a file with the specified configuration."""
    try:
        # Validate file exists
        if request.file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = uploaded_files[request.file_id]
        file_path = file_info["file_path"]
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        processing_jobs[job_id] = {
            "status": "processing",
            "progress": 0,
            "total_count": 0,
            "processed_count": 0,
            "error": None,
            "results": None,
            "output_file_path": None
        }
        
        # Start background processing
        background_tasks.add_task(run_processing_workflow, job_id, file_path, request)
        
        return ProcessingResult(
            job_id=job_id,
            status="processing",
            processed_count=0,
            total_count=0,
            results=[]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}", response_model=ProcessingResult)
async def get_job_status(job_id: str):
    """Get the status of a processing job."""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    
    return ProcessingResult(
        job_id=job_id,
        status=job["status"],
        processed_count=job["processed_count"],
        total_count=job["total_count"],
        results=job["results"] or [],
        output_file_path=job["output_file_path"],
        error_message=job["error"]
    )

@app.get("/download/{job_id}")
async def download_results(job_id: str):
    """Download the results file for a completed job."""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    
    if job["status"] != "completed" or not job["output_file_path"]:
        raise HTTPException(status_code=400, detail="Job not completed or no output file")
    
    output_path = Path(job["output_file_path"])
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        path=output_path,
        filename=output_path.name,
        media_type="text/csv"
    )

@app.get("/tasks")
async def get_available_tasks():
    """Get list of available processing tasks."""
    return {
        "tasks": [
            {"id": task.value, "name": task.value.replace("_", " ").title()} 
            for task in TaskType
        ],
        "modes": [
            {"id": mode.value, "name": mode.value.replace("_", " ").title()} 
            for mode in ProcessingMode
        ],
        "models": [
            {"id": model.value, "name": model.value} 
            for model in LLMModel
        ]
    }

# backend/main.py - FIXED VERSION (update the background task function)

# Find this function in your main.py and replace it:

async def run_processing_workflow(job_id: str, file_path: str, request: ProcessingRequest):
    """Background task to run the processing workflow - FIXED VERSION."""
    try:
        print(f"🚀 Starting background job {job_id}")
        
        # Update job status
        processing_jobs[job_id]["status"] = "processing"
        
        # Run the workflow SYNCHRONOUSLY (this fixes the event loop issue)
        result = workflow.run_workflow_sync(file_path, request)
        
        if result.error:
            print(f"❌ Job {job_id} failed: {result.error}")
            processing_jobs[job_id]["status"] = "failed"
            processing_jobs[job_id]["error"] = result.error
        else:
            print(f"✅ Job {job_id} completed successfully")
            processing_jobs[job_id]["status"] = "completed"
            processing_jobs[job_id]["results"] = result.results
            processing_jobs[job_id]["total_count"] = len(result.processed_data or [])
            processing_jobs[job_id]["processed_count"] = len(result.results or [])
            processing_jobs[job_id]["output_file_path"] = result.metadata.get("output_file")
            
    except Exception as e:
        error_msg = f"Background task error: {str(e)}"
        print(f"❌ Job {job_id} failed with exception: {error_msg}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = error_msg

@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    print(f"Starting HG AI Platform API on {config.API_HOST}:{config.API_PORT}")
    print(f"Upload directory: {config.UPLOAD_DIR}")
    print(f"Output directory: {config.OUTPUT_DIR}")
    print(f"OpenAI API configured: {bool(config.OPENAI_API_KEY)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG
    )
    
@app.post("/process-debug")
async def process_file_debug(request_data: dict):
    """Debug endpoint to see what data is being received."""
    print("🔍 DEBUG: Received raw data:")
    print(request_data)
    
    try:
        # Try to create ProcessingRequest from the data
        processing_request = ProcessingRequest(**request_data)
        print("✅ Successfully parsed as ProcessingRequest")
        print(f"   file_id: {processing_request.file_id}")
        print(f"   task: {processing_request.task}")
        print(f"   mode: {processing_request.mode}")
        print(f"   llm_model: {processing_request.llm_model}")
        print(f"   batch_size: {processing_request.batch_size}")
        print(f"   row_range: {processing_request.row_range}")
        
        return {"status": "debug_success", "parsed_data": processing_request.dict()}
        
    except Exception as e:
        print(f"❌ Failed to parse data: {str(e)}")
        return {"status": "debug_failed", "error": str(e), "received_data": request_data}

# Also update the main process endpoint to be more robust:
@app.post("/process", response_model=ProcessingResult)
async def process_file(request_data: dict, background_tasks: BackgroundTasks):
    """Process a file with the specified configuration."""
    try:
        print("🔍 Processing request data:")
        print(request_data)
        
        # Create ProcessingRequest with validation
        try:
            # Ensure all required fields are present with defaults
            processed_data = {
                "file_id": request_data.get("file_id"),
                "task": request_data.get("task", "attribute_extraction"),
                "mode": request_data.get("mode", "batch"),
                "llm_model": request_data.get("llm_model", "gpt-3.5-turbo"),
                "batch_size": request_data.get("batch_size", 5),
            }
            
            # Add row_range if provided
            if "row_range" in request_data:
                processed_data["row_range"] = request_data["row_range"]
                
            print("✅ Processed data:", processed_data)
            
            request = ProcessingRequest(**processed_data)
            print("✅ Successfully created ProcessingRequest")
            
        except Exception as validation_error:
            print(f"❌ Validation error: {str(validation_error)}")
            raise HTTPException(
                status_code=422, 
                detail=f"Invalid request data: {str(validation_error)}"
            )
        
        # Validate file exists
        if request.file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = uploaded_files[request.file_id]
        file_path = file_info["file_path"]
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        processing_jobs[job_id] = {
            "status": "processing",
            "progress": 0,
            "total_count": 0,
            "processed_count": 0,
            "error": None,
            "results": None,
            "output_file_path": None
        }
        
        # Start background processing
        background_tasks.add_task(run_processing_workflow, job_id, file_path, request)
        
        return ProcessingResult(
            job_id=job_id,
            status="processing",
            processed_count=0,
            total_count=0,
            results=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))