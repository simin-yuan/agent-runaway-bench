import sys
kind = sys.argv[1]
B = "http://127.0.0.1:8765/v1"
if kind == "smolagents":
    from smolagents import ToolCallingAgent, OpenAIServerModel
    m = OpenAIServerModel(model_id="loop-model", api_base=B, api_key="dummy")
    a = ToolCallingAgent(tools=[], model=m, stream_outputs=True, max_steps=1, verbosity_level=0)
    n = 0
    try:
        for ev in a.run("hello", stream=True):
            c = getattr(ev, "content", None)
            if isinstance(c, str) and type(ev).__name__ == "ChatMessageStreamDelta": n += len(c)
    except Exception as e:
        print("exception:", type(e).__name__, str(e)[:120])
    print("smolagents streamed chars:", n)
else:
    from langchain_openai import ChatOpenAI
    from langgraph.prebuilt import create_react_agent
    llm = ChatOpenAI(model="loop-model", base_url=B, api_key="dummy", streaming=True)
    g = create_react_agent(llm, tools=[])
    n = 0
    for chunk, meta in g.stream({"messages": [("user", "hello")]}, stream_mode="messages"):
        if isinstance(chunk.content, str): n += len(chunk.content)
    print("langgraph streamed chars:", n)
