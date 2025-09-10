import logging

from app.ai_core import LLMFactoryInterface
from app.core.enums import LLMProvider

logger = logging.getLogger(__name__)


class MT5Service:
    """Text correction service using configurable LLM models.

    Provides optimized methods for translation, summarization,
    and multilingual text processing using the configured correction model.
    """

    def __init__(self, llm_factory: LLMFactoryInterface):
        """Initialize MT5Service with provided LLM factory.

        Args:
            llm_factory: LLM factory instance for creating models
        """
        self.mt5_model = llm_factory.create_model(
            llm_provider_type=LLMProvider.LLM_CORRECTION_MODEL,
            temperature=0.3,
            with_tools=False,  # Text correction works better without tools
        )
        logger.info("MT5Service initialized with configured correction model")

    def translate(self, text: str, target_language: str = "English") -> str:
        """Translate text to target language using mT5.

        Args:
            text: Text to translate
            target_language: Target language (e.g., "English", "Hindi", "Spanish")

        Returns:
            str: Translated text
        """
        # Use proper mT5 format for translation
        prompt = f"translate {target_language}: {text}"
        response = self.mt5_model.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    def summarize(self, text: str, max_length: int = 150) -> str:
        """Summarize text using mT5.

        Args:
            text: Text to summarize
            max_length: Maximum length of summary

        Returns:
            str: Summarized text
        """
        prompt = f"summarize: {text}"
        response = self.mt5_model.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    def correct_grammar1(self, text: str) -> str:
        """Correct grammar using prithivida/grammar_error_correcter_v1 model.

        Args:
            text: Text to correct

        Returns:
            str: Corrected text
        """
        logger.info(f"Correcting grammar: {text}")

        # Try multiple prompt formats for better correction
        prompt_formats = [
            f"gec: {text}",
            f"grammar error correction: {text}",
            f"correct grammar: {text}",
            text,  # Try without prefix
        ]

        for prompt in prompt_formats:
            try:
                response = self.mt5_model.invoke(prompt)
                corrected_text = response.content if hasattr(response, "content") else str(response)

                # Check if we got a meaningful response that's different from input
                if (
                    corrected_text
                    and corrected_text.strip() != text.strip()
                    and len(corrected_text.strip()) > 0
                    and corrected_text.strip().lower() != text.strip().lower()
                ):
                    logger.info(f"Grammar corrected: {corrected_text}")
                    return corrected_text.strip()
            except Exception as e:
                logger.warning(f"Grammar correction failed with prompt '{prompt}': {e}")
                continue

        # Fallback: return original text
        logger.info("Returning original text (grammar correction not effective for this text)")
        return text

    def correct_grammar(self, text: str) -> str:
        """Correct grammar using vennify/t5-base-grammar-correction model."""
        logger.info(f"Correcting grammar: {text}")

        try:
            # Always prepend the correct prefix
            prompt = f"gec: {text}"
            response = self.mt5_model.invoke(prompt)

            corrected_text = response.content if hasattr(response, "content") else str(response)

            if corrected_text and corrected_text.strip() != text.strip():
                logger.info(f"Grammar corrected: {corrected_text}")
                return corrected_text.strip()
        except Exception as e:
            logger.warning(f"Grammar correction failed: {e}")

        # Fallback
        return text
