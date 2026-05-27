from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os

os.environ["ANONYMIZED_TELEMETRY"] = "False"
load_dotenv()


print("Loading & Chunking Docs...")
loader = TextLoader("./data/company_internal_knowledge.txt")
docs = loader.load()

doc_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,
    separators=["\n\n", "\n", ".", " ", ""]
)
doc_chunks = doc_splitter.split_documents(docs)

from langchain_cohere import CohereEmbeddings

print("Creating vector embeddings...")
# embeddings = GoogleGenerativeAIEmbeddings(model="embedding-001")


embeddings = CohereEmbeddings(
    model="embed-english-v3.0"
)


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
