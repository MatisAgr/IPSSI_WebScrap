import TP_BeautifulSoup4 as scraper
import mongo_connect as db_connector


from pymongo.errors import PyMongoError

def main():
    base_url = "https://www.blogdumoderateur.com/"
    all_scraped_articles = []
    total_inserted_count = 0
    total_skipped_count = 0

    # Define headers once
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print("--- Starting Category URL Scraping ---")
    category_urls = scraper.scrape_category_urls(base_url, headers)

    if not category_urls:
        print("No category URLs found or error fetching them. Scraping only the homepage.")
        # Optionally, add the base_url itself to scrape the homepage if categories fail
        category_urls = [base_url] # Or decide to exit if categories are mandatory
    else:
        print(f"Found {len(category_urls)} categories to scrape.")
        # Optional: Add homepage scraping as well if desired
        # if base_url not in category_urls:
        #     category_urls.insert(0, base_url) # Add homepage at the beginning

    print("--- Connecting to MongoDB ---")
    articles_collection = db_connector.connect_to_mongo()

    if articles_collection is None:
        print("Failed to connect to MongoDB. Cannot save data. Exiting.")
        return # Exit if DB connection failed

    print("--- Starting Article Scraping for Each Category ---")

    # Iterate through each category URL found
    for category_url in category_urls:
        print(f"--- Scraping Category: {category_url} ---")

        # Scrape articles from the current category listing page
        scraped_articles = scraper.scrape_article_previews(category_url) # Pass headers if needed by scrape_article_previews

        if not scraped_articles:
            print(f"No articles were scraped from {category_url}. Moving to next category.")
            continue # Skip to the next category

        print(f"--- Scraping finished for {category_url}. Found {len(scraped_articles)} articles. ---")
        print("--- Inserting scraped articles into MongoDB ---")

        # Insert articles from this category into the collection
        inserted_count = 0
        skipped_count = 0
        for article_data in scraped_articles:
            try:
                # Check if an article with the same URL already exists
                if article_data.get('url'):
                    existing_article = articles_collection.find_one({'url': article_data['url']})
                    if existing_article:
                        # print(f"  Skipped (already exists): {article_data.get('title', 'N/A')} (URL: {article_data['url']})")
                        skipped_count += 1
                        continue # Skip to the next article

                # If no URL or not found, proceed with insertion
                insert_result = articles_collection.insert_one(article_data)
                # print(f"  Inserted article: {article_data.get('title', 'N/A')} (ID: {insert_result.inserted_id})")
                inserted_count += 1
                all_scraped_articles.append(article_data) # Keep track if needed

            except PyMongoError as e:
                print(f"  Error inserting article '{article_data.get('title', 'N/A')}': {e}")
                skipped_count += 1
            except Exception as e:
                print(f"  Unexpected error inserting article '{article_data.get('title', 'N/A')}': {e}")
                skipped_count += 1

        print(f"--- MongoDB Insertion Summary for {category_url} ---")
        print(f"Successfully inserted: {inserted_count} articles.")
        print(f"Skipped or failed: {skipped_count} articles.")
        total_inserted_count += inserted_count
        total_skipped_count += skipped_count
        print("----------------------------------------------------")


    print("--- Overall MongoDB Insertion Summary ---")
    print(f"Total successfully inserted across all categories: {total_inserted_count} articles.")
    print(f"Total skipped or failed across all categories: {total_skipped_count} articles.")
    print("---------------------------------------")

# --- Run the main function ---
if __name__ == "__main__":
    main()