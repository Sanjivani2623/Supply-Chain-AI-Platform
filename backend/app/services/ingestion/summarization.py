"""
Summarization service.

Preserves the existing TextRank/Sumy approach from the original notebook
(Infosys_Intern_Proj_Data.ipynb) as the default/baseline summarizer, and
exposes an abstraction so alternative summarizers (LLM-based) can be
swapped in via configuration without touching callers.
"""
from abc import ABC, abstractmethod

from app.services.ingestion.preprocessing import clean_text


class BaseSummarizer(ABC):
    @abstractmethod
    def summarize(self, content: str, num_sentences: int = 3) -> str:
        ...


class TextRankSummarizer(BaseSummarizer):
    """Direct refactor of the notebook's `summarize_content_textrank`."""

    def summarize(self, content: str, num_sentences: int = 3) -> str:
        content = clean_text(content)
        if not content:
            return ""
        try:
            from sumy.parsers.plaintext import PlaintextParser
            from sumy.nlp.tokenizers import Tokenizer
            from sumy.summarizers.text_rank import TextRankSummarizer as SumyTextRank

            parser = PlaintextParser.from_string(content, Tokenizer("english"))
            summarizer = SumyTextRank()
            sentences = summarizer(parser.document, num_sentences)
            return " ".join(str(s) for s in sentences)
        except Exception:
            # Fallback: first N sentences by naive split, keeps pipeline resilient
            parts = content.split(". ")
            return ". ".join(parts[:num_sentences])


def get_summarizer(strategy: str = "textrank") -> BaseSummarizer:
    if strategy == "textrank":
        return TextRankSummarizer()
    raise ValueError(f"Unknown summarization strategy: {strategy}")
