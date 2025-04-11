![image](https://github.com/user-attachments/assets/2e3c176e-23a7-43ec-b601-d4532eafd39c)
![image](https://github.com/user-attachments/assets/823d6163-7020-402a-b5cf-4a92e7abb17e)
SHL Assessment Recommendation Engine: Solution Approach
Data Collection:
Scraped SHL's product catalog using BeautifulSoup and requests
Extracted details: 
Name, URL, Test type, Duration, Remote Support and Adaptive Support.
Overcame pagination challenges by:
Incrementing URL by 12
Adding ?page={page_num}&type=1&type=1 to URL
Introducing time.sleep(1) for polite scraping
Result: 300+ unique assessments collected
Vector Database Creation:
Technology Stack: Employed FAISS for vector storage, integrated with a custom GoogleGenAIEmbeddings class using Google’s models/embedding-001 to generate dense vectors from assessment descriptions.
Document Preparation: Created Document objects with metadata (name, url, remote, adaptive, test_type, duration) and content for semantic search, ensuring rich contextual representation.
Vector Generation: Generated embeddings using the Google GenAI embedding model, enabling efficient similarity searches.
Index Storage: Saved the FAISS index locally in data/faiss_index after pre-building it with the embedding class, optimizing retrieval performance.

Recommendation Engine:
Utilized Retrieval-Augmented Generation (RAG) with LangChain andGoogle Generative AI (Gemini generative-1.5-flash model)
Prompt Engineering: Designed a structured Prompt Template to generate recommendations in a Markdown table format, including columns for Assessment Name, Remote Testing Support, Adaptive/IRT Support, Test Type, Test Duration (with "Variable Time" for zero or undetected durations), and URL.
FAISS retrieved top 10 assessments based on query similarity

Deployment:
Streamlit App: Deployed on Streamlit Community Cloud, leveraging its flexibility with no strict size limits to provide an interactive interface for users to input queries and view recommendations.
API: Deployed on Render.com, a platform supporting Git-based deployments, using a Flask wrapper to expose a /recommend endpoint. The API converts Markdown output to JSON, ensuring interoperability.
Tools and Libraries:
Scraping: requests, BeautifulSoup, pandas
Vector DB: FAISS, langchain_community, custom GoogleGenAIEmbeddings
RAG: LangChain, google-generativeai, python-dotenv
UI/API: Streamlit, Flask, Render.com
Utilities: os, logging
This approach resulted in a robust, user-friendly system with a working demo and API endpoint, effectively solving the assessment selection problem through integrated scraping, semantic search, and RAG-based recommendations.
