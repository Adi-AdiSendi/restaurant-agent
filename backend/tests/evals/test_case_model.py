from pathlib import Path

import pytest

from app.memory.operations import Operation
from evals.case_model import Case, load_cases


@pytest.fixture(scope="module")
def cases() -> list[Case]:
    return load_cases()


def test_every_category_has_at_least_five_cases(cases: list[Case]) -> None:
    counts: dict[str, int] = {}
    for case in cases:
        counts[case.category] = counts.get(case.category, 0) + 1
    assert len(counts) == 7
    assert min(counts.values()) >= 5


def test_steps_and_profiles_only_name_the_case_users(cases: list[Case]) -> None:
    for case in cases:
        spoken: set[str] = set()
        for step in case.steps:
            assert step.user in case.users, case.id
            if step.into_conversation_of:
                assert step.into_conversation_of in spoken, case.id
            spoken.add(step.user)
        assert set(case.profiles) <= set(case.users), case.id


def test_expected_facts_use_the_stored_vocabulary(cases: list[Case]) -> None:
    """A typo like "peanuts" would make a profile check pass or fail for the wrong reason."""
    for case in cases:
        for profile in case.profiles.values():
            for kind, value in [*profile.active, *profile.superseded, *profile.not_active]:
                assert Operation(op="add", kind=kind, value=value).value == value, case.id


def test_a_case_in_the_wrong_file_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "grounding.yaml").write_text(
        "- id: x\n  category: isolation\n  description: d\n  users: [u]\n"
        "  steps: [{user: u, say: hi}]\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="category grounding"):
        load_cases(tmp_path)


def test_unknown_fields_are_rejected(tmp_path: Path) -> None:
    (tmp_path / "grounding.yaml").write_text(
        "- id: x\n  category: grounding\n  description: d\n  users: [u]\n"
        "  steps: [{user: u, say: hi, expect: {forbid: [peanut]}}]\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="forbid"):
        load_cases(tmp_path)
