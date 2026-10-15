import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.entities import ConversationModel
from app.schemas.research import (
    ConversationCreate,
    ConversationResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    req: ConversationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new research session/conversation."""
    conv = ConversationModel(
        title=req.title or "New Research Session",
        selected_doc_ids=req.selected_doc_ids or [],
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    """List all research sessions with their message history."""
    result = await db.execute(
        select(ConversationModel)
        .options(selectinload(ConversationModel.messages))
        .order_by(ConversationModel.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get single conversation and its full message history."""
    result = await db.execute(
        select(ConversationModel)
        .options(selectinload(ConversationModel.messages))
        .where(ConversationModel.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a research session and its associated messages."""
    result = await db.execute(select(ConversationModel).where(ConversationModel.id == conversation_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    await db.delete(conv)
    await db.commit()
