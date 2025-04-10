import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
import google.generativeai as genai
import os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

# Initialize Google GenAI embeddings
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file.")
genai.configure(api_key=google_api_key)

# Custom embedding class for Google GenAI
class GoogleGenAIEmbeddings:
    def __init__(self, model="models/embedding-001"):
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        embeddings = []
        for text in texts:
            result = genai.embed_content(model=self.model, content=text)
            embeddings.append(result["embedding"])
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        result = genai.embed_content(model=self.model, content=text)
        return result["embedding"]

def create_faiss_index(csv_path, index_save_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at {csv_path}")
    
    # Load the CSV file
    df = pd.read_csv(csv_path)
    df.fillna("", inplace=True)
    
    # Prepare documents with metadata
    documents = []
    for _, row in df.iterrows():
        metadata = {
            "name": row.get("name", ""),
            "url": row.get("url", ""),
            "remote": row.get("remote", "Yes"),
            "adaptive": row.get("adaptive", "No"),
            "test_type": row.get("test_type", ""),
            "duration": row.get("duration", "")  # Default duration
        }
        
        page_content = f"""
        Assessment: {row.get('name', '')}
        Description: {row.get('description', '')}
        Test Type: {row.get('test_type', '')}
        Remote Testing: {row.get('remote', 'Yes')}
        Adaptive Testing: {row.get('adaptive', 'No')}
        Duration: {row.get('duration', '')}
        """
        
        documents.append(Document(page_content=page_content, metadata=metadata))
    
    # Create FAISS index with Google embeddings
    embeddings = GoogleGenAIEmbeddings()
    vectorstore = FAISS.from_documents(documents, embedding=embeddings)
    
    # Save index locally
    vectorstore.save_local(index_save_path)
    print(f"FAISS index saved to: {index_save_path}")

if __name__ == "__main__":
    csv_path = r"data\updated_assessments.csv"
    index_save_path = "data/faiss_index"
    create_faiss_index(csv_path, index_save_path)