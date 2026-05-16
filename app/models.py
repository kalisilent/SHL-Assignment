from pydantic import BaseModel, Field
from typing import List, Literal

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)

    class Config:
        extra = "forbid"

class ChatRequest(BaseModel):
    messages: List[Message] = Field(min_length=1)

    class Config:
        extra = "forbid"

class Recommendation(BaseModel):
    name: str = Field(min_length=1)
    url: str = Field(min_length=1)
    test_type: str = Field(min_length=1)

    class Config:
        extra = "forbid"

class ChatResponse(BaseModel):
    reply: str = Field(min_length=1)
    # It must be an empty list [], NOT null, when not recommending
    recommendations: List[Recommendation] = Field(default_factory=list, max_length=10)
    end_of_conversation: bool

    class Config:
        extra = "forbid"