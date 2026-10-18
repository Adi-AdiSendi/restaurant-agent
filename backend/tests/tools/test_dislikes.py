from app.tools.dislikes import disliked_removables

BURGER = ["pickles", "onion", "tomato", "smash sauce (mayo, mustard)", "sesame seeds"]


def test_a_dislike_matches_in_either_number_and_any_case() -> None:
    assert disliked_removables(BURGER, ["Pickle", "onions", "tomatoes"], []) == [
        "pickles",
        "onion",
        "tomato",
    ]


def test_a_dislike_inside_a_longer_ingredient_leaves_that_ingredient_out() -> None:
    assert disliked_removables(BURGER, ["mayo", "sesame"], []) == [
        "smash sauce (mayo, mustard)",
        "sesame seeds",
    ]


def test_a_dislike_must_match_whole_words() -> None:
    assert disliked_removables(["pine nuts", "onion"], ["pine", "nut", "on"], []) == ["pine nuts"]


def test_a_dislike_no_dish_lets_you_remove_changes_nothing() -> None:
    assert disliked_removables(BURGER, ["mushrooms", "smash sauce mustard"], []) == []


def test_kept_ingredients_stay_in() -> None:
    assert disliked_removables(BURGER, ["pickles", "onion"], ["Pickles"]) == ["onion"]
