import streamlit as st
from recommendation_engine import RecommendationEngine
import os
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Streamlit app configuration
st.set_page_config(page_title="SHL Assessment Recommendation Engine", layout="wide")

# Direct relative paths
CSV_PATH = "data/shl_individual_assessments.csv"
INDEX_DIR = "data/faiss_index"

# Initialize the Recommendation Engine
@st.cache_resource
def load_recommendation_engine():
    try:
        if not os.path.exists(CSV_PATH):
            raise FileNotFoundError(f"CSV file not found at {CSV_PATH}")
        if not os.path.exists(os.path.join(INDEX_DIR, "index.faiss")):
            raise FileNotFoundError(f"FAISS index not found at {INDEX_DIR}")
        engine = RecommendationEngine(CSV_PATH, INDEX_DIR)
        logger.info("Recommendation engine loaded successfully")
        return engine
    except Exception as e:
        logger.error(f"Error loading recommendation engine: {str(e)}")
        raise

# Load engine 
try:
    engine = load_recommendation_engine()
    st.success("Recommendation engine loaded successfully!")
except Exception as e:
    st.error(f"Failed to initialize the recommendation engine: {str(e)}")
    st.stop()

# UI 
st.title("SHL Assessment Recommendation System")
st.markdown("Enter a query to get tailored SHL assessment recommendations for your hiring needs.")

# Input query
query = st.text_area(
    "Enter your hiring query (e.g., 'I am hiring for Java developers who can collaborate effectively with my teams. Looking for assessments under 40 minutes.')",
    height=100,
)

# Generate recommendations
if st.button("Get Recommendations"):
    if query.strip():
        with st.spinner("Generating recommendations..."):
            try:
                raw_recommendations = engine.get_recommendations(query)
                # Debug: Display raw response
               # st.write("Raw Response from Gemini:", raw_recommendations)
                
                # Parse the markdown table into a DataFrame
                lines = raw_recommendations.split("\n")
                if len(lines) < 4 or not any("|" in line for line in lines):  # Check for table structure
                    st.error("No valid table found in the response.")
                    st.stop()

                headers = [h.strip() for h in lines[1].split("|")[1:-1] if h.strip()]
                if len(headers) < 6:  # Ensure minimum expected columns
                    st.error("Invalid table header format.")
                    st.stop()

                data = []
                for line in lines[3:-1]:  # Skip header and separator lines
                    if line.strip() and "|" in line:
                        row = [cell.strip() for cell in line.split("|")[1:-1] if cell.strip()]
                        if len(row) >= 6:  # Ensure minimum row length
                            # Convert duration to integer (e.g., "30-45 minutes" -> 45)
                            duration_str = row[4]
                            duration = int(duration_str.split("-")[-1].split()[0]) if "-" in duration_str else int(duration_str.split()[0])
                            data.append({
                                "Assessment Name": row[0],
                                "Remote Testing Support": row[1],
                                "Adaptive/IRT Support": row[2],
                                "Test Type": [t.strip() for t in row[3].split(",")],
                                "Duration": duration,
                                "URL": f"https://www.shl.com{row[5]}"
                            })
                        else:
                            logger.warning(f"Skipping malformed row: {row}")

                if not data:
                    st.error("No valid recommendations found.")
                else:
                    df = pd.DataFrame(data)
                    st.markdown("### Recommended SHL Assessments")
                    st.table(df)
                    with st.expander("View Raw Response"):
                        st.text(raw_recommendations)
            except Exception as e:
                st.error(f"Error generating recommendations: {str(e)}")
                logger.error(f"Exception in recommendations: {str(e)}")
    else:
        st.warning("Please enter a query to get recommendations.")
else:
    st.info("Enter a query and click 'Get Recommendations' to see results.")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit and powered by Google Gemini. Data sourced from SHL's product catalog.")