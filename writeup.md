# Who stops a runaway loop once the output cap is gone?

Language models sometimes get stuck. Halfway through a reply they start emitting the same line, or the same short paragraph, over and over. For a long time this was mostly harmless, because every request carried an output cap. The loop ran into the cap, the reply ended, and you paid for a few thousand wasted tokens.

That cap is quietly disappearing. Agent frameworks are dropping it so that long answers don't get cut off halfway. I wanted to know what happens to a looping model when nothing caps it, so I built a small test and ran it against six agent setups.

## The test

The test is a fake model endpoint. It speaks the OpenAI Chat Completions and Responses streaming formats and sends one sentence on repeat, about 300,000 characters in total. It logs two things for each request: whether the client asked for an output cap, and how much it read before hanging up.

Every framework gets the same stream and the same measurement. No API key and no spend are involved, so anyone can rerun it. The code, and the raw server log behind every row below, are at [agent-runaway-bench](https://github.com/simin-yuan/agent-runaway-bench).

## What happened

| Framework | Cap sent | Read before stopping |
|---|---|---|
| Hermes Agent (chat-completions wire) | none | 16,168 characters |
| OpenAI Agents SDK 0.24.0, Chat Completions model | none | all 300,048 |
| OpenAI Agents SDK 0.24.0, Responses model | none | all 300,048 |
| OpenAI Codex CLI 0.163.0, `codex exec` | none | all 300,048 |
| smolagents 1.26.0 | none | all 300,048 |
| LangGraph 1.2.16 | none | all 300,048 |

None of the six clients asked for an output cap. Five of them read the loop to the end and handed it back as the answer. In `codex exec` the whole thing was printed to stdout, which in a CI job or a cron task means 300,000 characters of one sentence landing in a log or a downstream step.

Hermes was the exception. It noticed the repetition after about 16,000 characters, closed the stream, discarded the partial reply and told the user the model had looped. That row also matters for a second reason: it shows the test can see a guard when one exists. The other rows aren't an artifact of the setup.

## Two kinds of loop

Most frameworks do protect against loops, just a different kind. Agents get a maximum number of turns or steps. Some count repeated tool calls and stop when the same call comes back too often. Those checks run between turns.

A loop inside a single reply never reaches the next turn. Each turn-level check waits for the reply to finish, and with no output cap the reply finishes only when the model hits its own limit. In practice that means the turn-level guards never get a chance to act on this kind of loop.

Real models do fall into it. Hermes keeps a note in its source about a 60,000-character looping reply that was delivered as 31 chat messages, and the Codex issue tracker has reports of repeated and duplicated output from recent models.

## What a fix looks like

Hermes added its stream guard in #130551. The idea is simple: watch the text as it streams, and once a long stretch is dominated by copies of the same lines, stop reading. The check is cheap and it only fires on long, verbatim repetition, so a user who asks for a phrase fifty times still gets it, and so does a table where every row shares a long suffix.

Even there, the guard had been wired into two of the four streaming paths. While running these tests I found that the Bedrock Converse and Codex Responses paths read a loop to the end. The Bedrock gap stood out, because Hermes's own docs describe Converse as sending no output cap by default, which makes it exactly the path where a stream guard matters most. I sent a fix that reuses the existing guard on both paths, with tests that fail on the current code and pass with the change, plus one test that fails if a future streaming path is added without a guard ([issue #141477](https://github.com/NousResearch/hermes-agent/issues/141477), [PR #141479](https://github.com/NousResearch/hermes-agent/pull/141479)).

Two details from that fix seem worth passing on to anyone adding a guard to their own framework. First, cutting the stream isn't the end of it: Hermes's Codex path drains the rest of a stream after it finishes reading, and without an exception for the cut it would have gone straight back to reading the loop. Second, a loop can start while the model is writing a tool call, so a cut has to drop the half-written call, including anything kept for replay. Otherwise the next request carries a tool call with no result, and the provider rejects it.

## Limits

This measures the frameworks. It says nothing about whether a hosted API stops a looping generation on its own side; I didn't test that, and it would change the cost picture. The stream is synthetic and faster than any real model. And six setups is a sample, not a survey.

## If you maintain an agent framework

Point your client at the fake endpoint, ask it anything, and read the log. If it reads all 300,000 characters, your users are relying on the model's output limit to stop a loop. Results for other frameworks are welcome as pull requests.
