from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.user import User
from services.reports import generate_status_csv

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/status.csv")
def status_report(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Response:
    content, filename = generate_status_csv(db)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
