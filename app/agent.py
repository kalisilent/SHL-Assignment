import os
import json
import requests
import google.generativeai as genai
from app.models import ChatResponse, Message, Recommendation
from app.retriever import CatalogRetriever
from app.query_builder import build_queries
from app.conversation_policy import should_recommend, is_off_topic_or_refusal, is_compare_turn
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class Agent:
    def __init__(self, retriever: CatalogRetriever):
        self.retriever = retriever
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-5.4")

        self.system_prompt = """You are the SHL Expert Assessment Consultant.
Your goal is to help hiring managers choose SHL assessments using ONLY the catalog context below.

## BEHAVIOR
- **Clarify** when the request is vague and you lack role/seniority/focus (recommendations must be []).
- **Recommend** when you have enough context: write a concise reply; the system attaches catalog shortlist separately.
- **Refine** when constraints change: acknowledge adds/removals in your reply.
- **Compare** when asked about differences between named assessments: explain using catalog fields only; recommendations stay [].
- **Refuse** legal, regulatory, general hiring, or off-topic requests politely; recommendations stay [].
- **Scope:** Never invent URLs or product names. Never recommend outside SHL catalog.

## SYNONYMS
- OPQ / OPQ32 -> Occupational Personality Questionnaire
- UCF -> OPQ Universal Competency Report
- Verify G+ / G+ -> SHL Verify Interactive G+
- Cognitive -> Verify ability / mental agility tests

## TURN AWARENESS
Turns left in this conversation: {turns_left}. If turns_left <= 2, stop asking questions.

## CATALOG CONTEXT (ranked)
{context}

## OUTPUT (JSON)
Return:
- "reply": string (your message to the user)
- "recommendations": [] unless instructed otherwise below
- "end_of_conversation": boolean

{recommendation_instruction}
"""

    def _retrieve(self, messages: list[Message]) -> list[dict]:
        queries = build_queries(messages)
        if not queries:
            return []
        return self.retriever.search_multi(queries, top_k=10, candidate_k=120)

    @staticmethod
    def _to_recommendations(items: list[dict]) -> list[Recommendation]:
        recs = []
        for item in items[:10]:
            recs.append(
                Recommendation(
                    name=item.get("name", ""),
                    url=item.get("url", ""),
                    test_type=item.get("test_type", ""),
                )
            )
        return recs

    async def respond(self, messages: list[Message], turn_count: int) -> ChatResponse:
        retrieved_items = self._retrieve(messages)
        context_str = json.dumps(retrieved_items, indent=2)

        turns_left = max(0, 8 - turn_count)
        recommend_now = should_recommend(messages, turn_count)
        catalog_recs = self._to_recommendations(retrieved_items) if recommend_now else []

        if is_off_topic_or_refusal(messages):
            recommend_now = False
            catalog_recs = []

        if is_compare_turn(messages):
            recommend_now = False
            catalog_recs = []

        if recommend_now:
            rec_instruction = (
                'The user is ready for a shortlist. Set "recommendations": [] in JSON; '
                "the server will attach the ranked catalog shortlist. Focus your reply on rationale."
            )
        else:
            rec_instruction = (
                'Set "recommendations": [] — you are clarifying, comparing, or refusing.'
            )

        formatted_system_prompt = self.system_prompt.format(
            context=context_str,
            turns_left=turns_left,
            recommendation_instruction=rec_instruction,
        )

        chat_history_str = ""
        for msg in messages[:-1]:
            role_name = "User" if msg.role == "user" else "Agent"
            chat_history_str += f"{role_name}: {msg.content}\n\n"

        current_user_msg = messages[-1].content
        final_prompt = f"""
### PREVIOUS CONVERSATION HISTORY:
{chat_history_str}

### CURRENT USER MESSAGE:
{current_user_msg}
"""

        try:
            if self.openai_base_url and self.openai_api_key:
                response_dict = self._call_openai_compatible(formatted_system_prompt, final_prompt)
            else:
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction=formatted_system_prompt,
                )
                response = model.generate_content(
                    contents=[final_prompt],
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=ChatResponse,
                        temperature=0.1,
                    ),
                )
                response_dict = json.loads(response.text)

            result = ChatResponse(**response_dict)
            if recommend_now and catalog_recs:
                result.recommendations = catalog_recs
            elif not recommend_now:
                result.recommendations = []
            return result
        except Exception:
            if recommend_now and catalog_recs:
                return ChatResponse(
                    reply="Based on your requirements, here is a catalog-grounded shortlist.",
                    recommendations=catalog_recs,
                    end_of_conversation=False,
                )
            return ChatResponse(
                reply="Could you share a bit more about the role, seniority, and skills you need to assess?",
                recommendations=[],
                end_of_conversation=False,
            )

    def _call_openai_compatible(self, system_prompt: str, user_prompt: str) -> dict:
        base_url = self.openai_base_url.rstrip("/")
        endpoint = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}",
        }
        payload = {
            "model": self.openai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }

        response = requests.post(endpoint, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
