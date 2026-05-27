from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnablePassthrough
# from langchain_google_genai import GoogleGenerativeAIEmbeddings

from prompts.rag import GENERATE_RAG_ANSWER_PROMPT, GENERATE_RAG_QUERIES_PROMPT

from .shared import RAGQueriesOutput, get_llm

from langchain_cohere import CohereEmbeddings


import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

@lru_cache
def get_retriever():
    return (
        Chroma(
            persist_directory="db",
            embedding_function=CohereEmbeddings(
    model="embed-english-v3.0"
)

        )
        .as_retriever(search_type="mmr", search_kwargs={"k": 5, "fetch_k": 15})
    )


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def build_rag_query_designer():
    return (
        PromptTemplate.from_template(GENERATE_RAG_QUERIES_PROMPT)
        | get_llm().with_structured_output(RAGQueriesOutput)
    )


def build_rag_answer_generator():
    return (
        {
            "context": get_retriever() | format_docs,
            "question": RunnablePassthrough()
        }
        | ChatPromptTemplate.from_template(GENERATE_RAG_ANSWER_PROMPT)
        | get_llm()
        | StrOutputParser()
    )
