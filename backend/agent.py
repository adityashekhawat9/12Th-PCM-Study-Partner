import json
import os
from pathlib import Path

import faiss
import numpy as np
from groq import Groq
from fastembed import TextEmbedding

from backend.constants import DEFAULT_MODEL, SYSTEM_PROMPT, INDEX_PATH, METADATA_PATH
from backend.types import ChatRequest, ChatResponse


class StarterAgent:
    """Starter agent that candidates will extend or replace."""

    def __init__(self) -> None:
        self.model = os.getenv("MODEL", DEFAULT_MODEL)
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
        self.index = None
        self.metadata = []
        
        # Load local embedding model
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

        if INDEX_PATH.exists() and METADATA_PATH.exists():
            self.index = faiss.read_index(str(INDEX_PATH))
            with open(METADATA_PATH) as f:
                self.metadata = json.load(f)

    def _get_embedding(self, text: str) -> list[float]:
        # fastembed returns a generator of numpy arrays
        return list(self.embedding_model.embed([text]))[0].tolist()

    def answer(self, request: ChatRequest) -> ChatResponse:
        # Get the last user message for retrieval
        last_user_message = next(
            (msg.content for msg in reversed(request.messages) if msg.role == "user"), ""
        )

        context_text = ""
        if self.index is not None and last_user_message:
            # Retrieve top 5 chunks
            query_emb = np.array([self._get_embedding(last_user_message)], dtype=np.float32)
            distances, indices = self.index.search(query_emb, 5)
            
            context_pieces = []
            for idx in indices[0]:
                if idx < len(self.metadata) and idx >= 0:
                    meta = self.metadata[idx]
                    context_pieces.append(f"[Source: {meta['book']}, Page {meta['page']}]\n{meta['text']}")
            
            if context_pieces:
                context_text = "\n\n--- TEXTBOOK CONTEXT ---\n" + "\n\n".join(context_pieces)

        # Inject context into system prompt
        instructions = SYSTEM_PROMPT + context_text

        # The Groq chat.completions API is highly compatible with OpenAI's format
        # However, we need to format the messages properly. 
        # The starter code used `client.responses.create` which is from a very specific or older version of the OpenAI SDK, or a wrapper.
        # Let's use standard ChatCompletions.
        
        # Build messages list
        groq_messages = [{"role": "system", "content": instructions}]
        for msg in request.messages:
            groq_messages.append({"role": msg.role, "content": msg.content})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=groq_messages,
        )
        return ChatResponse(answer=response.choices[0].message.content.strip(), model=self.model)
