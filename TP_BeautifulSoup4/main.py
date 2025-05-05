import TP_BeautifulSoup4 as scraper 
import mongo_connect as db_connector 


from pymongo.errors import PyMongoError

def main():

    # 1. Define the URL to scrape (homepage or a specific category)
    listing_page_url = "https://www.blogdumoderateur.com/" # Example: Homepage

    print(f"--- Starting Scraping Process for {listing_page_url} ---")

    # 2. Scrape the articles
    scraped_articles = scraper.scrape_article_previews(listing_page_url)

    if not scraped_articles:
        print("No articles were scraped. Exiting.")
        return # Exit if scraping failed or returned no data

    print(f"\n--- Scraping finished. Found {len(scraped_articles)} articles. ---")
    print("--- Connecting to MongoDB ---")

    articles_collection = db_connector.connect_to_mongo()

    if articles_collection is None:
        print("Failed to connect to MongoDB. Cannot save data. Exiting.")
        return # Exit if DB connection failed

    print("\n--- Inserting scraped articles into MongoDB ---")

    # 4. Insert each scraped article into the collection
    inserted_count = 0
    skipped_count = 0
    for article_data in scraped_articles:
        try:

            # Simple insertion without duplicate check:
            insert_result = articles_collection.insert_one(article_data)
            print(f"  Inserted article: {article_data.get('title', 'N/A')} (ID: {insert_result.inserted_id})")
            inserted_count += 1

        except PyMongoError as e:
            print(f"  Error inserting article '{article_data.get('title', 'N/A')}': {e}")
            skipped_count += 1
        except Exception as e:
            print(f"  Unexpected error inserting article '{article_data.get('title', 'N/A')}': {e}")
            skipped_count += 1


    print("\n--- MongoDB Insertion Summary ---")
    print(f"Successfully inserted: {inserted_count} articles.")
    print(f"Skipped or failed: {skipped_count} articles.")
    print("---------------------------------")

# --- Run the main function ---
if __name__ == "__main__":
    main()