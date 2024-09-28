import pydantic
from pydantic.alias_generators import to_camel


class BaseModel(pydantic.BaseModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
