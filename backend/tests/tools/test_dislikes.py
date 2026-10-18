from app.tools.dislikes import disliked_removables

BURGER = ["pickles", "onion", "tomato", "smash sauce (mayo, mustard)"]


def test_a_dislike_matches_in_either_number_and_any_case() -> None:
    assert disliked_removables(BURGER, ["Pickle", "onions", "tomatoes"], []) == [
        "pickles",
        "onion",
        "tomato",
    ]


def test_only_removable_ingredients_are_left_out() -> None:
    assert disliked_removables(BURGER, ["mushrooms", "mayo"], []) == []


def test_kept_ingredients_stay_in() -> None:
    assert disliked_removables(BURGER, ["pickles", "onion"], ["Pickles"]) == ["onion"]
