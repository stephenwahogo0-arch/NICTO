"""ChatML template system for proper prompt formatting.
Uses <|im_start|>/<|im_end|> boundaries as specified in the blueprint."""


def format_chatml(messages: list[dict], system_prompt: str = "") -> str:
    """Format messages into ChatML template.
    
    Args:
        messages: List of dicts with 'role' and 'content' keys
        system_prompt: Optional system prompt override
    
    Returns:
        Properly formatted ChatML string
    """
    parts = []
    
    # Extract system message from messages or use provided
    system = system_prompt
    for m in messages:
        if m.get("role") == "system":
            system = m.get("content", "")
    
    if system:
        parts.append(f"<|im_start|>system\n{system}\n<|im_end|>")
    
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "system":
            continue  # Already handled above
        parts.append(f"<|im_start|>{role}\n{content}\n<|im_end|>")
    
    parts.append("<|im_start|>assistant\n")
    return "\n".join(parts)


def format_chatml_with_context(
    user_input: str,
    system_prompt: str,
    conversation_history: list[tuple[str, str]] = None,
    memory_context: str = "",
) -> str:
    """Format a full request with system prompt, history, and user input."""
    parts = []
    
    # System prompt
    parts.append(f"<|im_start|>system\n{system_prompt}\n<|im_end|>")
    
    # Memory context as system extension
    if memory_context:
        parts.append(f"<|im_start|>system\nRelevant context:\n{memory_context}\n<|im_end|>")
    
    # Conversation history
    if conversation_history:
        for user_msg, asst_msg in conversation_history[-(6):]:  # Last 6 exchanges
            parts.append(f"<|im_start|>user\n{user_msg}\n<|im_end|>")
            parts.append(f"<|im_start|>assistant\n{asst_msg}\n<|im_end|>")
    
    # Current user input
    parts.append(f"<|im_start|>user\n{user_input}\n<|im_end|>")
    parts.append("<|im_start|>assistant\n")
    
    return "\n".join(parts)


def extract_response(text: str) -> str:
    """Extract assistant response from ChatML-formatted output."""
    if "<|im_start|>assistant" in text:
        text = text.split("<|im_start|>assistant")[-1]
    if "<|im_end|>" in text:
        text = text.split("<|im_end|>")[0]
    return text.strip()


def count_tokens(text: str) -> int:
    """Rough token count estimate (chars / 3.5)."""
    return int(len(text) / 3.5)
