"""
Session snapshot and content management for Notiq.
Handles serialization, data packing, and session state utilities.
"""
import base64
from datetime import datetime
from typing import Dict, List


def get_session_snapshot(doc: str, images: List[Dict], pdfs: List[Dict], subject: str = "General") -> Dict:
    """
    Return a normalized dict of the current note, with attachments base64-encoded.
    
    Args:
        doc: The main document content
        images: List of image dicts with 'name', 'mime', 'bytes', 'caption'
        pdfs: List of PDF dicts with 'name', 'mime', 'bytes', 'caption'
        subject: Subject/topic of the note
        
    Returns:
        Normalized snapshot dict ready for Gemini processing
    """
    def _pack(items):
        return [
            {
                "name": it["name"],
                "mime": it["mime"],
                "caption": it.get("caption", ""),
                "data_b64": base64.b64encode(it["bytes"]).decode("ascii"),
            }
            for it in items
        ]

    images_packed = _pack(images)
    pdfs_packed = _pack(pdfs)

    return {
        "subject": subject,
        "content": doc,
        "images": images_packed,
        "pdfs": pdfs_packed,
        "saved_at": datetime.now().isoformat(),
    }


def serialize_for_save(doc: str, images: List[Dict], pdfs: List[Dict], subject: str) -> Dict:
    """
    Serialize session for JSON save (includes base64-encoded attachments).
    """
    return get_session_snapshot(doc, images, pdfs, subject)


def pack_for_download(doc: str, images: List[Dict], pdfs: List[Dict], subject: str, as_json: bool) -> tuple:
    """
    Pack content for download.
    
    Returns:
        (content_string, mime_type, filename)
    """
    if as_json:
        import json
        payload = serialize_for_save(doc, images, pdfs, subject)
        content_str = json.dumps(payload, ensure_ascii=False, indent=2)
        return content_str, "application/json", f"{subject or 'notes'}.json"
    else:
        return doc, "text/markdown", f"{subject or 'notes'}.md"
