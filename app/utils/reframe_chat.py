"""Text reframing utility for improving chat messages.

This module provides a dependency-injected service for correcting and reframing
user input messages using LLM providers. Uses LLMFactoryInterface with tool-free
LLM instances for optimal text correction performance.

Example:
    ```python
    from app.core.di_container import inject
    from app.utils.reframe_chat import ReframeChat

    # Using dependency injection (recommended)
    reframer = inject(ReframeChat)
    corrected = reframer.correct("i need halp with my cod")
    # Returns: "I need help with my code"

    # Direct instantiation
    reframer = ReframeChat()
    corrected = reframer.correct("bad grammer text")
    ```

Dependencies:
    - LLMFactoryInterface: Creates tool-free LLM instances for text correction
    - LLMProvider enum: Specifies which LLM provider to use
"""

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.ai_core import LLMFactoryInterface
from app.core.di_container import inject
from app.core.enums import LLMProvider
from app.core.errors import AppError

logger = logging.getLogger(__name__)


def _ensure_content_format(content):
    """Ensure content is properly formatted for Ollama models."""
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    elif isinstance(content, list):
        # Check if list contains properly formatted content parts
        formatted_parts = []
        for part in content:
            if isinstance(part, str):
                formatted_parts.append({"type": "text", "text": part})
            elif isinstance(part, dict) and "type" in part:
                formatted_parts.append(part)
            else:
                formatted_parts.append({"type": "text", "text": str(part)})
        return formatted_parts
    else:
        return [{"type": "text", "text": str(content)}]


class ReframeChat:
    """Text correction service using tool-free LLM instances.

    Provides text correction capabilities using LLMFactoryInterface with
    tool-free LLM instances to avoid interference from agent tools.

    Attributes:
        correction_llm (BaseChatModel): Tool-free LLM instance for text correction

    Example:
        ```python
        # Using DI (recommended)
        reframer = inject(ReframeChat)
        result = reframer.correct("fix this sentnce")

        # Direct instantiation
        reframer = ReframeChat()
        result = reframer.correct("bad text")
        ```
    """

    def __init__(self, llm_correction_model: LLMProvider = LLMProvider.LLM_CORRECTION_MODEL):
        """Initialize the ReframeChat service.

        Args:
            llm_correction_model: LLM provider type to use for text correction.
                         Defaults to LLM_MEDIUM_MODEL.
        """
        logger.info("Initializing ReframeChat service...")
        try:
            # Create tool-free LLM instance using the updated factory
            llm_factory = inject(LLMFactoryInterface)
            self.correction_llm = llm_factory.create_model(
                llm_provider_type=llm_correction_model,
                temperature=0.2,  # Lower temperature for consistent corrections
                with_tools=False,  # No tools for text correction
            )
            logger.info(f"ReframeChat service initialized with {llm_correction_model} (tool-free)")
        except Exception as e:
            logger.error(f"Failed to initialize ReframeChat service: {e}")
            raise

    def correct(self, text: str) -> str:
        """Correct and reframe the provided text.

        Args:
            text: The text to be corrected and reframed

        Returns:
            str: The corrected and reframed text

        Raises:
            AppError: If text correction fails
            ValueError: If input text is empty or None
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty or None")

        logger.info("Correcting text: %s", text[:50] + "..." if len(text) > 50 else text)

        try:
            # Prepare messages for LLM
            messages = [
                SystemMessage(
                    content=_ensure_content_format("Fix grammar and spelling errors. Return ONLY the corrected text, nothing else.")
                ),
                HumanMessage(content=_ensure_content_format(text)),
            ]

            # Get correction from LLM
            corrected_response = self.correction_llm.invoke(messages)

            # Extract corrected text
            if hasattr(corrected_response, "content"):
                corrected_text = str(corrected_response.content).strip()
            else:
                corrected_text = str(corrected_response).strip()

            # Fallback to original text if correction is empty
            if not corrected_text:
                logger.warning("LLM returned empty response, falling back to original text")
                corrected_text = text.strip()

            logger.info("Text correction completed: %s → %s", text, corrected_text)
            return corrected_text

        except Exception as e:
            logger.error(f"Failed to correct text '{text}': {e}")
            raise AppError(f"Text correction failed: {e!s}") from e


def create_reframe_chat_service() -> ReframeChat:
    """Factory function to create ReframeChat service with DI.

    Returns:
        ReframeChat: Configured ReframeChat service instance
    """
    return ReframeChat()