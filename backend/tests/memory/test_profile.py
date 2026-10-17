from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.operations import Operation
from app.memory.profile import hard_constraints, load_profile, preference_history
from app.memory.supersede import apply_operations
from app.menu.allergens import Allergen
from tests.conftest import make_user


def add(kind: str, value: str) -> Operation:
    return Operation.model_validate({"op": "add", "kind": kind, "value": value})


async def test_profile_has_only_this_users_active_rows(session: AsyncSession) -> None:
    alice, bob = await make_user(session, "alice"), await make_user(session, "bob")
    await apply_operations(session, alice, [add("budget", "40"), add("allergy", "egg")], None)
    await apply_operations(session, alice, [add("budget", "60")], None)
    await apply_operations(session, bob, [add("diet", "vegan")], None)
    profile = await load_profile(session, alice)
    assert sorted((p.kind, p.value) for p in profile) == [("allergy", "egg"), ("budget", "60.00")]
    assert all(p.user_id == alice for p in profile)


async def test_history_includes_superseded_rows_newest_first(session: AsyncSession) -> None:
    user = await make_user(session, "user1")
    await apply_operations(session, user, [add("spice", "mild")], None)
    await apply_operations(session, user, [add("spice", "hot")], None)
    history = await preference_history(session, user)
    assert [(h.value, h.status) for h in history] == [("hot", "active"), ("mild", "superseded")]
    assert history[1].superseded_by == history[0].id
    assert history[0].is_hard is False


async def test_hard_constraints_come_from_active_allergy_and_diet_rows(
    session: AsyncSession,
) -> None:
    user = await make_user(session, "user1")
    ops = [
        add("allergy", "peanut"),
        add("allergy", "dairy"),
        add("diet", "vegan"),
        add("like", "x"),
    ]
    await apply_operations(session, user, ops, None)
    constraints = hard_constraints(await load_profile(session, user))
    assert constraints.excluded_allergens == {Allergen.PEANUT, Allergen.DAIRY}
    assert constraints.vegan
    assert constraints.vegetarian


async def test_vegetarian_diet_is_not_vegan(session: AsyncSession) -> None:
    user = await make_user(session, "user1")
    await apply_operations(session, user, [add("diet", "vegetarian")], None)
    constraints = hard_constraints(await load_profile(session, user))
    assert constraints.vegetarian
    assert not constraints.vegan
    assert not constraints.excluded_allergens
