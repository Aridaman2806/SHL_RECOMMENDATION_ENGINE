import pandas as pd
import os
import logging
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables (optional, for future use)
load_dotenv()

class NameScraper:
    def __init__(self, csv_path, output_csv_path="data/updated_assessments_test.csv"):
        self.csv_path = csv_path
        self.output_csv_path = output_csv_path
        self.data = self._load_data()

    def _load_data(self):
        try:
            if not os.path.exists(self.csv_path):
                raise FileNotFoundError(f"CSV file not found at {self.csv_path}")
            df = pd.read_csv(self.csv_path)
            if "name" not in df.columns or "url" not in df.columns:
                raise ValueError("CSV must contain 'name' and 'url' columns")
            logger.info(f"Loaded {len(df)} records from CSV")
            return df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise

    def _setup_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _scrape_assessment_details(self, url):
        try:
            session = self._setup_session()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            full_url = f"https://www.shl.com{url}" if not url.startswith("http") and pd.notna(url) else url
            if pd.isna(url) or not full_url:
                logger.warning(f"Skipping invalid URL: {url}")
                return {"name": "Unknown", "duration": 0}

            response = session.get(full_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            time.sleep(2)

            # Extract name from <h1> or fallback to <title> or content
            name_tag = soup.find("h1")
            if name_tag:
                extracted_name = name_tag.text.strip()
            else:
                title_tag = soup.find("title")
                extracted_name = title_tag.text.strip() if title_tag else "Unknown"
                download_heading = soup.find("h4", text=lambda t: "Downloads" in t)
                if download_heading:
                    next_tag = download_heading.find_next("a")
                    extracted_name = next_tag.text.strip() if next_tag else extracted_name

            # Extract duration
            duration_tag = soup.find("p", text=lambda t: "Approximate Completion Time in minutes" in t)
            duration = int(duration_tag.text.split("=")[1].strip()) if duration_tag else 0

            return {
                "name": extracted_name,
                "duration": duration
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {"name": "Error", "duration": 0}

    def update_assessment_details(self):
        updated_data = []
        # Process all entries (removed [:10] limit)
        for item in self.data:
            original_name = item["name"]
            url = item["url"]
            logger.info(f"Scraping {url} for details (original name: {original_name})")
            scraped_details = self._scrape_assessment_details(url)

            # Use scraped name if valid, otherwise keep original
            final_name = scraped_details["name"] if scraped_details["name"] not in ["Error", "Unknown"] else original_name
            if final_name != original_name and scraped_details["name"] not in ["Error", "Unknown"]:
                logger.info(f"Updated name for {url}: {original_name} -> {final_name}")

            updated_item = item.copy()
            updated_item["name"] = final_name
            updated_item["duration"] = scraped_details["duration"]
            updated_data.append(updated_item)

        # Save to new CSV with permission error handling
        try:
            updated_df = pd.DataFrame(updated_data)
            updated_df.to_csv(self.output_csv_path, index=False)
            logger.info(f"Updated data saved to {self.output_csv_path}")
        except PermissionError as e:
            logger.error(f"Permission denied writing to {self.output_csv_path}: {str(e)}. Trying alternate path...")
            alternate_path = "updated_assessments_test.csv"  # Save in current directory
            try:
                updated_df.to_csv(alternate_path, index=False)
                logger.info(f"Updated data saved to alternate path: {alternate_path}")
            except Exception as e:
                logger.error(f"Failed to save to alternate path: {str(e)}")
        except Exception as e:
            logger.error(f"Error saving CSV: {str(e)}")

if __name__ == "__main__":
    scraper = NameScraper("data/shl_individual_assessments.csv")
    scraper.update_assessment_details()