"""Backend functions for plus_db_agent"""

from plus_db_agent.models import ClinicModel, DeskModel


async def check_clinic_id(pk: int) -> bool:
    """Check if client id exists"""
    return await ClinicModel.exists(id=pk)


async def check_desk_exist(desk_id: int) -> bool:
    """Check if desk exists"""
    return await DeskModel.exists(id=desk_id)


async def check_desk_vacancy(desk_id: int) -> bool:
    """Check if desk vacancy"""
    return await DeskModel.exists(id=desk_id, is_vacant=True)
