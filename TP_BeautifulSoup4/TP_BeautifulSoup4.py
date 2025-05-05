import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time # Import time for potential delays


def scrape_article_details(article_url, headers):
    """
    Fetches and scrapes details (summary, author, content images) from a single article page.
    Returns a dictionary with 'summary', 'author', and 'content_images'.
    """
    summary = None
    author = None
    content_images = [] # Initialize list for images
    try:
        # Optional: Add a small delay to be polite to the server
        # time.sleep(0.5)
        response = requests.get(article_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Extract Summary (Hat) ---
        summary_div = soup.find('div', class_='article-hat')
        summary_p = summary_div.find('p') if summary_div else None
        summary = summary_p.get_text(strip=True) if summary_p else None

        # --- Extract Author ---
        meta_info_div = soup.find('div', class_='meta-info')
        if meta_info_div:
            byline_span = meta_info_div.find('span', class_='byline')
            if byline_span:
                author_a = byline_span.find('a')
                if author_a:
                    author = author_a.get_text(strip=True)

        # --- Extract Content Images ---
        content_div = soup.find('div', class_='entry-content') # Find main content area
        if content_div:
            # Find all figures or images directly within the content
            figures = content_div.find_all('figure') # Prefer figures as they contain captions
            if figures:
                for figure in figures:
                    img_tag = figure.find('img')
                    if img_tag:
                        img_url = img_tag.get('data-lazy-src') or img_tag.get('src')
                        if not img_url or img_url.startswith('data:image'):
                            continue # Skip invalid URLs

                        # Find caption within the figure
                        figcaption = figure.find('figcaption')
                        caption = figcaption.get_text(strip=True) if figcaption else img_tag.get('alt', '') # Fallback to alt

                        content_images.append({
                            'url': img_url,
                            'caption_or_alt': caption
                        })
            else:
                # Fallback: Find images directly if no figures are used consistently
                images_in_content = content_div.find_all('img')
                for img_tag in images_in_content:
                    img_url = img_tag.get('data-lazy-src') or img_tag.get('src')
                    if not img_url or img_url.startswith('data:image'):
                        continue # Skip invalid URLs

                    # Use alt text as caption since there's no figure/figcaption
                    caption = img_tag.get('alt', '')

                    content_images.append({
                        'url': img_url,
                        'caption_or_alt': caption
                    })

        return {'summary': summary, 'author': author, 'content_images': content_images}

    except requests.exceptions.RequestException as e:
        print(f"  -> Request Error fetching details from {article_url}: {e}")
        # Return default dict with empty list for images
        return {'summary': None, 'author': None, 'content_images': []}
    except Exception as e:
        print(f"  -> Error parsing details from {article_url}: {e}")
        # Return potentially partial data, including any images found so far
        return {'summary': summary, 'author': author, 'content_images': content_images}

def scrape_article_previews(listing_url):
    """
    Scrapes article previews from a listing page on blogdumoderateur.com,
    then fetches the full summary, author, and content images from each article's page.

    Args:
        listing_url (str): The URL of the listing page.

    Returns:
        list: A list of dictionaries, each containing data for one article.
              Returns an empty list if scraping fails or no articles are found.
              Note: Fetching details requires an extra request per article.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    articles_data = []

    try:
        print(f"Fetching listing page: {listing_url}...")
        response = requests.get(listing_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        article_tags = soup.find_all('article', class_=re.compile(r'\bpost-\d+\b'))

        if not article_tags:
            print(f"No article previews found on {listing_url} with the selector.")
            return []

        print(f"Found {len(article_tags)} article previews. Now fetching details (summary, author, images)...")

        for idx, article in enumerate(article_tags):
            data = {}
            print(f"Processing preview {idx+1}/{len(article_tags)}...")

            # --- Extract data from the preview ".com/"---
            header = article.find('header', class_='entry-header')
            a_tag = header.find('a') if header else None
            data['url'] = a_tag['href'] if a_tag and a_tag.has_attr('href') else None
            title_tag = header.find('h3', class_='entry-title') if header else None
            data['title'] = title_tag.get_text(strip=True) if title_tag else None

            img_div = article.find('div', class_='post-thumbnail')
            img_tag = img_div.find('img') if img_div else None
            if img_tag:
                data['thumbnail'] = img_tag.get('data-lazy-src') or img_tag.get('src')
            else:
                data['thumbnail'] = None

            meta_div = article.find('div', class_='entry-meta') # Preview meta
            category_tag = meta_div.find('span', class_=re.compile(r'\bfavtag\b')) if meta_div else None
            data['subcategory'] = category_tag.get_text(strip=True) if category_tag else None

            date_tag = meta_div.find('time', class_='published') if meta_div else None # Preview date
            if date_tag:
                 data['date_display'] = date_tag.get_text(strip=True)
                 if date_tag.has_attr('datetime'):
                     try:
                         date_iso = date_tag['datetime']
                         data['date_iso'] = datetime.fromisoformat(date_iso.split('T')[0]).strftime('%Y-%m-%d')
                     except (ValueError, IndexError):
                         data['date_iso'] = None
                 else:
                     data['date_iso'] = None
            else:
                 data['date_display'] = None
                 data['date_iso'] = None

            # --- Fetch and scrape details (summary, author, images) from the article page ---
            data['summary'] = None
            data['author'] = None
            data['content_images'] = [] # Initialize as empty list
            if data['url']:
                print(f"  Fetching details for: {data['title'] or data['url']}")
                # time.sleep(0.2) # Optional small delay between detail requests
                details = scrape_article_details(data['url'], headers)
                data['summary'] = details.get('summary')
                data['author'] = details.get('author')
                data['content_images'] = details.get('content_images', []) # Get images, default to empty list
            else:
                print("  Skipping details fetch (no URL found in preview).")


            # Only add if we found essential data like a URL or title
            if data.get('url') or data.get('title'):
                articles_data.append(data)

        return articles_data

    except requests.exceptions.RequestException as e:
        print(f"Request Error fetching listing page {listing_url}: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while scraping {listing_url}: {e}")
        return []


def scrape_article_full_details(article_url, headers):

    data = {
        'url': article_url,
        'title': None,
        'summary': None,
        'author': None,
        'date_display': None,
        'date_iso': None,
        'thumbnail': None, # This will be the main article image (header image)
        'subcategory': None, # Typically not found on the article page itself
        'content_images': []
    }

    try:
        # Optional: Add a small delay
        # time.sleep(0.5)
        response = requests.get(article_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Find Main Header ---
        main_header = soup.find('header', class_='article-header')
        if not main_header:
            print(f"  -> Warning: Main article header not found on {article_url}")
            # Still try to find content images below, but header info will be missing
        else:
            # --- Extract Title ---
            title_tag = main_header.find('h1', class_='entry-title')
            data['title'] = title_tag.get_text(strip=True) if title_tag else None

            # --- Extract Summary (Hat) ---
            summary_div = main_header.find('div', class_='article-hat')
            summary_p = summary_div.find('p') if summary_div else None
            data['summary'] = summary_p.get_text(strip=True) if summary_p else None

            # --- Extract Author & Date (from meta section within header) ---
            meta_section = main_header.find('div', class_='entry-meta', recursive=False) # Look directly within header
            if meta_section:
                meta_info_div = meta_section.find('div', class_='meta-info')
                if meta_info_div:
                    # Author
                    byline_span = meta_info_div.find('span', class_='byline')
                    if byline_span:
                        author_a = byline_span.find('a')
                        data['author'] = author_a.get_text(strip=True) if author_a else None
                    # Date
                    posted_on_span = meta_info_div.find('span', class_='posted-on')
                    if posted_on_span:
                        time_tag = posted_on_span.find('time', class_='published')
                        if time_tag:
                            data['date_display'] = time_tag.get_text(strip=True)
                            if time_tag.has_attr('datetime'):
                                try:
                                    date_iso_str = time_tag['datetime']
                                    # Extract only the date part YYYY-MM-DD
                                    data['date_iso'] = datetime.fromisoformat(date_iso_str).strftime('%Y-%m-%d')
                                except ValueError:
                                    pass # Keep date_iso as None if parsing fails

            # --- Extract Thumbnail/Header Image ---
            figure_hat_img = main_header.find('figure', class_='article-hat-img')
            if figure_hat_img:
                img_tag = figure_hat_img.find('img')
                if img_tag:
                    data['thumbnail'] = img_tag.get('data-lazy-src') or img_tag.get('src')

        # --- Extract Content Images (using the existing logic, applied to the whole soup) ---
        content_div = soup.find('div', class_='entry-content') # Find main content area
        if content_div:
            figures = content_div.find_all('figure')
            if figures:
                for figure in figures:
                    img_tag = figure.find('img')
                    if img_tag:
                        img_url = img_tag.get('data-lazy-src') or img_tag.get('src')
                        if not img_url or img_url.startswith('data:image'): continue
                        figcaption = figure.find('figcaption')
                        caption = figcaption.get_text(strip=True) if figcaption else img_tag.get('alt', '')
                        data['content_images'].append({'url': img_url, 'caption_or_alt': caption})
            else: # Fallback
                images_in_content = content_div.find_all('img')
                for img_tag in images_in_content:
                    img_url = img_tag.get('data-lazy-src') or img_tag.get('src')
                    if not img_url or img_url.startswith('data:image'): continue
                    caption = img_tag.get('alt', '')
                    data['content_images'].append({'url': img_url, 'caption_or_alt': caption})

        return data # Return the dictionary with all found data

    except requests.exceptions.RequestException as e:
        print(f"  -> Request Error fetching full details from {article_url}: {e}")
        return None # Indicate failure
    except Exception as e:
        print(f"  -> Error parsing full details from {article_url}: {e}")
        # Return potentially partial data found so far in case of parsing error
        return data