import json
from typing import List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import DATA_DIR, atomic_write_json

class DocumentItem(BaseModel):
    name: str = Field(description="Name of the required document or certificate")
    clause_reference: str = Field(description="Tender clause reference or page number")
    mandatory: bool = Field(description="True if mandatory, false if optional")
    description: str = Field(description="Details on issuing authority or validity")

class KeywordItem(BaseModel):
    keyword: str = Field(description="Key phrase or terminology")
    section: str = Field(description="Target section in the proposal letter")
    context: str = Field(description="Clause excerpt demonstrating usage")

class FormField(BaseModel):
    field_id: str = Field(description="Unique identifier for the form field")
    label: str = Field(description="Display label for the form field")
    input_type: str = Field(description="text, number, date, or file")
    required: bool = Field(description="True if the field is mandatory")
    description: str = Field(description="Helper text or description for the field")

class TenderAnalysisOutput(BaseModel):
    checklist: List[DocumentItem]
    keywords: List[KeywordItem]
    form_schema: List[FormField]

def run_llm_extraction(tender_id: str) -> dict:
    chunks_path = DATA_DIR / tender_id / "normalized_chunks.json"
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    clauses_text = "\n\n---\n\n".join([f"[{c['category']}] {c['text']}" for c in chunks])
    if len(clauses_text) > 100000:
        clauses_text = clauses_text[:100000] + "\n[TRUNCATED]"
        
    llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert tender bid director. Analyze the normalized tender clauses and extract: 1) Document checklist, 2) Proposal keywords, and 3) Client intake form schema. Ensure all outputs strictly follow the required JSON schema."),
        ("human", "TENDER CLAUSES:\n{clauses}")
    ])
    
    chain = prompt | llm.with_structured_output(TenderAnalysisOutput)
    result = chain.invoke({"clauses": clauses_text})
    result_dict = result.model_dump()
    
    tender_dir = DATA_DIR / tender_id
    atomic_write_json(tender_dir / "doc_checklist.json", result_dict["checklist"])
    atomic_write_json(tender_dir / "proposal_keywords.json", result_dict["keywords"])
    atomic_write_json(tender_dir / "client_form_schema.json", result_dict["form_schema"])
    
    return result_dict