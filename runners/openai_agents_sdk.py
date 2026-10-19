import asyncio, sys
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, OpenAIResponsesModel, set_tracing_disabled
set_tracing_disabled(True)
client = AsyncOpenAI(base_url="http://127.0.0.1:8765/v1", api_key="dummy")
async def go(kind):
    model = OpenAIChatCompletionsModel("loop-model", client) if kind == "chat" else OpenAIResponsesModel("loop-model", client)
    r = Runner.run_streamed(Agent(name="a", instructions="hi", model=model), "hello")
    n = 0
    async for ev in r.stream_events():
        if ev.type == "raw_response_event":
            d = getattr(ev.data, "delta", None)
            if isinstance(d, str) and getattr(ev.data, "type", "") in ("response.output_text.delta",): n += len(d)
    print(kind, "client received chars:", n, "final_output chars:", len(r.final_output or ""))
asyncio.run(go(sys.argv[1]))
