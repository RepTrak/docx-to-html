import datetime
from typing import List, Optional, Union, Literal
from pydantic import BaseModel

class BaseConfig:
    """Base configuration for Pydantic models."""
    pass

class DataItem(BaseModel):
    code: str

    class Config(BaseConfig):
        pass


class SurveyDataItem(DataItem):
    label: str


class SurveyDataItemPositionable(SurveyDataItem):
    position: int

class AttributeTagSchema(BaseModel):
    key: str
    value: str
    
class LoopElementVariablesResponseSchema(BaseModel):
    id: Optional[int]
    survey: Optional[SurveyDataItem]
    section: Optional[SurveyDataItemPositionable]
    element: Optional[SurveyDataItemPositionable]
    over_columns: Optional[bool]
    
class SectionResponseSchema(BaseModel):
    """
    Schema for section responses
    """

    code: str
    label: str
    notes: Optional[str] = None
    position: Optional[int] = None
    loop: Optional[LoopElementVariablesResponseSchema] = None

class GridColumnSchema(BaseModel):

    code: int
    label: str
    position: int
    tags: Optional[List[AttributeTagSchema]] = None
    notes: Optional[str] = None

class VariableResponseSchema(BaseModel):
    """
    Schema for variable responses
    """

    code: str
    label: str
    notes: Optional[str] = None
    position: Optional[int] = None
    revision: Optional[int] = None
    # options: Optional[ElementVariableOptionsSchemasAnnotated] = None
    tags: Optional[List[AttributeTagSchema]] = None

class SectionElementResponseSchema(BaseModel):
    """
    Schema for section element responses
    """

    code: str
    label: str
    notes: Optional[str] = None
    type: Literal["CHOICE", "OPEN_END", "BREAK_PAGE"]
    position: Optional[int] = None
    revision: Optional[int] = None
    tags: Optional[List[AttributeTagSchema]] = None
    # options: Optional[ElementOptionsSchemasAnnotated] = None
    is_loop_target: Optional[bool] = None
    help_text: Optional[str] = None

class FullSectionElementSchema(SectionElementResponseSchema):
    variables: Optional[List[VariableResponseSchema]] = None
    columns: Optional[List[GridColumnSchema]] = None
    # element_settings: Optional[ElementTypeDefinitions] = None


class FullSectionResponseSchema(SectionResponseSchema):
    elements: Optional[List[FullSectionElementSchema]] = None


class FullSurveyResponseSchema(BaseModel):
    sections: List[FullSectionResponseSchema]
