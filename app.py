from flask import Flask, request, jsonify
from recommendation_engine import RecommendationEngine
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Direct relative paths
CSV_PATH = "data/shl_individual_assessments.csv"
INDEX_DIR = "data/faiss_index"

# Initialize Recommendation Engine
def init_recommendation_engine():
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

# Load engine globally
try:
    recommendation_engine = init_recommendation_engine()
except Exception as e:
    logger.error(f"Failed to initialize recommendation engine: {str(e)}")
    raise

# Health Check Endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Assessment Recommendation Endpoint (POST as specified)
@app.route('/recommend', methods=['POST'])
def get_recommendations():
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data or 'query' not in data or not data['query'].strip():
            return jsonify({"error": "Query field is required"}), 400

        query = data['query']

        # Generate recommendations
        raw_recommendations = recommendation_engine.get_recommendations(query)
        
        # Parse markdown table into the required JSON format
        lines = [line.strip() for line in raw_recommendations.split("\n") if line.strip()]
        if len(lines) < 3 or not any("|" in line for line in lines):  # Check for table structure
            return jsonify({"error": "No valid table found in the response"}), 500

        # Extract headers
        headers_line = lines[0]
        headers = [h.strip() for h in headers_line.split("|")[1:-1] if h.strip()]
        if len(headers) != 6:  # Expect 6 columns: Name, Remote, Adaptive, Type, Duration, URL
            return jsonify({"error": f"Invalid table header format. Expected 6 columns, got {len(headers)}"}), 500

        # Extract data rows (skip header and separator)
        recommended_assessments = []
        for line in lines[2:]:  # Start from the first data row
            if line and "|" in line:
                row = [cell.strip() for cell in line.split("|")[1:-1] if cell.strip()]
                if len(row) == 6:  # Ensure exactly 6 columns
                    # Convert duration to integer, handling range (e.g., "30-45 minutes" -> 30)
                    duration_str = row[4].replace("minutes", "").strip()
                    if "-" in duration_str:
                        duration = int(duration_str.split("-")[0])  # Take the minimum value
                    else:
                        duration = int(duration_str)
                    # Extract short test type code (e.g., "K" from "K (Knowledge-based)")
                    test_type_str = row[3].split()[0] if row[3] else "Unknown"
                    recommended_assessments.append({
                        "url": f"https://www.shl.com{row[5]}",  # Prepend https://www.shl.com/ to URL
                        "adaptive_support": row[2],
                        "description": row[0],  # Use Assessment Name as description
                        "duration": duration,
                        "remote_support": row[1],
                        "test_type": [test_type_str]  # Use short code as list
                    })
                else:
                    logger.warning(f"Skipping malformed row: {row}")

        if not recommended_assessments:
            return jsonify({"error": "No valid recommendations found"}), 404

        return jsonify({"recommended_assessments": recommended_assessments}, ensure_ascii=False, indent=2), 200
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": f"Error generating recommendations: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=False)