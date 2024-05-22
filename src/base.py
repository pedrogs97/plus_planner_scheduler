"""Base model for all models."""
from tortoise import fields
from tortoise.models import Model
from pydantic import BaseModel as pydanticModel, ConfigDict


class BaseModel(Model):
    """Base model for all models."""
    id = fields.BigIntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    deleted = fields.BooleanField(default=False)

    class Meta:
        abstract = True


class BaseSchema(pydanticModel):
    """Base schema"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")
