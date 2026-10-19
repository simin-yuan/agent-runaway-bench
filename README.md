# agent-runaway-bench

What does an agent framework do when the model gets stuck repeating itself mid-reply?

This repo answers that with one fake model endpoint and the same measurement for every framework.
`loop_server.py` streams a single sentence on repeat (about 300,000 characters) over the OpenAI
Chat Completions or Responses wire, and logs two things per request: whether the client asked for an
output cap, and how much it read before hanging up.

No API keys, no spend. Anyone can rerun it.

## Results (2026-10-19)

| Framework | Version | Output cap sent | Read before stopping | What the user gets |
|---|---|---|---|---|
| Hermes Agent, chat-completions wire (control) | `5fc490e` | none | **16,168 chars** | "Repetition Detected", partial discarded |
| OpenAI Agents SDK, Chat Completions model | 0.24.0 | none | 300,048 (all) | the whole loop as the final output |
| OpenAI Agents SDK, Responses model | 0.24.0 | none | 300,048 (all) | the whole loop as the final output |
| OpenAI Codex CLI, `codex exec` | 0.163.0 | none | 300,048 (all) | the whole loop printed to stdout |
| smolagents, `ToolCallingAgent` | 1.26.0 | none | 300,048 (all) | the whole loop streamed |
| LangGraph, `create_react_agent` | 1.2.16 | none | 300,048 (all) | the whole loop streamed |

Every row has its own raw server log in [`results/`](results/). smolagents made a second request after
its step limit; it also read the whole stream (details in `results/README.md`).

OpenHands SDK 1.55.1 is not listed: a fresh install failed at import time on a dependency error, so it
could not be measured.

**The control matters.** The same server and the same measurement detect Hermes's mid-stream guard,
so "read it all" in the other rows is how those frameworks behave, not a blind spot of the test.

The guard itself decides at 16,074 characters — the chunk boundary that crosses its 16,000-character
floor. The 16,168 above is what the endpoint had already pushed when the client hung up: one further
94-character chunk. Both numbers come from the same run and measure different sides of the wire.

## Why it matters

Most frameworks guard against loops across turns (max turns, repeated tool calls). Almost none guard
against a loop inside a single streamed reply. That used to be bounded by the output cap, but caps
are being dropped to avoid truncating long answers, and none of the clients above sent one. With no
cap and no mid-stream check, a looping model runs until the model's own output limit, and the loop
becomes the answer.

Real models do this. Hermes documents one incident where a 60,000-character looping reply went out as
31 chat messages (`agent/repetition_guard.py`).

## Scope and limits

- This measures the framework, not the provider. Whether a hosted API stops a loop server-side was not
  tested.
- The stream is synthetic and paced at about 48,000 chars/s, faster than real models.
- Hermes itself is the control here only on its chat-completions wire. Its Bedrock and Codex streams
  did not have the guard at `5fc490e`; that is reported to the upstream project separately, with a fix
  and tests, and is not claimed as fixed here.

## Run it

```sh
python3 loop_server.py 8765 300000 log.jsonl &   # port, total chars, log file
python runners/openai_agents_sdk.py chat          # or: responses
python runners/smolagents_langgraph.py smolagents # or: langgraph
sh runners/codex_cli.sh
sh runners/hermes.sh
cat log.jsonl
```

Each line of `log.jsonl` records the path, the cap the client sent (if any), the characters streamed,
and whether the client hung up early.

## Adding a framework

Point its OpenAI-compatible base URL at `http://127.0.0.1:8765/v1`, ask it anything, and read the log.
Pull requests with new rows are welcome.
