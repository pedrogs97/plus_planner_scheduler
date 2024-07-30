"""Custom ClientWebSocket"""

from typing import List, Optional, Union

from fastapi import WebSocket
from fastapi.websockets import WebSocketState
from plus_db_agent.models import SchedulerModel
from plus_db_agent.schemas import BaseSchema

from src.enums import MessageType
from src.scheduler.schemas import (
    CreateUUIDSchema,
    ErrorResponseSchema,
    EventSchema,
    Message,
    ReponseEventsCalendarSchema,
)


class ClientWebSocket:
    """Custom ClientWebSocket"""

    token: Optional[str] = None
    clinic_id: int
    uuid: str
    user_id: Optional[int] = None
    wb: WebSocket

    def __init__(self, wb: WebSocket) -> None:
        self.wb = wb

    async def accept(
        self,
        client_id: Union[int, None] = None,
        uuid_code: Union[str, None] = None,
    ) -> None:
        """Accept connection"""
        if client_id is None or uuid_code is None:
            return await self.send_error_message("Client ID ou UUID não informado")
        self.clinic_id = client_id
        self.uuid = uuid_code
        await self.wb.accept()

    async def send_invalid_message(self) -> None:
        """Send invalid message"""
        await self.send(
            Message(messageType=MessageType.INVALID, clinicId=self.clinic_id)
        )

    async def send_error_message(self, error: str) -> None:
        """Send error message"""
        await self.send(
            Message(
                messageType=MessageType.ERROR,
                clinicId=self.clinic_id,
                data=ErrorResponseSchema(error=error),
            )
        )

    async def send_new_uuid(self, uuid_code: str) -> None:
        """Send new uuid"""
        await self.send(
            Message(
                messageType=MessageType.CREATE_UUID,
                clinicId=self.clinic_id,
                data=CreateUUIDSchema(uuid=uuid_code),
            )
        )

    async def send(self, message: Union[Message, dict]) -> None:
        """Send message"""
        if isinstance(message, BaseSchema):
            await self.wb.send_json(message.model_dump())
        else:
            await self.wb.send_json(message)

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
                messageType=MessageType.GET_FULL_MONTH_CALENDAR,
                clinicId=self.clinic_id,
                data=ReponseEventsCalendarSchema(events=scheduler_events),
            )
        )

    async def close(self) -> None:
        """Close connection"""
        if self.wb.state == WebSocketState.CONNECTED:
            await self.wb.close()
