from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Generation
from app.schemas import HistoryItem

router = APIRouter()


@router.get("/history", response_model=list[HistoryItem])
def get_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * page_size
    generations = (
        db.query(Generation)
        .options(joinedload(Generation.posts))
        .order_by(Generation.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return generations


@router.delete("/history/{generation_id}", status_code=204)
def delete_generation(generation_id: str, db: Session = Depends(get_db)):
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if generation:
        db.delete(generation)
        db.commit()
