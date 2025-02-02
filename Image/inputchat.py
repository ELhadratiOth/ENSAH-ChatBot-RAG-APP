from pydantic import BaseModel, Field

class InputChat(BaseModel):
    """Input for the chat endpoint."""

    # The field extra defines a chat widget.
    # As of 2024-02-05, this chat widget is not fully supported.
    # It's included in documentation to show how it should be specified, but
    # will not work until the widget is fully supported for history persistence
    # on the backend.
    input: str = Field(
        ...,
        description="The human input to the chat system.",
        extra={"widget": {"type": "chat", "input": "input"}},
    )