from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
import google.generativeai as genai
import pandas as pd
import os
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from typing import List

# Load environment variables
load_dotenv()

# Custom embedding class for Google GenAI, inheriting from langchain_core.embeddings.Embeddings
class GoogleGenAIEmbeddings(Embeddings):
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

class RecommendationEngine:
    def __init__(self, csv_path, index_dir):
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found at {csv_path}")
        self.data = pd.read_csv(csv_path)

        # Load FAISS index
        index_faiss_path = os.path.join(index_dir, "index.faiss")
        if not os.path.exists(index_faiss_path):
            raise FileNotFoundError(f"FAISS index file not found at {index_faiss_path}")
        
        # Initialize Google GenAI
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file.")
        try:
            genai.configure(api_key=google_api_key)
        except Exception as e:
            raise ValueError(f"Failed to configure Google GenAI: {str(e)}")
        
        self.embeddings = GoogleGenAIEmbeddings()
        self.faiss_index = FAISS.load_local(index_dir, self.embeddings, allow_dangerous_deserialization=True)

        # Initialize Gemini model
        self.model = genai.GenerativeModel("gemini-1.5-flash")

        # Define prompt template
        self.prompt_template = """
        Given the following query: "{query}"
        And the retrieved assessments: {retrieved_docs}

        Recommend up to 10 relevant SHL assessments in a properly formatted markdown table with the following columns:
        - Assessment Name
        - Remote Testing Support (Yes/No)
        - Adaptive/IRT Support (Yes/No)
        - Test Type (with meaning)
        - Test Duration (in minutes) 
        - URL (use actual URLs from the metadata)

        Use this exact table format:
        | Assessment Name | Remote Testing Support | Adaptive/IRT Support | Test Type (with meaning) | Test Duration | URL |
        |-----------------|-------------------------|----------------------|--------------------------|---------------|-----|
        | [Name 1]        | Yes                     | No                   | [Type 1]                 | 30            | [URL 1] |
        | [Name 2]        | No                      | Yes                  | [Type 2]                 | 45            | [URL 2] |

        Ensure all recommendations meet any duration or other requirements mentioned in the query.
        Return ONLY the markdown table (no additional text).
        """
        
        self.prompt = PromptTemplate.from_template(self.prompt_template)

    def get_recommendations(self, query):
        docs = self.faiss_index.similarity_search(query, k=10)
        retrieved_docs = "\n".join([
            f"{doc.metadata['name']} - Remote: {doc.metadata['remote']}, Adaptive: {doc.metadata['adaptive']}, "
            f"Type: {doc.metadata['test_type']}, Duration: {doc.metadata['duration'] if doc.metadata['duration'] is not None else 'Variable Time'}, "
            f"URL: https://www.shl.com{doc.metadata['url']}"
            for doc in docs
        ])

        formatted_prompt = self.prompt.format(query=query, retrieved_docs=retrieved_docs)
        
        # Use Gemini model for text generation
        try:
            response = self.model.generate_content(
                formatted_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1000
                )
            )
            return response.candidates[0].content.parts[0].text.strip()
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return "Error generating recommendations."

if __name__ == "__main__":
    try:
        engine = RecommendationEngine(
            csv_path="data/updated_assessments.csv",
            index_dir="data/faiss_index"
        )
        query = "I am hiring for JAVA Developers who can also collaborate effectively with my business teams. Looking for an assessment(s) that can be completed in 40 minutes."
        recommendations = engine.get_recommendations(query)
        print(recommendations)
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")