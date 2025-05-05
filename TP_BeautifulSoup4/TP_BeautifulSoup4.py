import requests # requêtes HTTP
from bs4 import BeautifulSoup # scraper
from datetime import datetime
import re # regex

# custom
from utils.debug_color import debug_print

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# scrap les articles d'une catégorie
def scrape_category_urls(base_url):

    global headers

    category_urls = []
    try:
        debug_print(f"Fetching base page to find category URLs: {base_url}...", level="fetch")
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        primary_menu = soup.find('ul', id='primary-menu')
        if not primary_menu:
            debug_print("Primary menu ('ul#primary-menu') not found.", level="warning")
            return []

        menu_items = primary_menu.find_all('li', class_='menu-item-object-category', recursive=False) # Look for direct li children with the specific class

        if not menu_items:
             # si pas de 'li' trouvé, on cherche tous les 'a'
             menu_links = primary_menu.find_all('a', href=True)
             if not menu_links:
                 debug_print("No category links found within the primary menu.", level="warning")
                 return []
             menu_items = menu_links # mettre les liens comme items de menu

        # debug_print(f"Found {len(menu_items)} potential category items in the menu.", level="debug") # Optionnel, peut être bruyant

        for item in menu_items:
             if item.name == 'a':
                 link = item
             else:
                 link = item.find('a', href=True)

             if link:
                 href = link['href']
                 if href.startswith(base_url) and href != base_url:
                     category_urls.append(href)
                 elif href.startswith('/') and href != '/tools/': # exclure les liens /tools/ (pas d'articles)
                     pass

        debug_print(f"Extracted {len(category_urls)} category URLs.", level="success")
        return category_urls

    except requests.exceptions.RequestException as e:
        debug_print(f"Request Error fetching base page {base_url}: {e}", level="error")
        return []
    except Exception as e:
        debug_print(f"An unexpected error occurred while scraping category URLs from {base_url}: {e}", level="error")
        return []

