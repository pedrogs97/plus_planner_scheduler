"""Connection Manager Module"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from threading import Thread
from typing import List

from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect, WebSocketState
from plus_db_agent.enums import SchedulerStatus
from plus_db_agent.models import SchedulerModel
from tortoise.exceptions import OperationalError
from typing_extensions import Self

from src.backends import check_clinic_id
from src.enums import MessageType
from src.scheduler.api_client import APIClient
from src.scheduler.client import ClientWebSocket
from src.scheduler.schemas import (
    AddEventSchema,
    ConnectionSchema,
    EditEventSchema,
    EventSchema,
    GetDayCalendarSchema,
    GetFullMonthCalendarSchema,
    GetFullWeekCalendarSchema,
    Message,
    RemoveEventSchema,
)
from src.utils import get_week

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Class defining socket events"""

    _instance: "ConnectionManager" = None
    client_connections: List[ClientWebSocket] = []
    queue = asyncio.Queue()
    api_client = APIClient()

    def __new__(cls) -> Self:
        """Singleton instance"""
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
        return cls._instance

    async def connect(self, websocket: WebSocket, clinic_id: int):
        """Add a new client connection to the list on connect"""
        client_websocket = ClientWebSocket(wb=websocket)
        if await check_clinic_id(clinic_id):
            new_uuid = uuid.uuid4().hex
            await client_websocket.accept(client_id=clinic_id, uuid_code=new_uuid)
            await client_websocket.send_new_uuid(new_uuid)
            self.client_connections.append(client_websocket)
            await self.__listenner(client_websocket)
        else:
            if client_websocket.wb.state == WebSocketState.CONNECTED:
                await client_websocket.send_error_message(
                    "Token inválido ou clínica inexistente"
                )
            elif websocket.application_state == "open":
                await websocket.send(
                    Message(
                        message_type=MessageType.ERROR,
                        clinic_id=clinic_id,
                        data={"error": "Token inválido ou clínica inexistente"},
                    )
                )
            time.sleep(0.1)
            await websocket.close()
            await client_websocket.close()

    async def disconnect(self, client: ClientWebSocket):
        """Remove a client connection from the list on disconnect"""
        if client in self.client_connections:
            self.client_connections.remove(client)
        if client.wb.state == WebSocketState.CONNECTED:
            await client.close()

    def get_all_connections(self) -> List[ClientWebSocket]:
        """Return all connections"""
        return self.client_connections

    def get_connection_by_uuid(self, uuid_code: str) -> ClientWebSocket:
        """Return connection by uuid"""
        for connection in self.client_connections:
            if connection.uuid == uuid_code:
                return connection
        return None

    def get_connection_by_clinic_id(self, clinic_id: int) -> ClientWebSocket:
        """Return connection by clinic_id"""
        for connection in self.client_connections:
            if connection.clinic_id == clinic_id:
                return connection
        return None

    async def broadcast_clinic_messages(self, clinic_id: int, message: Message) -> None:
        """Broadcast messages"""
        for client_connection in self.client_connections:
            if client_connection.clinic_id == clinic_id:
                await client_connection.send(message)

    async def __listenner(self, websocket_client: ClientWebSocket) -> None:
        """Listen to incoming messages"""
        try:
            while True:
                data = await websocket_client.wb.receive_json()
                try:
                    message = Message.model_validate_json(json.dumps(data))
                    await self.queue.put((websocket_client, message))
                except (ValueError, AttributeError):
                    await websocket_client.send_invalid_message()
                    continue
        except WebSocketDisconnect:
            self.disconnect(websocket_client)

    async def __process_full_month_calendar(
        self, message: Message, client: ClientWebSocket
    ) -> None:
        """Process full month calendar"""
        if not isinstance(message.data, GetFullMonthCalendarSchema):
            await client.send_invalid_message()
            return
        current_date = datetime.strptime(
            f"{message.data.year}-{message.data.month}-01", "%Y-%m-%d"
        ).date()
        scheduler_events = await SchedulerModel.filter(
            clinic_id=message.clinic_id,
            date__month=current_date.month,
            date__year=current_date.year,
        ).all()
        await client.send_events_calendar(scheduler_events)

    async def __process_full_week_calendar(
        self, message: Message, client: ClientWebSocket
    ) -> None:
        """Process full week calendar"""
        if not isinstance(message.data, GetFullWeekCalendarSchema):
            await client.send_invalid_message()
            return
        current_date = datetime.strptime(
            f"{message.data.year}-{message.data.month}-{message.data.day}", "%Y-%m-%d"
        ).date()
        week, _, _ = get_week(current_date)
        scheduler_events = await SchedulerModel.filter(
            clinic_id=message.clinic_id, date__gte=week[0], date__lte=week[-1]
        ).all()
        await client.send_events_calendar(scheduler_events)

    async def __process_day_calendar(
        self, message: Message, client: ClientWebSocket
    ) -> None:
        """Process day calendar"""
        if not isinstance(message.data, GetDayCalendarSchema):
            await client.send_invalid_message()
            return
        scheduler_events = await SchedulerModel.filter(
            clinic_id=message.clinic_id, date__date=message.data.date
        ).all()
        await client.send_events_calendar(scheduler_events)

    async def __process_add_event(
        self, message: Message, client: ClientWebSocket
    ) -> None:
        """Process add event"""
        try:
            if not isinstance(message.data, AddEventSchema):
                await client.send_invalid_message()
                return
            new_event = await SchedulerModel.create(
                status=SchedulerStatus.WAITING_CONFIRMATION.value,
                date=message.data.date,
                description=message.data.description,
                is_return=message.data.is_return,
                is_off=message.data.is_off,
                off_reason=message.data.off_reason,
                clinic_id=message.clinic_id,
                patient=message.data.patient,
                user=client.user_id,
                desk=message.data.desk,
            )
            new_event_schema = EventSchema(
                id=new_event.id,
                date=new_event.date,
                description=new_event.description,
                is_return=new_event.is_return,
                is_off=new_event.is_off,
                off_reason=new_event.off_reason,
                patient=new_event.patient,
                desk=new_event.desk,
            )
            new_message = Message(
                message_type=MessageType.ADD_EVENT,
                clinic_id=message.clinic_id,
                data=new_event_schema,
            )
            await self.broadcast_clinic_messages(client.clinic_id, new_message)
        except (OperationalError, AttributeError):
            await client.send_error_message("Erro ao adicionar o evento")

    async def __process_edit_event(
        self, message: Message, client: ClientWebSocket
    ) -> None:
        """Process edit event"""
        try:
            if not isinstance(message.data, EditEventSchema):
                await client.send_invalid_message()
                return
            event = await SchedulerModel.get(id=message.data.event_id)
            for key, value in message.data.model_dump().items():
                if value and hasattr(event, key):
                    setattr(event, key, value)
            await event.save()
            new_event_schema = EventSchema(
                id=event.id,
                date=event.date,
                description=event.description,
                is_return=event.is_return,
                is_off=event.is_off,
                off_reason=event.off_reason,
                patient=event.patient,
                desk=event.desk,
            )
            new_message = Message(
                message_type=MessageType.EDIT_EVENT,
                clinic_id=message.clinic_id,
                data=new_event_schema,
            )
            await self.broadcast_clinic_messages(client.clinic_id, new_message)
        except OperationalError:
            await client.send_error_message("Erro ao editar o evento")

    async def __process_remove_event(
        self, message: Message, client: ClientWebSocket
    ) -> None:
        """Process remove event"""
        try:
            if not isinstance(message.data, RemoveEventSchema):
                await client.send_invalid_message()
                return
            event = await SchedulerModel.get(id=message.data.event_id)
            await event.delete()
            new_message = Message(
                message_type=MessageType.REMOVE_EVENT,
                clinic_id=message.clinic_id,
                data=message.data,
            )
            await self.broadcast_clinic_messages(client.clinic_id, new_message)
        except OperationalError:
            await client.send_error_message("Erro ao remover o evento")

    async def __process_connection(self, message: Message, client: ClientWebSocket):
        """Process connection"""
        try:
            if not isinstance(message.data, ConnectionSchema):
                await client.send_invalid_message()
                return
            if not self.api_client.check_is_token_is_valid(message.data.token):
                await client.send_error_message("Token inválido")
                time.sleep(0.1)
                await self.disconnect(client)
                return
            user_dict = self.api_client.get_user_by_token(client.token)
            client.token = message
            client.user_id = user_dict["id"]
            await client.send(
                Message(
                    message_type=MessageType.CONNECTION, clinic_id=message.clinic_id
                )
            )
        except (OperationalError, AttributeError):
            await client.send_error_message("Erro ao validar conexão")
            time.sleep(0.1)
            await self.disconnect(client)

    async def __process_message(
        self, message: Message, client: ClientWebSocket
    ) -> None:
        """Process message"""
        try:
            if message.message_type == MessageType.CONNECTION:
                await self.__process_connection(message, client)
            elif (
                client.token
                and message.message_type == MessageType.GET_FULL_MONTH_CALENDAR
            ):
                await self.__process_full_month_calendar(message, client)
            elif (
                client.token
                and message.message_type == MessageType.GET_FULL_WEEK_CALENDAR
            ):
                await self.__process_full_week_calendar(message, client)
            elif client.token and message.message_type == MessageType.GET_DAY_CALENDAR:
                await self.__process_day_calendar(message, client)
            elif client.token and message.message_type == MessageType.ADD_EVENT:
                await self.__process_add_event(message, client)
            elif client.token and message.message_type == MessageType.EDIT_EVENT:
                await self.__process_edit_event(message, client)
            elif client.token and message.message_type == MessageType.REMOVE_EVENT:
                await self.__process_remove_event(message, client)
            elif not client.token:
                await client.send_error_message("Token inválido")
                time.sleep(0.1)
                await self.disconnect(client)
            else:
                await client.send_invalid_message()
        except (AttributeError, OperationalError):
            await client.send_error_message("Erro ao processar a mensagem")

    async def __process_queue(self):
        while True:
            if not self.queue.empty():
                websocket, message = await self.queue.get()
                logger.info("Processing message: %s", message.message_type)
                await self.__process_message(message, websocket)
            await asyncio.sleep(1)

    def __start_queue_processor(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.__process_queue())

    def start_main_thread(self):
        """Start the main thread"""
        thread = Thread(target=self.__start_queue_processor)
        thread.start()
        logger.info("Main thread started")
