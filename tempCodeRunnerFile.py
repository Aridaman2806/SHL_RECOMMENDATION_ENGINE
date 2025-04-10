import pandas as pd
import os
import logging
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables (optional, for future API use if needed)
load_dotenv()

class NameScraper:
    def __init__(self, csv_path, output_csv_path="data/updated_assessments.csv"):
        self.csv_path = csv_path
        self.output_csv_path = output_csv_path
        self.data = self._load_data()

    def _load_data(self):
        try:
            if not os.path.exists(self.csv_path):
                raise FileNotFoundError(f"CSV file not found at {self.csv_path}")
            df = pd.read_csv(self.csv_path)
            # Ensure name and url columns exist
            if "name" not in df.columns or "url" not in df.columns:
                raise ValueError("CSV must contain 'name' and 'url' columns")
            logger.info(f"Loaded {len(df)} records from CSV")
            return df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise

    def _scrape_assessment_name(self, url):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            # Prepend SHL base URL to relative paths
            full_url = f"https://www.shl.com{url}" if not url.startswith("http") else url
            response = requests.get(full_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            time.sleep(2)  # Add delay to avoid rate limiting

            # Attempt to extract name from <h1> tag (common for page titles)
            name_tag = soup.find("h1")
            if name_tag:
                extracted_name = name_tag.text.strip()
            else:
                # Fallback to <title> tag if <h1> is not found
                extracted_name = soup.title.text.strip() if soup.title else "Unknown"

            return extracted_name
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return "Error"

    def update_names(self):
        updated_data = []
        for item in self.data:
            original_name = item["name"]
            url = item["url"]
            logger.info(f"Scraping {url} for name (original: {original_name})")
            extracted_name = self._scrape_assessment_name(url)

            # Use extracted name if valid, otherwise keep original
            final_name = extracted_name if extracted_name != "Error" and extracted_name != "Unknown" else original_name
            if final_name != original_name:
                logger.info(f"Updated name for {url}: {original_name} -> {final_name}")

            updated_item = item.copy()
            updated_item["name"] = final_name
            updated_data.append(updated_item)

        # Save to new CSV
        updated_df = pd.DataFrame(updated_data)
        updated_df.to_csv(self.output_csv_path, index=False)
        logger.info(f"Updated data saved to {self.output_csv_path}")

if __name__ == "__main__":
    scraper = NameScraper("data/shl_individual_assessments.csv")
    scraper.update_names()