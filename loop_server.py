"""A fake model endpoint that streams one sentence on repeat.
Speaks OpenAI Chat Completions and OpenAI Responses (SSE). Logs, per request:
the output cap the client asked for, chars streamed, and whether the client hung up early."""
import json, sys, time, socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LINE = "I will now check the configuration file again.\n"
TOTAL = int(sys.argv[2]) if len(sys.argv) > 2 else 200_000
CHUNK = LINE * 2
PACE = 0.002  # ~48k chars/s: faster than real models, slow enough to see when a client hangs up
LOG = open(sys.argv[3] if len(sys.argv) > 3 else "server_log.jsonl", "a")

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def _sse(self, obj, event=None):
        data = (f"event: {event}\n" if event else "") + "data: " + (obj if isinstance(obj, str) else json.dumps(obj)) + "\n\n"
        self.wfile.write(data.encode()); self.wfile.flush(); time.sleep(PACE)
    def do_GET(self):
        body = json.dumps({"object": "list", "data": [{"id": "loop-model", "object": "model"}]}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); req = json.loads(self.rfile.read(n) or b"{}")
        cap = {k: req[k] for k in ("max_tokens", "max_completion_tokens", "max_output_tokens") if k in req}
        if not self.path.startswith("/v1/"):
            self.send_response(404); self.send_header("Content-Length", "0"); self.end_headers(); return
        self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
        self.send_response(200); self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache"); self.send_header("Connection", "close"); self.end_headers()
        sent, hung_up, t0 = 0, False, time.time()
        responses = self.path.rstrip("/").endswith("/responses")
        try:
            if responses:
                rid = "resp_1"; item = {"id": "msg_1", "type": "message", "role": "assistant", "status": "in_progress", "content": []}
                base = {"id": rid, "object": "response", "model": "loop-model", "status": "in_progress", "output": []}
                self._sse({"type": "response.created", "response": base}, "response.created")
                self._sse({"type": "response.output_item.added", "output_index": 0, "item": item}, "response.output_item.added")
                self._sse({"type": "response.content_part.added", "item_id": "msg_1", "output_index": 0, "content_index": 0, "part": {"type": "output_text", "text": "", "annotations": []}}, "response.content_part.added")
                while sent < TOTAL:
                    self._sse({"type": "response.output_text.delta", "item_id": "msg_1", "output_index": 0, "content_index": 0, "delta": CHUNK}, "response.output_text.delta"); sent += len(CHUNK)
                text = CHUNK * (sent // len(CHUNK))
                done_item = dict(item, status="completed", content=[{"type": "output_text", "text": text, "annotations": []}])
                self._sse({"type": "response.output_text.done", "item_id": "msg_1", "output_index": 0, "content_index": 0, "text": text}, "response.output_text.done")
                self._sse({"type": "response.output_item.done", "output_index": 0, "item": done_item}, "response.output_item.done")
                self._sse({"type": "response.completed", "response": dict(base, status="completed", output=[done_item], usage={"input_tokens": 10, "output_tokens": sent // 4, "total_tokens": 10 + sent // 4})}, "response.completed")
            else:
                def chunk(delta, fin=None):
                    return {"id": "c1", "object": "chat.completion.chunk", "created": 0, "model": "loop-model", "choices": [{"index": 0, "delta": delta, "finish_reason": fin}]}
                self._sse(chunk({"role": "assistant", "content": ""}))
                while sent < TOTAL:
                    self._sse(chunk({"content": CHUNK})); sent += len(CHUNK)
                self._sse(chunk({}, "stop")); self._sse("[DONE]")
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Windows raises ConnectionAbortedError (WinError 10053) where POSIX raises BrokenPipeError.
            hung_up = True
        LOG.write(json.dumps({"path": self.path, "client_cap": cap or None, "chars_streamed": sent, "client_hung_up_early": hung_up, "secs": round(time.time() - t0, 2)}) + "\n"); LOG.flush()

if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 8765), H).serve_forever()
