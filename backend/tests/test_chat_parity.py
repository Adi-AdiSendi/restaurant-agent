"""Chat parity (ADR 0026): whatever the chat can do, the guest can do by hand.

Every tool the model may call, and every memory operation extraction may
apply, maps to the HTTP route the UI uses for the same thing. A new tool or
operation without a manual route fails here.
"""

import re
from pathlib import Path
from typing import get_args

from app.agent.tool_dispatch import HANDLERS
from app.main import create_app
from app.memory.operations import Operation
from app.memory.vocabulary import Kind

TOOL_ROUTES = {
    "search_menu": ("GET", "/api/restaurants/{slug}/menu"),
    "get_item": ("GET", "/api/restaurants/{slug}/menu"),
    "show_menu": ("GET", "/api/restaurants/{slug}/menu"),
    "view_cart": ("GET", "/api/cart"),
    "add_to_cart": ("POST", "/api/cart/lines"),
    "update_cart_line": ("PATCH", "/api/cart/lines/{line_id}"),
    "remove_cart_line": ("DELETE", "/api/cart/lines/{line_id}"),
    "clear_cart": ("DELETE", "/api/cart"),
    "recent_orders": ("GET", "/api/orders"),
    # The chat only proposes; the guest's button places the order (ADR 0019).
    "propose_checkout": ("POST", "/api/orders"),
}

MEMORY_ROUTES = {
    "add": ("POST", "/api/preferences"),
    "supersede": ("PATCH", "/api/preferences/{pref_id}"),
    "remove": ("DELETE", "/api/preferences/{pref_id}"),
}

TYPES_TS = Path(__file__).parents[2] / "frontend" / "src" / "api" / "types.ts"


def routes() -> set[tuple[str, str]]:
    """Every API route, from the OpenAPI schema (routers are nested in the app)."""
    paths: dict[str, dict[str, object]] = create_app().openapi()["paths"]
    return {(method.upper(), path) for path, ops in paths.items() for method in ops}


def test_every_tool_has_a_manual_route() -> None:
    assert set(HANDLERS) == set(TOOL_ROUTES), "map each new tool to its manual route"
    missing = set(TOOL_ROUTES.values()) - routes()
    assert not missing


def test_every_memory_operation_has_a_manual_route() -> None:
    ops = set(get_args(Operation.model_fields["op"].annotation))
    assert ops == set(MEMORY_ROUTES), "map each new memory operation to its manual route"
    assert not set(MEMORY_ROUTES.values()) - routes()


def test_the_ui_knows_every_preference_kind() -> None:
    """The UI's kinds match the backend's. The frontend then requires a label for each
    (`LABELS` is a Record) and its page test checks every label has a section."""
    union = re.search(r"PreferenceKind =((?:\s*\|?\s*'\w+')+)", TYPES_TS.read_text("utf-8"))
    assert union is not None
    assert set(re.findall(r"'(\w+)'", union.group(1))) == {k.value for k in Kind}
