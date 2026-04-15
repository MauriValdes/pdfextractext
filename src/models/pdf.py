# src/models/pdf.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class DocumentMetadata(BaseModel):
    filename: str
    page_count: int
    file_size: int 
    author: Optional[str] = "Desconocido"

class ProcessResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_hash: str
    status: str = "processing" 
    raw_text: Optional[str] = None  
    summary_text: Optional[str] = None 
    ai_model: Optional[str] = None  
    processed_at: datetime = Field(default_factory=datetime.now)
    metadata: DocumentMetadata