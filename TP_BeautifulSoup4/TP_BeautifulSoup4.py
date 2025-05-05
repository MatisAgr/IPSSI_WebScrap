import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time # Import time for potential delays


def scrape_article_details(article_url, headers):
    """
    Récupère et scrape les détails (résumé, auteur, images de contenu, tags) depuis la page d'un article unique.
    Retourne un dictionnaire avec 'summary', 'author', 'content_images', et 'tags'.
    """
    summary = None
    author = None
    content_images = [] # Initialise la liste pour les images
    tags = []           # Initialise la liste pour les tags
    try:
        # time.sleep(0.5) # Délai optionnel
        response = requests.get(article_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Extraire le Résumé (Chapeau) ---
        summary_div = soup.find('div', class_='article-hat')
        summary_p = summary_div.find('p') if summary_div else None
        summary = summary_p.get_text(strip=True) if summary_p else None

        # --- Extraire l'Auteur ---
        # Cherche dans l'en-tête principal d'abord pour plus de précision
        main_header = soup.find('header', class_='article-header')
        if main_header:
            meta_section = main_header.find('div', class_='entry-meta', recursive=False)
            if meta_section:
                meta_info_div = meta_section.find('div', class_='meta-info')
                if meta_info_div:
                    byline_span = meta_info_div.find('span', class_='byline')
                    if byline_span:
                        author_a = byline_span.find('a')
                        author = author_a.get_text(strip=True) if author_a else None
        # Fallback si non trouvé dans l'en-tête (moins précis)
        if author is None:
            meta_info_div_fallback = soup.find('div', class_='meta-info') # Recherche globale
            if meta_info_div_fallback:
                byline_span = meta_info_div_fallback.find('span', class_='byline')
                if byline_span:
                    author_a = byline_span.find('a')
                    author = author_a.get_text(strip=True) if author_a else None


        # --- Extraire les Images du Contenu ---
        content_div = soup.find('div', class_='entry-content') # Trouve la zone de contenu principal
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
            else: # Fallback
                images_in_content = content_div.find_all('img')
                for img_tag in images_in_content:
                    img_url = img_tag.get('data-lazy-src') or img_tag.get('src')
                    if not img_url or img_url.startswith('data:image'): continue
                    caption = img_tag.get('alt', '')
                    content_images.append({'url': img_url, 'caption_or_alt': caption})

        # --- Extraire les Tags/Catégories (en bas de page) ---
        terms_div = soup.find('div', class_='article-terms')
        if terms_div:
            tags_list_ul = terms_div.find('ul', class_='tags-list')
            if tags_list_ul:
                tag_links = tags_list_ul.find_all('a', class_='post-tags')
                if tag_links:
                    tags = [link.get_text(strip=True) for link in tag_links]

        return {'summary': summary, 'author': author, 'content_images': content_images, 'tags': tags}

    except requests.exceptions.RequestException as e:
        print(f"  -> Erreur Requête lors de la récupération des détails de {article_url}: {e}")
        # Retourne le dict par défaut avec les listes vides
        return {'summary': None, 'author': None, 'content_images': [], 'tags': []}
    except Exception as e:
        print(f"  -> Erreur Parsing lors de la récupération des détails de {article_url}: {e}")
        # Retourne les données potentiellement partielles, incluant les tags trouvés jusqu'à l'erreur
        return {'summary': summary, 'author': author, 'content_images': content_images, 'tags': tags}


def scrape_article_previews(listing_url):
    """
    Scrapes article previews from a listing page on blogdumoderateur.com,
    then fetches details (summary, author, content images, tags) from each article's page.

    Args:
        listing_url (str): The URL of the listing page.

    Returns:
        list: A list of dictionaries, each containing data for one article.
              Returns an empty list if scraping fails or no articles are found.
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

        article_tags_html = soup.find_all('article', class_=re.compile(r'\bpost-\d+\b')) # Renommé pour éviter confusion avec les tags de catégorie

        if not article_tags_html:
            print(f"No article previews found on {listing_url} with the selector.")
            return []

        print(f"Found {len(article_tags_html)} article previews. Now fetching details (summary, author, images, tags)...")

        for idx, article_html in enumerate(article_tags_html): # Utilise le nouveau nom de variable
            data = {}
            print(f"Processing preview {idx+1}/{len(article_tags_html)}...")

            # --- Extract data from the preview ---
            header = article_html.find('header', class_='entry-header')
            a_tag = header.find('a') if header else None
            data['url'] = a_tag['href'] if a_tag and a_tag.has_attr('href') else None
            title_tag = header.find('h3', class_='entry-title') if header else None
            data['title'] = title_tag.get_text(strip=True) if title_tag else None

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
                         data['date_iso'] = datetime.fromisoformat(date_iso_str.split('T')[0]).strftime('%Y-%m-%d')
                     except (ValueError, IndexError): data['date_iso'] = None
                 else: data['date_iso'] = None
            else:
                 data['date_display'] = None
                 data['date_iso'] = None

            # --- Fetch and scrape details (summary, author, images, TAGS) from the article page ---
            data['summary'] = None
            data['author'] = None
            data['content_images'] = []
            data['tags'] = [] # Initialise la liste des tags
            if data['url']:
                print(f"  Fetching details for: {data['title'] or data['url']}")
                # time.sleep(0.2)
                details = scrape_article_details(data['url'], headers) # Appel de la fonction modifiée
                data['summary'] = details.get('summary')
                data['author'] = details.get('author')
                data['content_images'] = details.get('content_images', [])
                data['tags'] = details.get('tags', []) # Récupère les tags
            else:
                print("  Skipping details fetch (no URL found in preview).")

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
    # Initialisation du dictionnaire avec toutes les clés attendues
    data = {
        'url': article_url,
        'title': None,
        'summary': None,
        'author': None,
        'date_display': None,
        'date_iso': None,
        'thumbnail': None,
        'category': None, # Sera défini comme le premier tag trouvé
        'tags': [],       # Liste complète des tags
        'content_images': []
    }

    try:
        # time.sleep(0.5) # Délai optionnel
        response = requests.get(article_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Trouver l'en-tête principal de l'article ---
        main_header = soup.find('header', class_='article-header')
        if not main_header:
            print(f"  -> Attention : En-tête principal ('header.article-header') non trouvé sur {article_url}")
            # Essayer quand même de trouver les autres infos ci-dessous
        else:
            # --- Extraire le Titre ---
            title_tag = main_header.find('h1', class_='entry-title')
            data['title'] = title_tag.get_text(strip=True) if title_tag else None

            # --- Extraire le Résumé (Chapeau) ---
            summary_div = main_header.find('div', class_='article-hat')
            summary_p = summary_div.find('p') if summary_div else None
            data['summary'] = summary_p.get_text(strip=True) if summary_p else None

            # --- Extraire l'Auteur & la Date (Tentative 1: dans le header) ---
            meta_section_header = main_header.find('div', class_='entry-meta', recursive=False)
            if meta_section_header:
                meta_info_div_header = meta_section_header.find('div', class_='meta-info')
                if meta_info_div_header:
                    # Auteur
                    byline_span = meta_info_div_header.find('span', class_='byline')
                    if byline_span:
                        author_a = byline_span.find('a')
                        data['author'] = author_a.get_text(strip=True) if author_a else None
                    # Date
                    posted_on_span = meta_info_div_header.find('span', class_='posted-on')
                    if posted_on_span:
                        time_tag = posted_on_span.find('time', class_='published')
                        if time_tag:
                            data['date_display'] = time_tag.get_text(strip=True)
                            if time_tag.has_attr('datetime'):
                                try:
                                    date_iso_str = time_tag['datetime']
                                    # Essayer de parser et formater
                                    data['date_iso'] = datetime.fromisoformat(date_iso_str.replace(' ', 'T')).strftime('%Y-%m-%d')
                                except ValueError:
                                    pass # Laisser None si le format est inattendu

            # --- Extraire la Miniature / Image d'en-tête ---
            figure_hat_img = main_header.find('figure', class_='article-hat-img')
            if figure_hat_img:
                img_tag = figure_hat_img.find('img')
                if img_tag:
                    data['thumbnail'] = img_tag.get('data-lazy-src') or img_tag.get('src')

        # --- Extraire l'Auteur & la Date (Tentative 2: dans article-social-content, si non trouvés avant) ---
        if data['author'] is None or data['date_iso'] is None:
            social_content_div = soup.find('div', class_='article-social-content')
            if social_content_div:
                meta_info_div_social = social_content_div.find('div', class_='meta-info')
                if meta_info_div_social:
                    # Auteur (si pas déjà trouvé)
                    if data['author'] is None:
                        byline_span = meta_info_div_social.find('span', class_='byline')
                        if byline_span:
                            author_a = byline_span.find('a')
                            data['author'] = author_a.get_text(strip=True) if author_a else None
                    # Date (si pas déjà trouvée)
                    if data['date_iso'] is None:
                        posted_on_span = meta_info_div_social.find('span', class_='posted-on')
                        if posted_on_span:
                            time_tag = posted_on_span.find('time', class_='published') # ou 'entry-date'
                            if not time_tag: # Essayer avec 'entry-date' comme classe alternative
                                time_tag = posted_on_span.find('time', class_='entry-date')
                            if time_tag:
                                data['date_display'] = time_tag.get_text(strip=True)
                                if time_tag.has_attr('datetime'):
                                    try:
                                        date_iso_str = time_tag['datetime']
                                        # Essayer de parser et formater (gère T ou espace comme séparateur)
                                        data['date_iso'] = datetime.fromisoformat(date_iso_str.replace(' ', 'T')).strftime('%Y-%m-%d')
                                    except ValueError:
                                        pass # Laisser None si le format est inattendu

        # --- Extraire les Images du Contenu ---
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

        # --- Extraire les Tags/Catégories (en bas de page) ---
        terms_div = soup.find('div', class_='article-terms')
        if terms_div:
            tags_list_ul = terms_div.find('ul', class_='tags-list')
            if tags_list_ul:
                tag_links = tags_list_ul.find_all('a', class_='post-tags')
                if tag_links:
                    data['tags'] = [link.get_text(strip=True) for link in tag_links]
                    if data['tags']:
                        data['category'] = data['tags'][0]

        return data # Retourne le dictionnaire avec toutes les données trouvées

    except requests.exceptions.RequestException as e:
        print(f"  -> Erreur Requête lors de la récupération des détails complets de {article_url}: {e}")
        return None # Indique l'échec
    except Exception as e:
        print(f"  -> Erreur Parsing lors de la récupération des détails complets de {article_url}: {e}")
        # Retourne les données potentiellement partielles trouvées jusqu'à l'erreur
        return data

