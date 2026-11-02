#!/bin/sh
# run_runaway.sh API RUN — one runaway cell; mirrors agent-runaway-bench README (port, 300000 chars, log file).
# API: chat (llm api_type default) | responses. Env: BENCH_C (agent-runaway-bench checkout), NATPY, OUTBASE.
API=$1; RUN=$2; HERE=$(cd "$(dirname "$0")" && pwd)
OUT="$OUTBASE/nat-tool_calling_agent-$API/run$RUN"; rm -rf "$OUT"; mkdir -p "$OUT/work"
PORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
python3 "$BENCH_C/loop_server.py" "$PORT" 300000 "$OUT/server.jsonl" & SP=$!
sleep 0.5
S=$(date +%s.%N)
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost NAT_API_TYPE=$API timeout -s KILL 600 "$NATPY" "$HERE/nat_bench.py" runaway \
  "http://127.0.0.1:$PORT/v1" "$OUT/work" > "$OUT/client.txt" 2>&1; echo "exit=$? wall_s=$(python3 -c "print(round($(date +%s.%N)-$S,2))")" >> "$OUT/client.txt"
sleep 0.5; kill $SP 2>/dev/null; wait $SP 2>/dev/null; rm -rf "$OUT/work"
echo "runaway $API run$RUN $(cat "$OUT/server.jsonl" | tr '\n' ' ') $(grep -E 'returned|exception' "$OUT/client.txt")"
