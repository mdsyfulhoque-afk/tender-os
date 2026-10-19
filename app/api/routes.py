import json
from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
from app.config import DATA_DIR, atomic_write_json
from app.services.ingestion import ingest_files
from app.services.extraction import extract_pdf
from app.services.nlp_chunker import process_chunks
from app.services.llm_pipeline import run_llm_extraction
from app.services.excel_exporter import generate_excel
from app.services.proposal_generator import generate_proposal

api_bp = Blueprint('api', __name__, url_prefix='/api/v3')

@api_bp.route('/tenders/upload', methods=['POST'])
def upload_tenders():
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400
        
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({"error": "No selected files"}), 400
        
    tender_id = ingest_files(files)
    return jsonify({"tender_id": tender_id, "status": "uploaded"}), 200

@api_bp.route('/tenders/<tender_id>/process', methods=['POST'])
def process_tender(tender_id):
    tender_dir = DATA_DIR / tender_id
    if not tender_dir.exists():
        return jsonify({"error": "Tender not found"}), 404
        
    manifest_path = tender_dir / "tender_manifest.json"
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    all_pages = []
    for file_info in manifest["files"]:
        if file_info["filename"].lower().endswith(".pdf"):
            pages = extract_pdf(file_info["path"], tender_id)
            all_pages.extend(pages)
            
    chunks = process_chunks(all_pages, tender_id)
    run_llm_extraction(tender_id)
    generate_excel(tender_id)
    
    return jsonify({"status": "processed", "chunks_count": len(chunks)}), 200

@api_bp.route('/tenders/<tender_id>/data', methods=['GET'])
def get_tender_data(tender_id):
    tender_dir = DATA_DIR / tender_id
    if not tender_dir.exists():
        return jsonify({"error": "Tender not found"}), 404
        
    data = {}
    for fname in ["doc_checklist.json", "proposal_keywords.json", "client_form_schema.json"]:
        fpath = tender_dir / fname
        if fpath.exists():
            with open(fpath, "r", encoding="utf-8") as f:
                data[fname.replace(".json", "")] = json.load(f)
                
    return jsonify(data), 200

@api_bp.route('/tenders/<tender_id>/download/excel', methods=['GET'])
def download_excel(tender_id):
    fpath = DATA_DIR / tender_id / "tender_requirements.xlsx"
    if not fpath.exists():
        return jsonify({"error": "Excel not found"}), 404
    return send_file(fpath, as_attachment=True, download_name="tender_requirements.xlsx")

@api_bp.route('/tenders/<tender_id>/submit-form', methods=['POST'])
def submit_form(tender_id):
    tender_dir = DATA_DIR / tender_id
    if not tender_dir.exists():
        return jsonify({"error": "Tender not found"}), 404
        
    submission = request.json
    out_path = tender_dir / "client_submission.json"
    atomic_write_json(out_path, submission)
    
    generate_proposal(tender_id)
    return jsonify({"status": "success", "message": "Proposal generated"}), 200

@api_bp.route('/tenders/<tender_id>/download/proposal', methods=['GET'])
def download_proposal(tender_id):
    fpath = DATA_DIR / tender_id / "generated_proposal.docx"
    if not fpath.exists():
        return jsonify({"error": "Proposal not found"}), 404
    return send_file(fpath, as_attachment=True, download_name="generated_proposal.docx")