from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class TaskType(str, Enum):
    ATTRIBUTE_EXTRACTION = "attribute_extraction"
    SALES_FAQ = "sales_faq"
    DATA_QA = "data_qa"
    CONTENT_ENRICHMENT = "content_enrichment"
    CATEGORY_CLASSIFICATION = "category_classification"

class ProcessingMode(str, Enum):
    BATCH = "batch"
    PRODUCT_ID_LOOKUP = "product_id_lookup"

class LLMModel(str, Enum):
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    row_count: int
    columns: List[str]
    sample_data: List[Dict[str, Any]]

class ProcessingRequest(BaseModel):
    file_id: str
    task: TaskType
    mode: ProcessingMode
    llm_model: LLMModel = LLMModel.GPT_35_TURBO
    batch_size: Optional[int] = Field(default=10, ge=1, le=100)
    product_ids: Optional[List[str]] = None
    row_range: Optional[Dict[str, int]] = None  # {"start": 0, "end": 100}
    custom_prompt: Optional[str] = None
    # Optional workflow graph coming from frontend (nodes + edges + configs)
    workflow: Optional[Dict[str, Any]] = None

class ProcessingResult(BaseModel):
    job_id: str
    status: str
    processed_count: int
    total_count: int
    results: List[Dict[str, Any]]
    output_file_path: Optional[str] = None
    error_message: Optional[str] = None

class AgentState(BaseModel):
    file_path: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    processed_data: Optional[List[Dict[str, Any]]] = None
    task_config: Optional[ProcessingRequest] = None
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class NodeConfig(BaseModel):
    node_id: str
    node_type: str
    config: Dict[str, Any]
    position: Dict[str, float]

class WorkflowState(BaseModel):
    nodes: List[NodeConfig]
    edges: List[Dict[str, str]]
    file_id: Optional[str] = None
    current_state: AgentState = Field(default_factory=AgentState)