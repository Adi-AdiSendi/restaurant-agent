from app.agent.context import build_input, memory_update_note, profile_block
from app.memory.models import Message
from app.memory.preference import Preference


def pref(kind: str, value: str) -> Preference:
    return Preference(user_id=1, kind=kind, value=value)


def test_profile_block_lists_hard_constraints_first() -> None:
    block = profile_block(
        [pref("like", "salmon"), pref("allergy", "peanut"), pref("diet", "vegan")]
    )
    lines = block.splitlines()
    assert "never recommend" in lines[1]
    assert "peanut" in lines[1]
    assert "vegan" in lines[2]
    assert "salmon" in lines[3]


def test_empty_profile_says_so() -> None:
    assert "nothing saved yet" in profile_block([])


def test_profile_is_the_first_item_then_history_in_order() -> None:
    history = [
        Message(role="user", content="Hi", recommended_item_ids=[]),
        Message(role="assistant", content="Try the bowl", recommended_item_ids=[13]),
        Message(role="user", content="I'll take it", recommended_item_ids=[]),
    ]
    items, seen = build_input([pref("diet", "vegan")], history)
    assert items[0]["role"] == "developer"
    assert "vegan" in str(items[0]["content"])
    assert [i["content"] for i in items[1:]] == [
        "Hi",
        "Try the bowl",
        "Item IDs recommended above: 13",
        "I'll take it",
    ]
    assert seen == {13}


def test_no_note_when_the_profile_did_not_change() -> None:
    assert memory_update_note([pref("diet", "vegan")], [pref("diet", "vegan")]) is None


def test_note_names_replacements_additions_and_removals() -> None:
    before = [pref("diet", "vegan"), pref("allergy", "dairy"), pref("allergy", "egg")]
    after = [pref("diet", "vegetarian"), pref("allergy", "egg"), pref("allergy", "peanut")]
    note = memory_update_note(before, after)
    assert note is not None
    assert 'Saved: allergy "peanut"; diet "vegetarian" (replaces "vegan").' in note
    assert 'No longer on file: allergy "dairy".' in note
    assert "Confirm this change" in note


def test_the_note_goes_last_after_the_guests_message() -> None:
    history = [Message(role="user", content="I'm vegetarian now", recommended_item_ids=[])]
    items, _ = build_input([pref("diet", "vegetarian")], history, "NOTE")
    assert [i["content"] for i in items[1:]] == ["I'm vegetarian now", "NOTE"]
