from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
documents = [
    {
        "content": "ENSA Al Hoceima Academic Calendar 2024-2025",
        "metadata": {
            "tags": ["calendar", "holidays", "exams", "schedule", "ENSAH"],
            "months_covered": ["September", "October", "November","and all other months"],
            "description": "Detailed academic events for 2024-2025."
        }
    },
    {
        "content": "General information about ENSA Al Hoceima.",
        "metadata": {
            "tags": ["school info", "admissions", "programs", "contact" ,"professors", "all about ENSA Al Hoceima" ,"all local events "],
            "description": "General information about ENSA Al Hoceima." , 
        }
    },
]

documents = [Document(page_content=doc["content"], metadata=doc["metadata"]) for doc in documents]
print(documents)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
import os
url = os.getenv("QDRANT_URL")
api_key = os.getenv("QDRANT_API_KEY")
QdrantVectorStore.from_documents(
    documents,
    embeddings,
    url=url,
    prefer_grpc=True,
    api_key=api_key,
    collection_name="subjects",
)

print("Subjects data created successfully.")