# scrap les détails d'un article (en complément des aperçus)
def scrape_article_details(article_url, headers):

    summary = None
    author = None
    content_images = []
    tags = []
    try:
        # time.sleep(0.5) # Délai optionnel
        response = requests.get(article_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # extract résumé
        summary_div = soup.find('div', class_='article-hat')
        summary_p = summary_div.find('p') if summary_div else None
        summary = summary_p.get_text(strip=True) if summary_p else None

        # extract auteur
        main_header = soup.find('header', class_='article-header') # zone d'en-tête de l'article
        if main_header:
            meta_section = main_header.find('div', class_='entry-meta', recursive=False)
            if meta_section:
                meta_info_div = meta_section.find('div', class_='meta-info')
                if meta_info_div:
                    byline_span = meta_info_div.find('span', class_='byline')
                    if byline_span:
                        author_a = byline_span.find('a')
                        author = author_a.get_text(strip=True) if author_a else None

        # extract image de l'article
        content_div = soup.find('div', class_='entry-content') # zone de contenu principal
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
                        content_images.append({'url': img_url, 'caption_or_alt': caption})

            else: # fallback
                images_in_content = content_div.find_all('img')
                for img_tag in images_in_content:
                    img_url = img_tag.get('data-lazy-src') or img_tag.get('src')
                    if not img_url or img_url.startswith('data:image'): continue
                    caption = img_tag.get('alt', '')
                    content_images.append({'url': img_url, 'caption_or_alt': caption})

        # extract Tags/Catégories
        terms_div = soup.find('div', class_='article-terms')
        if terms_div:
            tags_list_ul = terms_div.find('ul', class_='tags-list')
            if tags_list_ul:
                tag_links = tags_list_ul.find_all('a', class_='post-tags')
                if tag_links:
                    tags = [link.get_text(strip=True) for link in tag_links]

        return {'summary': summary, 'author': author, 'content_images': content_images, 'tags': tags}

    # gestion des exceptions
    except requests.exceptions.RequestException as e:
        debug_print(f"Request Error fetching details from {article_url}: {e}", level="error")
        return {'summary': None, 'author': None, 'content_images': [], 'tags': []}
    except Exception as e:
        debug_print(f"Parsing Error fetching details from {article_url}: {e}", level="error")
        # Retourner ce qui a pu être extrait avant l'erreur de parsing
        return {'summary': summary, 'author': author, 'content_images': content_images, 'tags': tags}


# scrap les aperçus d'articles d'une page de liste
def scrape_article_previews(listing_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    articles_data = []

    try:
        debug_print(f"Fetching listing page: {listing_url}...", level="fetch")
        response = requests.get(listing_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        article_tags_html = soup.find_all('article', class_=re.compile(r'\bpost-\d+\b'))

        if not article_tags_html:
            debug_print(f"No article previews found on {listing_url}.", level="warning")
            return []

        debug_print(f"Found {len(article_tags_html)} article previews. Fetching details...", level="info")

        for idx, article_html in enumerate(article_tags_html):
            data = {}
            # debug_print(f"Processing preview {idx+1}/{len(article_tags_html)}...", level="debug") # Optionnel

            # extract data de la preview
            header = article_html.find('header', class_='entry-header')
            a_tag = header.find('a') if header else None
            data['url'] = a_tag['href'] if a_tag and a_tag.has_attr('href') else None
            title_tag = header.find('h3', class_='entry-title') if header else None
            data['title'] = title_tag.get_text(strip=True) if title_tag else "No Title Found" # Default title

            img_div = article_html.find('div', class_='post-thumbnail')
            img_tag = img_div.find('img') if img_div else None
            data['thumbnail'] = img_tag.get('data-lazy-src') or img_tag.get('src') if img_tag else None

            meta_div = article_html.find('div', class_='entry-meta')
            category_tag = meta_div.find('span', class_=re.compile(r'\bfavtag\b')) if meta_div else None
            data['category'] = category_tag.get_text(strip=True) if category_tag else None

            date_tag = meta_div.find('time', class_='published') if meta_div else None
            if date_tag:
                 data['date_display'] = date_tag.get_text(strip=True)
                 if date_tag.has_attr('datetime'):
                     try:
                         date_iso_str = date_tag['datetime']
                         # Gérer le format ISO 8601 avec ou sans 'T'
                         date_iso_str = date_iso_str.replace(' ', 'T')
                         # Prendre seulement la partie date
                         data['date_iso'] = datetime.fromisoformat(date_iso_str.split('T')[0]).strftime('%Y-%m-%d')
                     except (ValueError, IndexError): data['date_iso'] = None
                 else: data['date_iso'] = None
            else:
                 data['date_display'] = None
                 data['date_iso'] = None

            #appel le scrape_article_details pour récupérer les détails supplémentaires
            data['summary'] = None
            data['author'] = None
            data['content_images'] = []
            data['tags'] = []
            if data['url']:
                # Message concis pour indiquer quelle URL est traitée
                debug_print(f"  Fetching details for article {idx+1}...", level="fetch", end='\r') # Utilise end='\r' pour écraser la ligne
                details = scrape_article_details(data['url'], headers)
                # Effacer la ligne précédente après la récupération
                print(' ' * 80, end='\r') # Efface la ligne avec des espaces
                data['summary'] = details.get('summary')
                data['author'] = details.get('author')
                data['content_images'] = details.get('content_images', [])
                data['tags'] = details.get('tags', []) # Récupère les tags
            else:
                debug_print(f"  Skipping details fetch for article {idx+1} (no URL found).", level="warning")

            if data.get('url') or data.get('title') != "No Title Found":
                articles_data.append(data)

        debug_print(f"Successfully scraped {len(articles_data)} articles from {listing_url}.", level="success")
        return articles_data

    # gestion des exceptions
    except requests.exceptions.RequestException as e:
        debug_print(f"Request Error fetching listing page {listing_url}: {e}", level="error")
        return []
    except Exception as e:
        debug_print(f"An unexpected error occurred while scraping {listing_url}: {e}", level="error")
        return []

# scrap les détails complets d'un article (sans complément et sans passer par l'aperçu)
# utilisé dans ./pages/Scrap_article.py
def scrape_article_full_details(article_url, headers):

    data = {
        'url': article_url,
        'title': None,
        'summary': None,
        'author': None,
        'date_display': None,
        'date_iso': None,
        'thumbnail': None,
        'category': None, # sera défini comme le premier tag trouvé
        'tags': [],
        'content_images': []
    }

    try:
        debug_print(f"Fetching full details for: {article_url}", level="fetch")
        # time.sleep(0.5) # Délai optionnel
        response = requests.get(article_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # recup le header de l'article
        main_header = soup.find('header', class_='article-header')
        if not main_header:
            debug_print(f"Main header ('header.article-header') not found on {article_url}", level="warning")
        else:
            # extract titre
            title_tag = main_header.find('h1', class_='entry-title')
            data['title'] = title_tag.get_text(strip=True) if title_tag else None

            # extract résumé
            summary_div = main_header.find('div', class_='article-hat')
            summary_p = summary_div.find('p') if summary_div else None
            data['summary'] = summary_p.get_text(strip=True) if summary_p else None

            # extract auteur & date
            meta_section_header = main_header.find('div', class_='entry-meta', recursive=False)
            if meta_section_header:
                meta_info_div_header = meta_section_header.find('div', class_='meta-info')
                if meta_info_div_header:
                    # extract auteur
                    byline_span = meta_info_div_header.find('span', class_='byline')
                    # debug_print(f"  -> byline_span: {byline_span}", level="debug") # Optionnel
                    if byline_span:
                        author_a = byline_span.find('a')
                        data['author'] = author_a.get_text(strip=True) if author_a else None
                    # extract date
                    posted_on_span = meta_info_div_header.find('span', class_='posted-on')
                    if posted_on_span:
                        time_tag = posted_on_span.find('time', class_='published')
                        if time_tag:
                            data['date_display'] = time_tag.get_text(strip=True)
                            if time_tag.has_attr('datetime'):
                                try:
                                    date_iso_str = time_tag['datetime']
                                    # Gérer le format ISO 8601 avec ou sans 'T'
                                    date_iso_str = date_iso_str.replace(' ', 'T')
                                    # Prendre seulement la partie date
                                    data['date_iso'] = datetime.fromisoformat(date_iso_str.split('T')[0]).strftime('%Y-%m-%d')
                                except ValueError:
                                    debug_print(f"Could not parse date: {time_tag.get('datetime')}", level="warning")
                                    pass # Laisser date_iso à None

            # extract miniature / (normalment image de preview)
            figure_hat_img = main_header.find('figure', class_='article-hat-img')
            if figure_hat_img:
                img_tag = figure_hat_img.find('img')
                if img_tag:
                    data['thumbnail'] = img_tag.get('data-lazy-src') or img_tag.get('src')

        # extract images de l'article
        content_div = soup.find('div', class_='entry-content')
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

        # extract Tags/Catégories
        terms_div = soup.find('div', class_='article-terms')
        if terms_div:
            tags_list_ul = terms_div.find('ul', class_='tags-list')
            if tags_list_ul:
                tag_links = tags_list_ul.find_all('a', class_='post-tags')
                if tag_links:
                    data['tags'] = [link.get_text(strip=True) for link in tag_links]
                    if data['tags']:
                        data['category'] = data['tags'][0] # Utilise le premier tag comme catégorie

        debug_print(f"Successfully scraped full details for: {data.get('title', article_url)}", level="success")
        return data

    # gestion des exceptions
    except requests.exceptions.RequestException as e:
        debug_print(f"Request Error fetching full details from {article_url}: {e}", level="error")
        return None # Indique l'échec
    except Exception as e:
        debug_print(f"Parsing Error fetching full details from {article_url}: {e}", level="error")
        # Retourner ce qui a pu être extrait avant l'erreur de parsing
        return data