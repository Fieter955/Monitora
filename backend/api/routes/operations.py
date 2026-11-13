from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.user import User
from schemas.operations import ProblemLocatorRead
from services.operations import list_problems as list_problems_svc

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/problems", response_model=list[ProblemLocatorRead])
def list_problems(
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ProblemLocatorRead]:
    return list_problems_svc(db)[offset : offset + limit]
