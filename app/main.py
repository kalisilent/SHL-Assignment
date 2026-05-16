from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from app.models import ChatRequest, ChatResponse
from app.retriever import CatalogRetriever
from app.agent import Agent
from app.sanitizer import sanitize_chat_response

retriever = None
agent = None

# This lifespan function loads FAISS and Gemini exactly ONCE when the server starts.
# If we loaded them on every request, we would fail SHL's 30-second timeout rule.
@asynccontextmanager
async def lifespan(app: FastAPI):
    global retriever, agent
    print("Starting up: Loading FAISS index and initializing Agent...")
    retriever = CatalogRetriever("data/catalog.json", "data/catalog.index")
    agent = Agent(retriever)
    print("System Ready!")
    yield

app = FastAPI(lifespan=lifespan)

# Required by assignment: GET /health returns {"status": "ok"}
@app.get("/health")
def health():
    return {"status": "ok"}

# Required by assignment: POST /chat takes history and returns ChatResponse

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # Enforce max 8 turns (user + assistant) per conversation as required.
    total_turns = len(request.messages)
    if total_turns > 8:
        return ChatResponse(
            reply="Turn limit reached. Please start a new request with your final constraints.",
            recommendations=[],
            end_of_conversation=False,
        )

    try:
        # Pass the message history to our Gemini agent.
        response = await agent.respond(request.messages, turn_count)
        # Sanitize and canonicalize the agent response to guarantee the strict schema
        try:
            sanitized = sanitize_chat_response(response, retriever.catalog)
            return sanitized
        except Exception as e:
            print(f"Sanitizer error: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        print(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")