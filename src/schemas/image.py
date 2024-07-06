from enum import Enum
from datetime import datetime
from typing import Optional, List, Union

from pydantic import BaseModel, ConfigDict, Field
from src.schemas.comments import CommentToImage
from src.schemas.tag import TagImage


class ImageSchema(BaseModel):
    url: str
    description: str

class ImageCreate(BaseModel):
    id: int
    url: str
    description: str
    created_at: datetime

class ImageUpdateSchema(BaseModel):
    description: Optional[str] = None


class ImageResponse(BaseModel):
    id: int
    url: str
    description: str
    tags: Optional[List[TagImage]] = None
    comments: Optional[List[CommentToImage]] = None

    model_config = ConfigDict(from_attributes=True)


class CropEnum(str, Enum):
    thumb = "thumb"
    crop = "crop"
    scale = "scale"
    fit = "fit"
    limit = "limit"
    fill = "fill"
    pad = "pad"
    lfill = "lfill"
    mpad = "mpad"

    def __str__(self):
        return self.value

class GravityEnum(str, Enum):
    auto = "auto"
    face = "face"
    center = "center"
    east = "east"
    north = "north"
    west = "west"
    south = "south"

    def __str__(self):
        return self.value

class EffectEnum(str, Enum):
    sepia = "sepia"
    monochrome = "monochrome"
    oil_paint = "oil_paint"
    grayscale = "grayscale"
    negate = "negate"
    cartoonify = "cartoonify"

    def __str__(self):
        return self.value

class BackgroundEnum(str, Enum):
    white = "white"
    black = "black"
    red = "red"
    green = "green"
    blue = "blue"
    yellow = "yellow"
    purple = "purple"
    brown = "brown"
    pink = "pink"
    orange = "orange"
    teal = "teal"
    cyan = "cyan"
    magenta = "magenta"
    lime = "lime"
    aqua = "aqua"
    gold = "gold"
    silver = "silver"

    def __str__(self):
        return self.value

class Transformation(BaseModel):
    gravity: GravityEnum    
    width: Optional[int] = 800
    height: Optional[int] = 800
    crop: CropEnum
    background: BackgroundEnum = BackgroundEnum.black
    effect: EffectEnum
    blur: Optional[int] = None
    sharpen: Optional[int] = None
    angle: Optional[int] = None

class Roundformation(BaseModel):
    gravity: GravityEnum    
    width: Optional[int] = 800
    height: Optional[int] = 800
    crop: CropEnum
    radius: Optional[str] = "max"
    effect: EffectEnum
    blur: Optional[int] = None
    sharpen: Optional[int] = None
    angle: Optional[int] = None