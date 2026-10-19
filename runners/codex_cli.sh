#!/bin/sh
# OpenAI Codex CLI against the loop server (Responses wire). Prints how much text reached stdout.
export LOOP_KEY=dummy
codex exec --skip-git-repo-check \
  -c 'model_providers.loop={name="loop",base_url="http://127.0.0.1:8765/v1",wire_api="responses",env_key="LOOP_KEY"}' \
  -c model_provider=loop -m loop-model "hello" < /dev/null > codex_out.txt 2> codex_err.txt
echo "codex exit=$? stdout chars=$(wc -c < codex_out.txt)"
