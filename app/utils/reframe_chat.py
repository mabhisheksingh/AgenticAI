"""Text reframing utility for improving chat messages.

This module provides a dependency-injected service for correcting and reframing
user input messages using LLM providers. It follows the DIP principle by depending
on abstractions (LLMProviderInterface) rather than concrete implementations.

Example:
    ```python
    from app.core.di_container import inject
    from app.utils.reframe_chat import ReframeChat
    
    # Using dependency injection
    reframer = inject(ReframeChat)
    corrected = reframer.correct("i need halp with my cod")
    # Returns: "I need help with my code"
    
    # Direct instantiation (not recommended)
    reframer = ReframeChat()
    corrected = reframer.correct("bad grammer text")
    ```

Dependencies:
    - LLMProviderInterface: For creating LLM instances
    - LLMProvider enum: For specifying which provider to use
"""
import logging
from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from app.agents import LLMProviderInterface
from app.core.di_container import inject
from app.core.enums import LLMProvider
from app.core.errors import AppError

logger = logging.getLogger(__name__)


class ReframeChat:
    """Text correction service with dependency injection support.
    
    This service provides text correction capabilities using configurable LLM 
    providers. It uses dependency injection to maintain loose coupling with 
    LLM implementations.
    
    Attributes:
        _llm_provider (LLMProviderInterface): Injected LLM provider factory
        _ollama_llm (BaseChatModel): Cached Ollama LLM instance
        
    Example:
        ```python
        # Using DI (recommended)
        reframer = inject(ReframeChat)
        result = reframer.correct("fix this sentnce")
        
        # Manual instantiation
        reframer = ReframeChat()
        result = reframer.correct("bad text")
        ```
    """
    
    def __init__(self, llm_provider: Optional[LLMProviderInterface] = None):
        """Initialize the ReframeChat service.
        
        Args:
            llm_provider: Optional LLM provider. If None, will be injected
                         automatically using the DI container.
                         
        Note:
            When using dependency injection (recommended), pass None or omit
            this parameter. The DI container will automatically provide the
            appropriate LLMProviderInterface implementation.
        """
        logger.info("Initializing ReframeChat service...")
        
        # Use dependency injection if no provider specified
        if llm_provider is None:
            try:
                self._llm_provider = inject(LLMProviderInterface)
                logger.debug("LLM provider injected successfully")
            except Exception as e:
                logger.error(f"Failed to inject LLM provider: {e}")
                raise AppError("Failed to initialize text reframing service") from e
        else:
            self._llm_provider = llm_provider
            logger.debug("LLM provider provided manually")
        
        # Initialize LLM instance (lazy loading)
        self._ollama_llm: Optional[BaseChatModel] = None
        logger.info("ReframeChat service initialized successfully")
    
    @property
    def ollama_llm(self) -> BaseChatModel:
        """Get or create the Ollama LLM instance.
        
        Returns:
            BaseChatModel: Configured Ollama LLM instance
            
        Raises:
            AppError: If LLM creation fails
        """
        if self._ollama_llm is None:
            try:
                logger.debug("Creating Ollama LLM instance...")
                self._ollama_llm = self._llm_provider.create_model(provider=LLMProvider.ollama)
                logger.debug("Ollama LLM instance created successfully")
            except Exception as e:
                logger.error(f"Failed to create Ollama LLM: {e}")
                raise AppError("Failed to create LLM instance for text reframing") from e
        
        return self._ollama_llm
    
    def correct(self, text: str) -> str:
        """Correct and reframe the provided text.
        
        Uses the configured LLM to improve grammar, spelling, and clarity
        of the input text while preserving the original meaning.
        
        Args:
            text: The text to be corrected and reframed
            
        Returns:
            str: The corrected and reframed text
            
        Raises:
            AppError: If text correction fails
            ValueError: If input text is empty or None
            
        Example:
            ```python
            reframer = inject(ReframeChat)
            
            # Basic correction
            result = reframer.correct("i need halp")
            # Returns: "I need help"
            
            # Complex reframing
            result = reframer.correct("can u tell me how 2 do this thing?")
            # Returns: "Can you tell me how to do this?"
            ```
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty or None")
        
        logger.info("Correcting text: %s", text[:50] + "..." if len(text) > 50 else text)
        
        try:
            # Prepare messages for LLM
            system_prompt = (
                "You are a text correction assistant. Fix grammar, spelling, and clarity "
                "in the given text while preserving the original meaning. Return ONLY the "
                "corrected text with no additional explanation, commentary, or formatting."
            )
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=text)
            ]
            
            # Get correction from LLM
            logger.debug("Invoking LLM for text correction...")
            corrected_response = self.ollama_llm.invoke(messages)
            
            # Handle different response content types
            if hasattr(corrected_response, 'content'):
                content = corrected_response.content
                if isinstance(content, str):
                    corrected_text = content.strip()
                elif isinstance(content, list) and content:
                    # Handle list content by joining or taking first item
                    corrected_text = str(content[0]).strip() if content else text
                else:
                    corrected_text = str(content).strip()
            else:
                corrected_text = str(corrected_response).strip()
            
            # Log results
            logger.info(
                "Text correction completed: %s", 
                corrected_text[:50] + "..." if len(corrected_text) > 50 else corrected_text
            )
            logger.debug("Original: %s", text)
            logger.debug("Corrected: %s", corrected_text)
            
            return corrected_text
            
        except Exception as e:
            logger.error(f"Failed to correct text: {e}")
            logger.error(f"Original text: {text}")
            raise AppError(f"Text correction failed: {str(e)}") from e


# Factory function for dependency injection
def create_reframe_chat_service() -> ReframeChat:
    """Factory function to create ReframeChat service with DI.
    
    Returns:
        ReframeChat: Configured ReframeChat service instance
    """
    return ReframeChat()
