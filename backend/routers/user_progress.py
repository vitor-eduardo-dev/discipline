from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from services.level_engine import level_progress

router = APIRouter(prefix="/users", tags=["User Progress"])

@router.get("/me/progress")
def get_my_progress(db: Session = Depends(get_db)):
    user = db.query(User).first()

    data = level_progress(user.xp)

    return {
        "name": user.name,
        "xp": user.xp,
        "level": data["level"],
        "next_level_xp": data["next_level_xp"],
        "progress_percent": data["progress_percent"]
    }
