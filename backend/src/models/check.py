from typing import Optional

from pydantic import BaseModel, validator
from tortoise import fields, models

from src.settings import Settings

settings = Settings()


class Checks(models.Model):
    """
    The Check model
    """

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32)
    type_check = fields.CharField(max_length=32)
    hop_ytv = fields.IntField(null=True, default=None)
    hop_vtg = fields.IntField(null=True, default=None)
    hop_jn = fields.IntField(null=True, default=None)
    loc_ytv = fields.IntField(null=True, default=None)
    loc_kids = fields.IntField(null=True, default=None)
    loc_jn = fields.IntField(null=True, default=None)
    lo_ytv = fields.IntField(null=True, default=None)
    lo_kids = fields.IntField(null=True, default=None)
    bom_gen = fields.IntField(null=True, default=None)
    bom_jun = fields.IntField(null=True, default=None)
    bom_vtgk = fields.IntField(null=True, default=None)
    bom_ytv = fields.IntField(null=True, default=None)
    bom_knp = fields.IntField(null=True, default=None)
    bom_sachet = fields.IntField(null=True, default=None)
    day_sachet = fields.IntField(null=True, default=None)
    pocky = fields.IntField(null=True, default=None)

    class Meta:
        table = "checks"


class CheckBase(BaseModel):
    name: str
    type_check: str

    class Config:
        from_attributes = True


class CheckCreate(CheckBase):
    hop_ytv: Optional[int] = None
    hop_vtg: Optional[int] = None
    hop_jn: Optional[int] = None
    loc_ytv: Optional[int] = None
    loc_kids: Optional[int] = None
    loc_jn: Optional[int] = None
    lo_ytv: Optional[int] = None
    lo_kids: Optional[int] = None
    bom_gen: Optional[int] = None
    bom_jun: Optional[int] = None
    bom_vtgk: Optional[int] = None
    bom_ytv: Optional[int] = None
    bom_knp: Optional[int] = None
    bom_sachet: Optional[int] = None
    day_sachet: Optional[int] = None
    pocky: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "hộp",
                "type_check": "trưng bày base",
                "hop_ytv": 4,
                "hop_vtg": 1,
                "hop_jn": 1,
            }
        }


class CheckPublic(CheckCreate):
    if settings.SHOW:
        id: int

    @validator(
        "hop_ytv",
        "hop_vtg",
        "hop_jn",
        "loc_ytv",
        "loc_kids",
        "loc_jn",
        "lo_ytv",
        "lo_kids",
        "bom_gen",
        "bom_jun",
        "bom_vtgk",
        "bom_ytv",
        "bom_knp",
        "bom_sachet",
        "day_sachet",
        "pocky",
        pre=True,
        always=True,
    )
    def remove_none(cls, value):
        if value is None:
            return 0
        return value

    def dict(self, **kwargs):
        return {k: v for k, v in super().dict(**kwargs).items() if v != 0}


class CheckUpdate(BaseModel):
    name: Optional[str] = None
    type_check: Optional[str] = None
    hop_ytv: Optional[int] = None
    hop_vtg: Optional[int] = None
    hop_jn: Optional[int] = None
    loc_ytv: Optional[int] = None
    loc_kids: Optional[int] = None
    loc_jn: Optional[int] = None
    lo_ytv: Optional[int] = None
    lo_kids: Optional[int] = None
    bom_gen: Optional[int] = None
    bom_jun: Optional[int] = None
    bom_vtgk: Optional[int] = None
    bom_ytv: Optional[int] = None
    bom_knp: Optional[int] = None
    bom_sachet: Optional[int] = None
    day_sachet: Optional[int] = None
    pocky: Optional[int] = None


class CheckDB(CheckPublic):
    id: int
