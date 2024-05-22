"""Models for the scheduler app."""
from tortoise import fields

from src.base import BaseModel
from src.enums import SchedulerStatus


class SchedulerModel(BaseModel):
    """Model to represent a scheduler."""

    status = fields.CharEnumField(
        enum_type=SchedulerStatus,
        max_length=20,
        default=SchedulerStatus.WAITING_CONFIRMATION,
    )
    date = fields.DatetimeField()
    description = fields.TextField(null=True)
    is_return = fields.BooleanField(default=False)
    is_off = fields.BooleanField(default=False)
    off_reason = fields.TextField(null=True)
    clinic_id = fields.BigIntField()
    patient = fields.CharField(max_length=150)
    user = fields.CharField(max_length=150)
    desk = fields.CharField(max_length=150)

    def __str__(self):
        return f"{self.date} - {self.status}"

    class Meta:
        table = "schedulers"


class HolidayModel(BaseModel):
    """Model to represent a holiday."""
    date = fields.DatetimeField()
    name = fields.CharField(max_length=100)
    type = fields.CharField(max_length=100)
    level = fields.CharField(max_length=100)

    def __str__(self):
        return f"{self.date} - {self.name}"

    class Meta:
        table = "holidays"
