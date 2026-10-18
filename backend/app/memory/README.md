# memory

Long-term memory about each user, and the conversations it comes from.
Every query is scoped by `user_id`.

- `models.py`: `Conversation`, `Message` (assistant messages keep their
  recommended item IDs).
- `preference.py`: `Preference`, typed facts (`allergy`, `diet`, `dislike`,
  `like`, `budget`, `spice`, `day_dislike`, `day_like`, `calories`) with
  `status` active, superseded or removed.
  CHECKs and partial unique indexes keep the vocabulary and "one active diet,
  budget, spice" true in the database. `vocabulary.py` holds the values.
- `extract.py`: one structured LLM call per user message returns operations
  (`add`, `supersede`, `remove`). The call goes through an injected
  `JSONCompleter` (implemented in `agent/`), so this module never imports the
  SDK. Prompt and schema in `extract_prompt.py`.
- `operations.py`: validates each operation. Values outside the vocabulary are
  dropped; the rest still apply.
- `supersede.py`: applies operations. Old facts are replaced, never stacked:
  a new diet, budget or spice supersedes the old one, `like X` supersedes
  `dislike X`. A target owned by another user, inactive, or of a different
  kind or value than the operation names is ignored (ADR 0016), so a wrong ID
  cannot delete an allergy.
- `manual_edit.py`: add, change and remove a fact by hand (the Preferences
  page, ADR 0026). Same `Operation` validation and `apply_operations` as
  extraction, under the same per-user lock as a chat turn; a fact that is
  not this user's active one is `PreferenceNotFound`.
- `profile.py`: the active profile for the agent, and the full history for
  `GET /api/preferences`.
- `conversations.py`: create, ownership check, last 20 messages, save a message.

Depends on: `menu` (allergen vocabulary), `users` (the per-user lock), `db`. Used by: `agent`, `api`.
