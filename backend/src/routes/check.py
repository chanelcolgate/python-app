from typing import List, Any, Union, Dict, Optional
import io

from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Query,
    Body,
    Depends,
    UploadFile,
    File,
)
from tortoise.exceptions import IntegrityError, DoesNotExist
import pandas as pd
import numpy as np

from src.models.check import CheckPublic, CheckCreate, CheckUpdate
from src.models.image_display import Checks
from src.settings import settings

check_router = APIRouter(tags=["Check"])


async def get_checks_or_404(id: str) -> Checks:
    try:
        checks = await Checks.get(id=id)
        return checks
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@check_router.get("/", response_model=List[CheckPublic])
async def retrieve_all_checks() -> List[CheckPublic]:
    checks = await Checks.all()
    return [CheckPublic.from_orm(check) for check in checks]


@check_router.get("/{id}", response_model=CheckPublic)
async def retrieve_check(
    checks: Checks = Depends(get_checks_or_404),
) -> CheckPublic:
    return CheckPublic.from_orm(checks)


@check_router.post("/new", status_code=status.HTTP_201_CREATED)
async def create_check(body: CheckCreate = Body(...)) -> dict:
    check_obj = await Checks.create(**body.dict(exclude_unset=True))
    return {"message": "Check created successuflly"}


@check_router.post("/uploadfile")
async def upload_file(file: UploadFile = File(...)) -> list:
    # Check if the uploaded file is an Excel file
    if not file.filename.endswith(".xlsx"):
        # return {"error": "Only Excel file (.xlsx) are supported"}
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only Excel file (.xlsx) are supported",
        )

    # Read the Excel file
    try:
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        data = []
        for index, row in df.iterrows():
            item = {}
            item["id"] = row["Ký hiệu bộ trưng bày"]
            item["name"] = row["Bộ trưng bày"]
            item["matrix"] = {
                key: value
                for key, value in row.items()
                if key not in ["Bộ trưng bày", "Ký hiệu bộ trưng bày"]
                if not np.isnan(value)
            }
            data.append(item)
        for elem in data:
            try:
                check_obj = await Checks.create(**elem)
            except IntegrityError:
                check = await get_checks_or_404(elem["id"])
                check_update = CheckUpdate(
                    name=elem["name"], matrix=elem["matrix"]
                )
                check.update_from_dict(check_update.dict(exclude_unset=True))
                await check.save()
        return data
    except Exception as e:
        return {
            "error": f"An error occurred while reading the Excel file: {str(e)}"
        }


@check_router.put("/edit/{id}")
async def update_check(
    checks_update: CheckUpdate, checks: Checks = Depends(get_checks_or_404)
) -> dict:
    checks.update_from_dict(checks_update.dict(exclude_unset=True))
    await checks.save()
    return CheckPublic.from_orm(checks).dict()


@check_router.delete("/{id}")
async def delete_checks(id: str) -> dict:
    try:
        checks = await Checks.filter(id=id).delete()
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Checks {id} does not exist",
        )
    return {"message": "Deleted images filtered with id"}
