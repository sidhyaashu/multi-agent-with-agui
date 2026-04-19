from pydantic import BaseModel,Field

class ChatRequest(BaseModel):
    message:str=Field(...,min_length=1)
    location:str = "Kolkata"
    thread_id:str | None = None

