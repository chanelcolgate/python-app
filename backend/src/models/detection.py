from typing import List, Optional

from pydantic import BaseModel, Field
from tortoise.models import Model
from tortoise import fields


class LocationBase(BaseModel):
    latitude: float
    longitude: float

    class Config:
        json_schema_extra = {"latitude": 16.0590299, "longitude": 108.2075305}


class QuantBase(BaseModel):
    name: str
    type: str
    hop_ytv: int
    hop_vtg: int
    hop_jn: int
    loc_ytv: int
    loc_kid: int
    loc_jn: int
    lo_ytv: int
    lo_kid: int
    bom_gen: int
    bom_jun: int
    bom_vtgk: int
    bom_ytv: int
    bom_knp: int
    bom_sachet: int
    day_sachet: int
    pocky: int

    class Config:
        json_schema_extra = {
            "name": "hộp",
            "type": "trưng bày base",
            "hop_ytv": 4,
            "hop_vtg": 1,
            "hop_jn": 1,
        }


class QuantCheck(QuantBase):
    pass


class QuantResult(QuantBase):
    pass


class QuantDescription(QuantBase):
    class Config:
        json_schema_extra = {"name": "lo_kids", "quantity": -1}


class DuplicateDescription(BaseModel):
    confidence: float
    image_src: str

    class Config:
        json_schema_extra = {
            "confidence": 57.59,
            "image_src": "http://10.20.1.90/image/fee8c9b5-21ad-4854-b7c6-5632f42e97e4.jpeg",
        }


class DetectionDescription(BaseModel):
    results: List[QuantResult]
    image_result: str

    class Config:
        json_schema_extra = {
            "results": [
                {"name": "hop_vtg", "quantity": 1},
                {"name": "hop_ytv", "quantity": 9},
                {"name": "loc_kids", "quantity": 4},
                {"name": "loc_ytv", "quantity": 4},
            ],
            "image_result": "http://10.20.1.90/image/fee8c9b5-21ad-4854-b7c6-5632f42e97e4.jpeg",
        }


class DescriptionBase(BaseModel):
    results: bool
    description: Optional[List[QuantDescription], DuplicateDescription]

    class Config:
        json_schema_extra = {
            "result": False,
            "description": [{"name": "lo_kids", "quantity": -1}],
        }


class DetectionBase(BaseModel):
    image: str
    limit: int
    location: LocationBase
    check_list: List[QuantCheck]

    class Config:
        json_schema_extra = {
            "example": {
                "image": "http://10.20.1.90/image/002df0a7-25c2-47d0-b3e8-e513c3c0d9de.jpeg",
                "limit": 300,
                "location": {"latitude": 16.0590299, "longitude": 108.2075305},
                "check_list": [
                    {
                        "name": "hop_vtg",
                        "quantity": 1,
                    },
                    {
                        "name": "hop_ytv",
                        "quantity": 1,
                    },
                    {"name": "lo_kids", "quantity": 1},
                ],
            }
        }


class DetectionPublic(DetectionBase):
    image_duplicates: Optional[bool, DuplicateDescription]
    produce_count: Optional[bool, DetectionDescription]
    value: DescriptionBase

    class Config:
        json_schema_extra = {
            "example": {
                "image": "http://10.20.1.90/image/002df0a7-25c2-47d0-b3e8-e513c3c0d9de.jpeg",
                "limit": 300,
                "location": {"latitude": 16.0590299, "longitude": 108.2075305},
                "check_list": [
                    {
                        "name": "hop_vtg",
                        "quantity": 1,
                    },
                    {
                        "name": "hop_ytv",
                        "quantity": 1,
                    },
                    {"name": "lo_kids", "quantity": 1},
                ],
                "image_dupliates": {
                    "confidence": 57.59,
                    "image_src": "http://10.20.1.90/image/fee8c9b5-21ad-4854-b7c6-5632f42e97e4.jpeg",
                },
                "produce_count": {
                    "results": [
                        {"name": "hop_vtg", "quantity": 1},
                        {"name": "hop_ytv", "quantity": 9},
                        {"name": "loc_kid", "quantity": 4},
                        {"name": "loc_ytv", "quantity": 4},
                    ],
                    "image_result": "http://10.20.1.90/image/fee8c9b5-21ad-4854-b7c6-5632f42e97e4.jpeg",
                },
                "value": {
                    "result": False,
                    "description": [{"name": "lo_kids", "quantity": -1}],
                },
            }
        }
