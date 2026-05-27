from enum import Enum
from functools import lru_cache
from typing import List

from langchain_groq import ChatGroq
from pydantic import BaseModel, Field


@lru_cache
def get_llm():
    return ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.1)


class EmailCategory(str, Enum):
    PRODUCT_ENQUIRY = "product_enquiry"
    CUSTOMER_COMPLAINT = "customer_complaint"
    CUSTOMER_FEEDBACK = "customer_feedback"
    UNRELATED = "unrelated"
    product_enquiry = "product_enquiry"
    customer_complaint = "customer_complaint"
    customer_feedback = "customer_feedback"
    unrelated = "unrelated"


class CategorizeEmailOutput(BaseModel):
    category: EmailCategory = Field(
        ...,
        description="Predicted category of the customer email."
    )


class RAGQueriesOutput(BaseModel):
    queries: List[str] = Field(
        ...,
        min_length=1,
        max_length=3,
        description=(
            "List of semantic search queries representing the user's intent."
        )
    )


class WriterOutput(BaseModel):
    email: str = Field(
        ...,
        min_length=1,
        description=(
            "Professional draft email response generated for the customer."
        )
    )


class ProofReaderOutput(BaseModel):
    send: bool = Field(
        ...,
        description="Whether the generated email is approved for sending."
    )

    feedback: str = Field(
        ...,
        min_length=1,
        description="Feedback explaining issues or improvements required."
    )
