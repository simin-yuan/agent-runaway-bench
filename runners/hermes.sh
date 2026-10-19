#!/bin/sh
# Hermes Agent (chat-completions wire) against the loop server: the positive control.
export HERMES_HOME="$(mktemp -d)" OPENAI_API_KEY=dummy
hermes config set model.provider custom >/dev/null
hermes config set model.base_url http://127.0.0.1:8765/v1 >/dev/null
hermes config set model.default loop-model >/dev/null
hermes chat -q "hello" --oneshot -Q < /dev/null | head -c 200; echo
