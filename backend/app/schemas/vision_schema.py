# app/schemas/vision_schema.py

from typing import List, Optional
from pydantic import BaseModel, Field

class NodeConnection(BaseModel):
    source: str = Field(description="Origin node or component name")
    target: str = Field(description="Destination node or target component")
    label: Optional[str] = Field(None, description="Label on the arrow or relation type")

class VisionAnalysisOutput(BaseModel):
    image_type: str = Field(description="Category: chart, architecture_diagram, flowchart, table, or other")
    title_or_caption: Optional[str] = Field(None, description="Title visible on the image")
    summary: str = Field(description="High-level 2-sentence description of the visual artifact")
    key_entities: List[str] = Field(default_factory=list, description="Important entities, systems, or labels")
    structural_relationships: List[NodeConnection] = Field(
        default_factory=list, 
        description="Graph nodes and data flows (if flowchart/architecture)"
    )
    raw_markdown_representation: str = Field(
        description="Markdown representation (e.g. Markdown table or bullet points of key trends)"
    )
    confidence_score: float = Field(description="Model confidence from 0.0 to 1.0 based on clarity")