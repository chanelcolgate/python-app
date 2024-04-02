from typing import Optional, Dict

from pydantic import BaseModel, validator
from tortoise import fields, models

from src.settings import settings


class Checks(models.Model):
    """
    The Check model
    """

    id = fields.CharField(max_length=8, pk=True)
    name = fields.CharField(max_length=32)
    transform = fields.BooleanField()
    count_face = fields.SmallIntField()
    matrix = fields.JSONField()

    class Meta:
        table = "checks"


class CheckBase(BaseModel):
    id: str
    name: str
    transform: bool
    count_face: int
    matrix: dict

    class Config:
        from_attributes = True


class CheckCreate(CheckBase):
    class Config:
        json_schema_extra = {
            "example": {
                "id": "HOPG",
                "name": "Bộ Hộp GOLD",
                "maxtrix": {
                    "hop_jn": "&01*04",
                    "hop_vtg": "&01*01",
                    "hop_ytv": "&01*01",
                },
                "transform": False,
                "count_face": 6,
            }
        }


class CheckPublic(CheckCreate):
    pass


# class CheckPublic(CheckCreate):
#     if settings.SHOW:
#         id: int
#
#     @validator(
#         "hop_ytv",
#         "hop_vtg",
#         "hop_jn",
#         "loc_ytv",
#         "loc_kids",
#         "loc_jn",
#         "lo_ytv",
#         "lo_kids",
#         "bom_gen",
#         "bom_jun",
#         "bom_vtgk",
#         "bom_ytv",
#         "bom_knp",
#         "bom_sachet",
#         "day_sachet",
#         "pocky",
#         pre=True,
#         always=True,
#     )
#     def remove_none(cls, value):
#         if value is None:
#             return 0
#         return value
#
#     def dict(self, **kwargs):
#         return {k: v for k, v in super().dict(**kwargs).items() if v != 0}


class CheckUpdate(BaseModel):
    name: Optional[str] = None
    transform: Optional[bool] = None
    count_face: Optional[int] = None
    matrix: Optional[Dict[str, str]] = None


class CheckDB(CheckPublic):
    pass
