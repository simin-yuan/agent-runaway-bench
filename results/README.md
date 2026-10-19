# Raw records, 2026-10-19

One fresh `loop_server.py` per client (port 8765, 300,000 characters, same pacing as in the repo),
each writing its own log, run back to back on Ubuntu 24.04.

- `<client>.jsonl`: the server's record of every request from that client: path, output cap sent,
  characters streamed, whether the client hung up early, seconds.
- `<client>_client.txt`: what the client itself reported or printed.

| Client | Version | Server record |
|---|---|---|
| Hermes Agent, chat-completions wire | `5fc490e`, unmodified | `hermes.jsonl` |
| OpenAI Agents SDK, Chat Completions model | 0.24.0 | `openai-agents-sdk-chat.jsonl` |
| OpenAI Agents SDK, Responses model | 0.24.0 | `openai-agents-sdk-responses.jsonl` |
| OpenAI Codex CLI, `codex exec` | 0.163.0 | `codex-cli.jsonl` |
| smolagents, `ToolCallingAgent` | 1.26.0 | `smolagents.jsonl` |
| LangGraph, `create_react_agent` (langchain-openai 1.7.2) | 1.2.16 | `langgraph.jsonl` |

smolagents made two requests. The runner sets `max_steps=1`, and when the first reply is not a tool
call or final answer, the agent asks the model once more for a final answer. Both requests read the
whole stream.

Timings depend on the machine and are not compared anywhere; the character counts are what matter.
