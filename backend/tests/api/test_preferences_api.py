"""The Preferences page routes: a manual edit acts exactly like one made in the chat."""

import httpx2
from sqlalchemy.ext.asyncio import AsyncSession

from tests.agent.fake_llm import FakeLLM, answer_turn
from tests.api.conftest import active, login, new_conversation, say
from tests.api.test_cart_api import CAFE, latte


async def add(http: httpx2.AsyncClient, kind: str, value: str) -> httpx2.Response:
    return await http.post("/api/preferences", json={"kind": kind, "value": value})


async def test_edits_need_a_login(client: httpx2.AsyncClient) -> None:
    assert (await add(client, "like", "salmon")).status_code == 401
    assert (await client.patch("/api/preferences/1", json={"value": "x"})).status_code == 401
    assert (await client.delete("/api/preferences/1")).status_code == 401


async def test_add_change_and_remove_return_the_history(client: httpx2.AsyncClient) -> None:
    await login(client, "prefs_api")
    added = await add(client, "dislike", "Pickles")
    assert added.status_code == 201
    [pickles] = added.json()
    changed = await client.patch(f"/api/preferences/{pickles['id']}", json={"value": "olives"})
    assert changed.status_code == 200 and await active(client) == [("dislike", "olives")]
    removed = await client.delete(f"/api/preferences/{changed.json()[0]['id']}")
    assert [r["status"] for r in removed.json()] == ["removed", "superseded"]


async def test_bad_values_are_422_with_a_message(client: httpx2.AsyncClient) -> None:
    await login(client, "prefs_bad")
    bad = await add(client, "calories", "100")
    assert bad.status_code == 422
    assert bad.json()["detail"]["code"] == "invalid_preference"
    assert "800 to 6000" in bad.json()["detail"]["message"]
    assert (await add(client, "mood", "happy")).status_code == 422


async def test_another_users_fact_is_404_and_stays(
    client: httpx2.AsyncClient, other_client: httpx2.AsyncClient
) -> None:
    await login(client, "prefs_owner")
    [nut] = (await add(client, "allergy", "peanut")).json()
    await login(other_client, "prefs_intruder")
    assert (await other_client.delete(f"/api/preferences/{nut['id']}")).status_code == 404
    patched = await other_client.patch(f"/api/preferences/{nut['id']}", json={"value": "fish"})
    assert patched.status_code == 404
    assert await active(client) == [("allergy", "peanut")]


async def test_a_manual_allergy_is_enforced_on_the_menu_cart_and_chat(
    seeded: AsyncSession, llm: FakeLLM, client: httpx2.AsyncClient
) -> None:
    await login(client, "prefs_dairy")
    await add(client, "allergy", "dairy")
    menu = (await client.get(f"/api/restaurants/{CAFE}/menu")).json()
    karak = next(i for i in menu["items"] if i["name"] == "Karak Chai")
    assert karak["conflicts_with_guest"] == ["dairy"]
    refused = await client.post("/api/cart/lines", json=await latte(seeded, "Whole milk"))
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "conflict"

    conversation = await new_conversation(client, CAFE)
    llm.turns.append(answer_turn("Here you go.", []))
    await say(client, conversation, "What should I get?")
    assert "dairy" in str(llm.calls[-1][0]["content"])


async def test_the_vocabulary_comes_from_the_server(client: httpx2.AsyncClient) -> None:
    await login(client, "prefs_vocab")
    vocab = (await client.get("/api/preferences/vocabulary")).json()
    assert "tree_nut" in vocab["allergens"] and vocab["diets"] == ["vegetarian", "vegan"]
    assert vocab["spice_levels"] == ["none", "mild", "medium", "hot"]
    assert vocab["weekdays"][0] == "monday" and vocab["calories_min"] == 800
