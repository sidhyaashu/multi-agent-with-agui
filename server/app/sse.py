import json

def sse_event(event_type:str,payload:dict) -> str:
    body = {"type":event_type,**payload}
    return f"data: {json.dumps(body,ensure_ascii=False)}\n\n"