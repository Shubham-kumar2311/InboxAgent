from typing import List, Annotated
from typing_extensions import TypedDict

from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages



class Email(BaseModel):

    id: str = Field(
        ...,
        description="Unique Gmail message ID"
    )

    threadId: str = Field(
        ...,
        description="Gmail conversation thread ID"
    )

    messageId: str = Field(
        ...,
        description="RFC message identifier"
    )

    references: str = Field(
        default="",
        description="Email references header"
    )

    sender: str = Field(
        ...,
        description="Sender email address"
    )

    receiver: str = Field(
        default="",
        description="Receiver email address"
    )

    subject: str = Field(
        default="No Subject",
        description="Email subject"
    )

    body: str = Field(
        default="",
        description="Email body content"
    )

    snippet: str = Field(
        default="",
        description="Short Gmail email preview"
    )

    date: str = Field(
        default="",
        description="Email sent date"
    )

    has_attachments: bool = Field(
        default=False,
        description="Whether email contains attachments"
    )




class GraphState(TypedDict):

    emails: List[Email]     # All pending emails
    current_email: Email
    email_category: str
    generated_email: str        # Generated AI response
    rag_queries: List[str]      # Queries generated for RAG
    retrieved_documents: str
    # LangGraph conversation history
    writer_messages: Annotated[
        list,
        add_messages
    ]
    sendable: bool
    trials: int
    rewrite_count: int = 0