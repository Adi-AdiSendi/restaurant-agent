from app.agent.prompt import APP_NAME, system_prompt
from app.menu.restaurant import Restaurant


def place(name: str, cuisine: str, categories: list[str]) -> Restaurant:
    return Restaurant(
        slug=name.lower().replace(" ", "-"),
        name=name,
        cuisine=cuisine,
        tagline=f"{name} tagline.",
        accent_color="#123456",
        categories=categories,
        position=0,
    )


CAFE = place("Bean Test", "Cafe", ["coffee", "pastries"])
GRILL = place("Grill Test", "Shawarma and grill", ["wraps"])


def test_names_the_restaurant_its_cuisine_and_categories() -> None:
    prompt = system_prompt(CAFE, [GRILL])
    assert f"{APP_NAME} for Bean Test, a cafe restaurant: Bean Test tagline." in prompt
    assert "menu categories are: coffee, pastries." in prompt


def test_lists_the_other_restaurants_as_suggestions_only() -> None:
    prompt = system_prompt(CAFE, [GRILL])
    assert "other restaurants are: Grill Test (shawarma and grill)." in prompt
    assert "Never recommend their dishes." in prompt


def test_no_other_restaurants() -> None:
    assert "other restaurants are: none." in system_prompt(CAFE, [])


def test_explains_options() -> None:
    assert "Only suggest options whose conflicts_with_guest is empty." in system_prompt(CAFE, [])


def test_ordering_never_places_or_overrides() -> None:
    prompt = system_prompt(CAFE, [])
    assert "call propose_checkout" in prompt
    assert "You cannot place orders, so never say an order is placed." in prompt
    assert "Never offer to add it anyway." in prompt
