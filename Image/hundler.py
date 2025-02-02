from dotenv import load_dotenv
import os
from langchain_core import embeddings
from langchain_qdrant import QdrantVectorStore
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
import re
from fastapi import FastAPI, HTTPException
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langserve import add_routes
from fastapi.middleware.cors import CORSMiddleware
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from fastapi.responses import JSONResponse
from datetime import datetime
from messagehistory import LastNMessageHistory
from inputchat import InputChat

load_dotenv(override=True)

os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_LOG_SEVERITY_LEVEL"] = "ERROR"
os.environ['LANGSMITH_TRACING'] = 'true'
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"    
os.environ["LANGSMITH_API_KEY"] = os.getenv('LANGSMITH_API_KEY')
os.environ["LANGSMITH_PROJECT"] = "ensah-monitoring"
required_vars = ['QDRANT_URL', 'QDRANT_API_KEY', 'GOOGLE_API_KEY' ,'LANGSMITH_API_KEY', 'LANGSMITH_PROJECT', 'LANGSMITH_ENDPOINT', 'LANGSMITH_TRACING',"MONGODB_URI"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


def _is_valid_identifier(value: str) -> bool:
    if not value or len(value) > 100:  
        return False
    valid_characters = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
    return bool(valid_characters.match(value))


qdrant_client =  QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY'),
)


embeddings  = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    task_type="semantic_similarity",
    google_api_key=os.getenv("GOOGLE_API_KEY"),)


llm  =  GoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

vector_store =  QdrantVectorStore(
    client=qdrant_client,
    collection_name="ensah_data",
    embedding=embeddings,
)
retriever=vector_store.as_retriever(search_kwargs={"k": 8} )


# message_trimmer = trim_messages(
#     max_tokens=3,
#     strategy="last",
#     include_system=True,
#     start_on="human",
#     token_counter=len,
# )

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an AI Agent specialized in answering questions about ENSAH.
Your role is to provide accurate and helpful answers about the programs, professors, and training offered at this institution.

Guidelines:
- Use the provided context to create your response, also use the chat history.
- If the question is related to ENSAH, use only relevant context information.
- Explain using simple and clear words.
- Always respond in the same language as the user input.
- Respond with 'I don't have that information in my knowledge base' if unable to answer.
- Your name is: ENSA Al Hoceima Chatbot , u should intoduce yourself when some one greats you.
- Your response should not include something like this in the beginning: "AI :".
- Try to be gentle and friendly in your response.
- Think carefully before answering and use the context and chat history to generate your response.

Context: {context}
    """),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])


def log_prompt(messages):
    print("\n=== Complete Prompt Being Sent to LLM ===")
    for msg in messages:
        print(f"\nRole: {msg}")
        print(f"Content: {msg}")
    print("=====================================\n")
    return messages

from langchain_core.runnables import RunnablePassthrough
chain = (
    # {
    #     "context": lambda x: x["context"], 
    #     "chat_history": message_trimmer,  
    #     "input": lambda x: x["input"]
    # } 
    # RunnablePassthrough.assign(messages=itemgetter("chat_history") | message_trimmer)
    # |
    prompt 
    # | log_prompt  
    | llm
)
# print("this is prompt :")
# print(prompt)

from langchain.chains import create_retrieval_chain

retrieval_chain = create_retrieval_chain(
    retriever,
    chain,
)

app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="ENSAH RAG API",
)

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    session_id = session_id.strip()
    if not _is_valid_identifier(session_id):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid session ID: '{session_id}'. Session ID must start with a letter or number "
                "and contain only alphanumeric characters, hyphens, or underscores."
            ),
        )
    if not session_id or not session_id.startswith('streamlit_'):
        raise ValueError("Invalid session ID format")
    
    mongodb_url = os.getenv("MONGODB_URI")
    
    mongo_history = MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string=mongodb_url,
        database_name="ensah_chatbot",
        collection_name="chat_histories",
    )
    
    last_n = LastNMessageHistory(mongo_history=mongo_history, max_messages=8)
    
    # print("Here are the last two messages:", last_n.messages)
    return last_n

from langchain_core.runnables.history import RunnableWithMessageHistory

chain_with_history = RunnableWithMessageHistory(
    retrieval_chain,
    get_session_history=get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer"
).with_types(input_type=InputChat)

# print("this is chain_with_history:")
# print(chain_with_history)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

add_routes(
    app,
    chain_with_history,
    path="/chat",
)

@app.get("/health")
async def health_check():
    try:
        mongodb_uri = os.getenv("MONGODB_URI")
        mongo_client = MongoDBChatMessageHistory(
            session_id="health_check",
            connection_string=mongodb_uri,
            database_name="ensah_chatbot",
            collection_name="chat_histories",
        )
        _ = mongo_client.messages

        _ = qdrant_client.get_collections()

        return {
            "status": "healthy",
            "mongodb": "connected",
            "qdrant": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
