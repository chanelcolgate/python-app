import io
import re
from typing import List, Any, Union, Dict, Optional

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
from src.utils import api_token
import src.excel as excel

check_router = APIRouter(tags=["Check"])


async def get_checks_or_404(id: str) -> Checks:
    try:
        checks = await Checks.get(id=id)
        return checks
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, result="fail"
        )


# @check_router.get(
#     "",
#     response_model=List[CheckPublic],
#     dependencies=[Depends(api_token)],
# )
# async def retrieve_all_checks() -> List[CheckPublic]:
#     key = settings.API_KEY.get("api_key")
#     checks = await Checks.all()
#     return [CheckPublic.from_orm(check) for check in checks]
#
#
# @check_router.get(
#     "/{id}", response_model=CheckPublic, dependencies=[Depends(api_token)]
# )
# async def retrieve_check(
#     checks: Checks = Depends(get_checks_or_404),
# ) -> CheckPublic:
#     return CheckPublic.from_orm(checks)
#
#
# @check_router.post(
#     "/new",
#     status_code=status.HTTP_201_CREATED,
#     dependencies=[Depends(api_token)],
# )
# async def create_check(body: CheckCreate = Body(...)) -> dict:
#     check_obj = await Checks.create(**body.dict(exclude_unset=True))
#     return {"message": "Check created successuflly"}


@check_router.post("/uploadfile", dependencies=[Depends(api_token)])
async def upload_file(file: UploadFile = File(...)) -> list:
    # Check if the uploaded file is an Excel file
    if not file.filename.endswith(".xlsx"):
        # return {"error": "Only Excel file (.xlsx) are supported"}
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only Excel file (.xlsx) are supported",
            result="fail",
        )

    # Read the Excel file
    try:
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        headers = df.columns.tolist()
        labels = [
            i
            for i in headers
            if i
            not in [
                "Các loại Bộ TB",
                "Ký hiệu bộ trưng bày (Mới)",
                "Ký hiệu bộ trưng bày",
                "Giải Thích Ký Hiệu",
                "Tổng Face Min SU",
            ]
        ]

        data = []
        prog_code_pattern = re.compile(r"(?P<a>[&$]\d{2})\*(?P<b>\d{2})")
        for index, row in df.iterrows():
            item = {}
            prog_code_matches = row["Ký hiệu bộ trưng bày (Mới)"].split("_")
            item["id"] = prog_code_matches[0]
            item["name"] = row["Giải Thích Ký Hiệu"]
            item["transform"] = True
            if "&" in row["Ký hiệu bộ trưng bày (Mới)"]:
                item["transform"] = False
            item["count_face"] = row["Tổng Face Min SU"]
            item["matrix"] = {}
            for elem in prog_code_matches[1:]:
                prog_code_match = prog_code_pattern.match(elem)
                a = prog_code_match.group("a")
                b = int(prog_code_match.group("b"))
                if not np.isnan(row[labels[b]]):
                    item["matrix"].update(
                        {labels[b]: f"{a}*{row[labels[b]]:.0f}"}
                    )
                else:
                    item["matrix"].update({labels[b]: f"{a}*0"})
            data.append(item)
        for elem in data:
            try:
                check_obj = await Checks.create(**elem)
            except IntegrityError:
                check = await get_checks_or_404(elem["id"])
                check_update = CheckUpdate(
                    name=elem["name"],
                    transform=elem["transform"],
                    count_face=elem["count_face"],
                    matrix=elem["matrix"],
                )
                check.update_from_dict(check_update.dict(exclude_unset=True))
                await check.save()
        return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"An error occured while reading the Excel file: {str(e)}",
            result="fail",
        )


# @check_router.put("/edit/{id}", dependencies=[Depends(api_token)])
# async def update_check(
#     checks_update: CheckUpdate, checks: Checks = Depends(get_checks_or_404)
# ) -> dict:
#     checks.update_from_dict(checks_update.dict(exclude_unset=True))
#     await checks.save()
#     return CheckPublic.from_orm(checks).dict()
#
#
@check_router.delete("/{id}", dependencies=[Depends(api_token)])
async def delete_checks(id: str) -> dict:
    try:
        checks = await Checks.filter(id=id).delete()
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Checks {id} does not exist",
            result="fail",
        )
    return {"message": "Deleted images filtered with id"}
