import uuid
from typing import List
from fastapi import APIRouter
from storage.postgres_store import (
    create_session, get_all_sessions, get_messages_for_session, 
    delete_session, get_docs_for_session, add_doc_to_session, 
    remove_doc_from_session
)

router = APIRouter()

@router.get("/sessions")
async def list_sessions():
    return get_all_sessions()

@router.post("/sessions")
async def start_session(title: str = "New Chat"):
    session_id = str(uuid.uuid4())
    create_session(session_id, title)
    return {"session_id": session_id}

@router.get("/sessions/{session_id}/messages")
async def list_messages(session_id: str):
    return get_messages_for_session(session_id)

@router.delete("/sessions/{session_id}")
async def remove_session(session_id: str):
    delete_session(session_id)
    return {"success": True}

@router.get("/sessions/{session_id}/documents")
async def list_session_docs(session_id: str):
    doc_ids = get_docs_for_session(session_id)
    return {"doc_ids": doc_ids}

@router.post("/sessions/{session_id}/documents/{doc_id}")
async def add_session_doc(session_id: str, doc_id: str):
    add_doc_to_session(session_id, doc_id)
    return {"success": True}

@router.post("/sessions/{session_id}/documents/bulk/add")
async def add_session_docs_bulk(session_id: str, doc_ids: List[str]):
    for doc_id in doc_ids:
        add_doc_to_session(session_id, doc_id)
    return {"success": True}

@router.delete("/sessions/{session_id}/documents/{doc_id}")
async def remove_session_doc(session_id: str, doc_id: str):
    remove_doc_from_session(session_id, doc_id)
    return {"success": True}

@router.post("/sessions/{session_id}/documents/bulk/remove")
async def remove_session_docs_bulk(session_id: str, doc_ids: List[str]):
    for doc_id in doc_ids:
        remove_doc_from_session(session_id, doc_id)
    return {"success": True}

@router.delete("/sessions/{session_id}/documents/bulk/clear")
async def clear_session_docs(session_id: str):
    current_docs = get_docs_for_session(session_id)
    for doc_id in current_docs:
        remove_doc_from_session(session_id, doc_id)
    return {"success": True}
