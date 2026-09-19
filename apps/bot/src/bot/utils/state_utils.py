from typing import Union, List, Optional
from aiogram.fsm.context import FSMContext

async def collect_messages_to_delete(state: FSMContext, data: Optional[Union[List[int], int]]) -> None:
    if not data:
        return

    messages_to_delete: set = (await state.get_data()).get("messages_to_delete", set())

    if isinstance(data, int):
        messages_to_delete.add(data)
    else:
        messages_to_delete = messages_to_delete.union(data)

    await state.update_data(messages_to_delete=messages_to_delete)
