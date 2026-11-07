from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.user import User
from schemas.operations import ProblemLocatorRead
from services.operations import list_problems as list_problems_svc

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/problems", response_model=list[ProblemLocatorRead])
def list_problems(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ProblemLocatorRead]:
    return list_problems_svc(db)
