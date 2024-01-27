from typing import List, Any, Union, Dict, Optional

from fastapi import APIRouter, HTTPException, status, Query, Body, Depends

from src.models.check import CheckPublic, CheckCreate, CheckUpdate, Checks
from src.settings import Settings

settings = Settings()

check_router = APIRouter(tags=["Check"])


async def get_checks_or_404(id: int) -> Checks:
    try:
        checks = await Checks.get(id=id)
        return checks
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


if settings.DEBUG:

    @check_router.get("/", response_model=Union[List[CheckPublic], list])
    async def retrieve_all_checks() -> Union[List[CheckPublic], list]:
        checks = await Checks.all()
        return [CheckPublic.from_orm(check).dict() for check in checks]

    @check_router.get("/{id}", response_model=dict)
    async def retrieve_check(
        checks: Checks = Depends(get_checks_or_404),
    ) -> dict:
        return CheckPublic.from_orm(checks).dict()

    @check_router.post("/new")
    async def create_check(body: CheckCreate = Body(...)) -> dict:
        check_obj = await Checks.create(**body.dict(exclude_unset=True))
        return {"message": "Check created successuflly"}

    @check_router.put("/edit/{id}")
    async def update_check(
        checks_update: CheckUpdate, checks: Checks = Depends(get_checks_or_404)
    ) -> dict:
        checks.update_from_dict(checks_update.dict(exclude_unset=True))
        await checks.save()
        return CheckPublic.from_orm(checks).dict()
