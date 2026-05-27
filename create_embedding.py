from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os

load_dotenv()

RAG_SEARCH_PROMPT_TEMPLATE = """
You are a professional AI assistant specialized in answering questions accurately using the provided knowledge base.

Your task is to generate clear, concise, and helpful responses strictly based on the retrieved context.

Guidelines:
- Answer the question directly and professionally.
- Use only the information available in the provided context.
- Do not make up, assume, or hallucinate information.
- If the answer is not available in the context, reply with exactly: "I don't know."
- Never mention the existence of context, documents, retrieval systems, or external information.
- Keep responses natural and human-like.
- For pricing, plans, features, policies, or technical details, provide complete relevant information from the context.
- If multiple relevant details exist, summarize them clearly in bullet points when appropriate.

Question:
{question}

Context:
{context}

Answer:
"""

print("Loading & Chunking Docs...")
loader = TextLoader("./data/company_internal_knowledge.txt")
docs = loader.load()

doc_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,
    separators=["\n\n", "\n", ".", " ", ""]
)
doc_chunks = doc_splitter.split_documents(docs)

print("Creating vector embeddings...")
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

if not os.path.exists("db"):
    vectorstore = Chroma.from_documents(
        documents=doc_chunks,
        embedding=embeddings,
        persist_directory="db"
    )
else:
    vectorstore = Chroma(
        persist_directory="db",
        embedding_function=embeddings
    )

# vectorstore_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})