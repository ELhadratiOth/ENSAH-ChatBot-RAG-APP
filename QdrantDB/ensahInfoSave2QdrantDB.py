import os
from langchain_community.document_loaders import JSONLoader, CSVLoader
from langchain_community.document_loaders.merge import MergedDataLoader
from dotenv import load_dotenv
from langchain_core.documents import Document
import json
import pandas as pd

load_dotenv(override=True)
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

folder_path = "./DataENG"

# Initialize document lists
csv_documents = []
json_documents = []

# Process CSV files
for filename in os.listdir(folder_path):
    if filename.endswith(".csv"):
        file_path = os.path.join(folder_path, filename)
        loader = CSVLoader(file_path, encoding='utf-8')
        csv_documents.extend(loader.load())

# Process abbreviation data
with open(os.path.join(folder_path, "abrevFiliere.json")) as f:
    abrev_data = json.load(f)

abrev_documents = []
for filiere_type, abbreviations in abrev_data.items():
    # Create a single document for each filiere type with all its abbreviations
    abbrev_list = [f"{abbrev} means {full_name}" for abbrev, full_name in abbreviations.items()]
    
    page_content = (
        f"{filiere_type.replace('_', ' ').title()} Abbreviations:\n"
        f"{'; '.join(abbrev_list)}"
    )
    
    abrev_documents.append(
        Document(
            page_content=page_content,
            metadata={
                "source": "abrevFiliere.json",
                "filiere_type": filiere_type.replace('_', ' ').title()
            }
        )
    )

# Process module data
with open(os.path.join(folder_path, "modulesFiliere.json")) as f:
    module_data = json.load(f)

module_documents = []
for filiere_code, filiere_info in module_data.items():
    # Get the semester key (handle both "semesters" and "semesters ")
    semester_key = "semesters" if "semesters" in filiere_info else "semesters "
    
    if semester_key in filiere_info:
        semesters = filiere_info[semester_key]
        
        # Create a document for each semester
        for semester, modules in semesters.items():
            page_content = (
                f"{filiere_info['specialty']} ({filiere_code.upper()}) - {semester}:\n"
                f"Modules: {', '.join(modules)}"
            )
            
            # Extract semester number
            semester_num = "".join(filter(str.isdigit, semester))
            year = (int(semester_num) + 1) // 2 if semester_num else None
            
            module_documents.append(
                Document(
                    page_content=page_content,
                    metadata={
                        "source": "modulesFiliere.json",
                        "filiere": filiere_code.upper(),
                        "specialty": filiere_info['specialty'],
                        "semester": semester,
                        "year": year,
                        "module_count": len(modules)
                    }
                )
            )

# Combine all documents
all_documents = csv_documents + abrev_documents + module_documents

# Optional: Print document count by source
source_counts = {}
for doc in all_documents:
    source = doc.metadata.get("source", "unknown")
    source_counts[source] = source_counts.get(source, 0) + 1

print("\nDocument counts by source:")
for source, count in source_counts.items():
    print(f"{source}: {count} documents")

# Return documents for further processing

from langchain_google_genai import GoogleGenerativeAIEmbeddings
embeddings = GoogleGenerativeAIEmbeddings(   
    model="models/text-embedding-004",
    task_type="semantic_similarity"
 )



from langchain_qdrant import QdrantVectorStore

import os
url = os.getenv("QDRANT_URL")
api_key = os.getenv("QDRANT_API_KEY")

QdrantVectorStore.from_documents(
    all_documents,
    embeddings,
    url=url,
    prefer_grpc=True,
    api_key=api_key,
    collection_name="ensah_data",
)

print("Data saved successfully!")
