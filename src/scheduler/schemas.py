"""Schemas for the scheduler module."""
from datetime import datetime, date
from typing import Optional, Union

from pydantic import Field, model_validator
from typing_extensions import Self

from src.base import BaseSchema
from src.enums import MessageType, SchedulerStatus
from src.scheduler.api_client import APIClient


class AddEventSchema(BaseSchema):
    """Schema to add a new event"""

    date: datetime
    description: Optional[str] = ""
    is_return: Optional[bool] = Field(alias="isReturn", default=False)
    is_off: Optional[bool] = Field(alias="isOff", default=False)
    off_reason: Optional[str] = Field(alias="offReason", default=None)
    clinic_id: int = Field(alias="clinicId")
    patient_id: int = Field(alias="patientId")
    patient: str
    user: str
    desk_id: int = Field(alias="deskId")
    desk: str

    @model_validator(mode="after")
    def check_off_reason(self) -> Self:
        """Check if off_reason is informed when is_off is True."""
        if self.is_off and self.off_reason is None:
            raise ValueError("Informe o motivo da ausência.")
        return self

    @model_validator(mode="before")
    def check_date(self) -> Self:
        """Check if date is in the future."""
        if self.date < datetime.now():
            raise ValueError("A data do agendamento deve ser futura.")
        return self

    @model_validator(mode="before")
    def check_clinic(self) -> Self:
        """Check if clinic exists."""
        if not APIClient().check_if_clinic_exist(self.clinic_id):
            raise ValueError("Clínica não encontrada.")
        return self

    @model_validator(mode="before")
    def check_desk(self) -> Self:
        """Check if desk exists."""
        if not APIClient().check_if_desk_exist(self.desk_id):
            raise ValueError("Consultório não encontrado.")

        if not APIClient().check_if_desk_vacancy(self.desk_id):
            raise ValueError("Consultório não disponível.")

        return self


class EditEventSchema(BaseSchema):
    """Schema to edit an event"""

    event_id: int = Field(alias="eventId", default=False)
    status: Optional[SchedulerStatus]
    date: datetime
    description: Optional[str] = ""
    is_return: Optional[bool] = Field(alias="isReturn", default=False)
    is_off: Optional[bool] = Field(alias="isOff", default=False)
    off_reason: Optional[str] = Field(alias="offReason", default=None)
    patient_id: Optional[int] = Field(alias="patientId", default=False)
    patient: Optional[str]
    desk_id: Optional[int] = Field(alias="deskId", default=False)
    desk: Optional[str]

    @model_validator(mode="after")
    def check_off_reason(self) -> Self:
        """Check if off_reason is informed when is_off is True."""
        if self.is_off and self.off_reason is None:
            raise ValueError("Informe o motivo da ausência.")
        return self

    @model_validator(mode="before")
    def check_date(self) -> Self:
        """Check if date is in the future."""
        if self.date < datetime.now():
            raise ValueError("A data do agendamento deve ser futura.")
        return self

    @model_validator(mode="before")
    def check_desk(self) -> Self:
        """Check if desk exists."""
        if not APIClient().check_if_desk_exist(self.desk_id):
            raise ValueError("Consultório não encontrado.")

        if not APIClient().check_if_desk_vacancy(self.desk_id):
            raise ValueError("Consultório não disponível.")

        return self


class EventSchema(BaseSchema):
    """Event Schema"""

    id: int
    date: datetime
    description: Optional[str] = ""
    is_return: Optional[bool] = Field(alias="isReturn", default=False)
    is_off: Optional[bool] = Field(alias="isOff", default=False)
    off_reason: Optional[str] = Field(alias="offReason", default=None)
    patient: Optional[str] = None
    desk: str


class GetFullMonthCalendarSchema(BaseSchema):
    """Schema to get the full month calendar"""

    month: int
    year: int


class ReponseEventsCalendarSchema(BaseSchema):
    """Response Schema to get the full month calendar"""

    events: list[EventSchema]


class GetFullWeekCalendarSchema(BaseSchema):
    """Schema to get the full week calendar"""

    day: int
    month: int
    year: int


class GetDayCalendarSchema(BaseSchema):
    """Schema to get the day calendar"""

    date: date


class RemoveEventSchema(BaseSchema):
    """Schema to remove an event"""

    event_id: int = Field(alias="eventId")


class ConnectionSchema(BaseSchema):
    """Connection Schema"""

    token: str


class CreateUUIDSchema(BaseSchema):
    """Create UUID Schema"""

    uuid: str


class ErrorResponseSchema(BaseSchema):
    """Error Response Schema"""

    error: str


class Message(BaseSchema):
    """Message Schema"""

    message_type: MessageType
    clinic_id: int = Field(alias="clinicId")
    data: Optional[Union[
        AddEventSchema,
        EditEventSchema,
        GetFullMonthCalendarSchema,
        GetFullWeekCalendarSchema,
        GetDayCalendarSchema,
        RemoveEventSchema,
        ConnectionSchema,
        CreateUUIDSchema,
        ErrorResponseSchema,
        ReponseEventsCalendarSchema,
    ]] = None
