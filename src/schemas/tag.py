from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class TagSchema(BaseModel):
    tag_list: List[str]

    @model_validator(mode="before")
    @classmethod
    def validate_tag_list_length(cls, data):
        max_tag_count = 5
        if "tag_list" in data and len(data["tag_list"]) > max_tag_count:
            raise ValueError(f"Too many tags, maximum {max_tag_count} tags allowed")
        return data

    @model_validator(mode="after")
    def validate_tag_length(self):
        max_tag_length = 50
        for tag in self.tag_list:
            if len(tag) > max_tag_length:
                raise ValueError(
                    f'Tag "{tag}" is too long, maximum {max_tag_length} characters allowed'
                )
        return self


class TagUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=50)


class TagImage(BaseModel):
    name: str


class TagResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
