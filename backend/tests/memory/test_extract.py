import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.extract import extract_operations
from app.memory.preference import Preference
from tests.agent.fake_llm import FakeLLM, extraction, op
from tests.conftest import make_user


async def test_valid_operations_are_returned() -> None:
    llm = FakeLLM([], extractions=[extraction(op("add", "allergy", "peanut"))])
    ops = await extract_operations(llm, [], None, "I'm allergic to peanuts")
    assert [(o.op, o.kind, o.value) for o in ops] == [("add", "allergy", "peanut")]


async def test_invalid_operation_is_dropped_and_the_rest_kept() -> None:
    answer = extraction(op("add", "allergy", "lactose"), op("add", "diet", "vegan"))
    llm = FakeLLM([], extractions=[answer])
    ops = await extract_operations(llm, [], None, "no milk, and I'm vegan")
    assert [(o.kind, o.value) for o in ops] == [("diet", "vegan")]


async def test_invalid_json_means_no_change() -> None:
    llm = FakeLLM([], extractions=["not json", json.dumps({"ops": []})])
    assert await extract_operations(llm, [], None, "hello") == []
    assert await extract_operations(llm, [], None, "hello") == []


async def test_profile_previous_reply_and_message_reach_the_model(session: AsyncSession) -> None:
    user = await make_user(session, "user1")
    row = Preference(user_id=user, kind="diet", value="vegan")
    session.add(row)
    await session.flush()
    llm = FakeLLM([])
    await extract_operations(llm, [row], "Any allergies?", "peanuts")
    sent = llm.extraction_inputs[0]
    assert f"{row.id}: diet = vegan" in sent
    assert "Any allergies?" in sent
    assert sent.endswith("peanuts")


async def test_empty_profile_is_explicit() -> None:
    llm = FakeLLM([])
    await extract_operations(llm, [], None, "hi")
    assert "(empty)" in llm.extraction_inputs[0]
