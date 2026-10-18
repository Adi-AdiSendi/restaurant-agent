# agent

Runs one chat turn: the model, its tool calls, and a structured final answer.

- `chat_turn.py`: entry point for the API, `handle_message(...)`. Loads the
  conversation (it must belong to the user) and its restaurant, locks the
  user row, saves the message, runs memory extraction, builds the model input
  and the `ToolContext` (`turn_setup.py`), runs the loop, saves the reply and
  returns a `ChatReply` (`turn_reply.py`).
  One transaction; any failure rolls back the whole turn. The turn has a
  deadline (`TURN_DEADLINE_SECONDS`, 22 s, under the Netlify proxy's 26 s);
  past it the turn is rolled back and `TurnTimeoutError` becomes a 504.
- `context.py`: the profile block (first input item, every turn) and the
  stored history; returns IDs recommended earlier in the conversation. When
  the latest message changed the profile, a note saying what changed goes
  last, so the reply confirms it (found by the phase 7 evals).
- `loop.py`: `run_turn(client, context, input_items, seen_ids, instructions=...)`.
  Gets an answer, grounds the cards, and runs `safety.check` on every card. A
  blocked card triggers one corrective retry; if still unsafe, blocked cards
  are dropped and the reply becomes a fixed safe message. Cards
  (`schemas.cards_for`) carry every option with its conflicts for this guest,
  and `may_contain_warnings`. Worst case 12 model calls per turn; in practice
  the deadline ends such a turn first.
- `tool_rounds.py`: calls the model with tools until it answers without tools
  (at most 5 tool rounds, then `AgentLoopError`), and retries a malformed
  answer once. Full tool results go back to the model untrimmed, after the
  model's own reasoning and function-call items, so a reasoning model keeps
  its reasoning between rounds with `store=False`.
- `answer.py`: `FinalAnswer` `{reply, recommended_item_ids}`, its strict JSON
  schema, and the retry prompt. A bad answer is retried once, then
  `AgentAnswerError`.
- `grounding.py`: a recommended ID becomes a card only if it exists in this
  conversation's restaurant and was seen: a tool returned it this turn, or it was recommended earlier in this
  conversation. Others are dropped and logged. Cards come from the DB, never
  from model text.
- `llm_client.py`: the small `LLMClient` and `AgentLLM` interfaces.
  `openai_client.py` implements them with the Responses API (`store=False`),
  including `complete_json` for `memory/extract.py`. Tests use
  `tests/agent/fake_llm.py`.
- `tool_dispatch.py`: tool specs and name-to-handler dispatch.
- `turn_setup.py`: everything the model gets for a turn: the profile block,
  the cart at the start of the turn (`cart_block.py`, with each line's id),
  the history, the `ToolContext` and the system prompt.
- `turn_reply.py`: `ChatReply` = the reply and cards, plus action cards built
  only from successful cart tool results (`added`, `updated`, `removed`, and
  one `checkout` card) and the cart as it is after the turn. Cart writes are
  part of the turn's transaction, so a failed or timed-out turn undoes them.
- `prompt.py`: `system_prompt(restaurant, others)`, built each turn for the
  conversation's restaurant: its name, cuisine and categories, how to handle
  options, ordering (change the cart only when asked, explain a refused
  add, propose checkout but never place an order), and the other restaurants
  (suggest by name, never search).

Depends on: `tools`, `memory`, `safety`, `orders`, `users`, `menu`. Used by: `api/chat.py`.
