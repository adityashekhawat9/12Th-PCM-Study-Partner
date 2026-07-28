from pathlib import Path
from typing import Final


DEFAULT_MODEL: Final[str] = "llama-3.1-8b-instant"

# Data paths
DATA_DIR: Final[Path] = Path(__file__).parent.parent / "data"
INDEX_PATH: Final[Path] = DATA_DIR / "index.faiss"
METADATA_PATH: Final[Path] = DATA_DIR / "metadata.json"

SYSTEM_PROMPT: Final[str] = (
    "You are an AI tutor for Class 12 CBSE Mathematics, Physics, and Chemistry. "
    "You MUST only answer questions related to these three subjects. "
    "If the user asks something outside of Class 12 PCM (like cricket, general knowledge, etc.), "
    "politely refuse to answer and remind them of your purpose. "
    "When answering, use the provided textbook context to give accurate, step-by-step explanations. "
    "Include citations to the textbook and page number based on the context."
)
