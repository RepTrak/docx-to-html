from dataclasses import Field
import datetime
from typing import List, Optional, Union, Literal, Dict
from pydantic import BaseModel, RootModel

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
    type: Literal[
                "CHOICE",
                "OPEN_END",
                "BREAK_PAGE",
                "SCREENER",
                "COUNTRY_DROPDOWN",
                "AGE_ORI",
                "S105_RATING_FAMILIARITY",
                "GEOGRAPHIC_AREA_REGION",
                "PULSE_FILTER",
                "YES_NO",
                "EDUCATION_STANDARD",
                "INCOME_STANDARD",
                  ]
    position: Optional[int] = None
    revision: Optional[int] = None
    tags: Optional[List[AttributeTagSchema]] = None
    # options: Optional[ElementOptionsSchemasAnnotated] = None
    is_loop_target: Optional[bool] = None
    help_text: Optional[str] = None
    section: Optional[SurveyDataItemPositionable]

class FullSectionElementSchema(SectionElementResponseSchema):
    variables: Optional[List[VariableResponseSchema]] = None
    columns: Optional[List[GridColumnSchema]] = None
    # element_settings: Optional[ElementTypeDefinitions] = None


class FullSectionResponseSchema(SectionResponseSchema):
    elements: Optional[List[FullSectionElementSchema]] = None


class FullSurveyResponseSchema(BaseModel):    
    code: Optional[str] = "AUTO_GENERATED_SURVEY"
    label: Optional[str] = "Auto-generated Survey"
    notes: Optional[str] = "This survey was auto-generated from markdown content."
    placeholder: Optional[bool] = False
    product_code: Optional[str] = "DIRECT_STAKEHOLDERS"
    meta_day_of_the_week: Optional[bool] = True
    meta_time_of_day: Optional[bool] = True
    meta_day_of_month: Optional[bool] = True
    meta_month: Optional[bool] = True
    meta_year: Optional[bool] = True
    meta_week_of_year: Optional[bool] = True
    meta_record_uuid: Optional[bool] = True
    meta_user_agent: Optional[bool] = True
    meta_day_of_the_month: Optional[bool] = True
    open_datasource_exit_config: Optional[List[Dict[str, Union[str, int]]]] = None
    show_reptrak_logo: Optional[bool] = True
    show_client_logo: Optional[bool] = False
    client_logo_position: Optional[Literal["left", "right"]] = "left"
    reptrak_logo_position: Optional[Literal["left", "right"]] = "right"
    allow_open_datasource: Optional[bool] = False
    allow_multiple_submissions_per_device: Optional[bool] = None
    sections: List[FullSectionResponseSchema]

SectionsListResponseSchema = RootModel[List[FullSectionResponseSchema]]
