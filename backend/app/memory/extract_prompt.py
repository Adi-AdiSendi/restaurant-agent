"""Instructions and strict output schema for the memory extraction call."""

from app.memory.vocabulary import Diet, Kind, Spice
from app.menu.allergens import Allergen

_ALLERGENS = ", ".join(a.value for a in Allergen)

EXTRACTION_PROMPT = f"""You maintain a restaurant guest's long-term food profile.
Read the guest's new message and return the operations that keep the profile true.
Return {{"operations": []}} when nothing durable about the guest changed.

Kinds and values:
- allergy: one of {_ALLERGENS}. Map wording to this list: "lactose intolerant" or \
"no milk" -> dairy; "coeliac" -> gluten; "nuts" -> tree_nut and peanut (two operations).
- diet: {", ".join(d.value for d in Diet)}.
- spice: how much heat they enjoy: {", ".join(s.value for s in Spice)}.
- budget: the most they want to pay per item, a number in SAR, e.g. "50".
- like / dislike: a short food, ingredient or dish, e.g. "mushrooms", "salmon".
- day_dislike: a food avoided on one weekday, written "<weekday>: <food>", e.g. \
"friday: meat" (one operation per weekday).
- calories: the guest's own daily calorie goal in kcal, e.g. "1800".

Operations:
- add: a new fact. target_id null.
- supersede: the guest changed or corrected an existing fact. target_id is that \
fact's id; kind and value are the new fact.
- remove: an existing fact is no longer true and nothing replaces it. target_id \
is that fact's id; repeat its kind and value.

Store only facts about the guest themself that will matter in future visits.
Do not store: other people's preferences, hypotheticals, questions, one-off \
moods ("I'm not that hungry today"), or anything already in the profile.

Examples (profile shown as id: kind = value):
- "My friend is vegan, what would she like?" -> []
- "I'm lactose intolerant" -> add allergy dairy
- profile 4: diet = vegetarian; "Actually I eat fish now" -> remove 4 (diet vegetarian)
- profile 7: dislike = mushrooms; "I've come round to mushrooms, I love them now" \
-> supersede 7 with like mushrooms
- profile 2: budget = 40.00; "I can spend up to 70 today and in general" -> supersede 2 \
with budget 70
- "Is the wagyu burger spicy?" -> []
- "I don't eat meat on Fridays" -> add day_dislike "friday: meat"
- "I'm keeping under 1800 calories a day" -> add calories 1800
- "My sister is counting calories" -> []
- "Any allergies?" was asked, guest answers "peanuts" -> add allergy peanut"""

EXTRACTION_FORMAT: dict[str, object] = {
    "type": "json_schema",
    "name": "memory_operations",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["operations"],
        "properties": {
            "operations": {
                "type": "array",
                "maxItems": 10,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["op", "kind", "value", "target_id"],
                    "properties": {
                        "op": {"type": "string", "enum": ["add", "supersede", "remove"]},
                        "kind": {"type": "string", "enum": [k.value for k in Kind]},
                        "value": {"type": "string"},
                        "target_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    },
                },
            }
        },
    },
}
