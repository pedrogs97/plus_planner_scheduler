"""Custom ClientWebSocket"""

from typing import Iterable, Union, List, Tuple
from fastapi import WebSocket
from plus_db_agent.models import SchedulerModel
from src.scheduler.schemas import (
    Message,
    EventSchema,
    CreateUUIDSchema,
    ErrorResponseSchema,
    ReponseEventsCalendarSchema,
)
from src.enums import MessageType


class ClientWebSocket(WebSocket):
    """Custom ClientWebSocket"""

    token: str
    clinic_id: int
    uuid: str

    async def accept(
        self,
        subprotocol: Union[str, None] = None,
        headers: Union[Iterable[Tuple[bytes, bytes]], None] = None,
        client_id: Union[int, None] = None,
        uuid_code: Union[str, None] = None,
    ) -> None:
        await super().accept(subprotocol, headers)
        if client_id is None or uuid_code is None:
            return await self.send_error_message("Client ID ou UUID não informado")
        self.clinic_id = client_id
        self.uuid = uuid_code

    async def send_invalid_message(self) -> None:
        """Send invalid message"""
        await self.send(
            Message(message_type=MessageType.INVALID, clinic_id=self.clinic_id)
        )

    async def send_error_message(self, error: str) -> None:
        """Send error message"""
        await self.send(
            Message(
                message_type=MessageType.ERROR,
                clinic_id=self.clinic_id,
                data=ErrorResponseSchema(error=error),
            )
        )

    async def send_new_uuid(self, uuid_code: str) -> None:
        """Send new uuid"""
        await self.send(
            Message(
                message_type=MessageType.CREATE_UUID,
                clinic_id=self.clinic_id,
                data=CreateUUIDSchema(uuid=uuid_code),
            )
        )

    async def send(self, message: Message) -> None:
        """Send message"""
        await self.send_json(message.model_dump())

    async def send_events_calendar(self, events: List[SchedulerModel]) -> None:
        """Send full month calendar"""
        scheduler_events: List[EventSchema] = []
        for event in events:
            scheduler_events.append(
                EventSchema(
                    id=event.id,
                    date=event.date,
                    description=event.description,
                    is_return=event.is_return,
                    is_off=event.is_off,
                    off_reason=event.off_reason,
                    patient=event.patient,
                    desk=event.desk,
                )
            )
        await self.send(
            Message(
                message_type=MessageType.GET_FULL_MONTH_CALENDAR,
                clinic_id=self.clinic_id,
                data=ReponseEventsCalendarSchema(events=scheduler_events),
            )
        )
