import requests # requêtes HTTP
from bs4 import BeautifulSoup # scraper
from datetime import datetime
import re # regex
import time # Pour délai optionnel

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
                 # Vérifier si l'URL commence par base_url OU est une URL relative commençant par /
                 # Exclure les URLs non pertinentes comme /tools/ ou la page d'accueil elle-même
                 if href.startswith(base_url) and href != base_url:
                     category_urls.append(href)
                 elif href.startswith('/') and not href.startswith('/tools/') and href != '/':
                     # Construire l'URL absolue pour les liens relatifs
                     from urllib.parse import urljoin
                     absolute_url = urljoin(base_url, href)
                     category_urls.append(absolute_url)


        # Supprimer les doublons potentiels
        category_urls = list(dict.fromkeys(category_urls))

        debug_print(f"Extracted {len(category_urls)} unique category URLs.", level="success")
        return category_urls

    except requests.exceptions.RequestException as e:
        debug_print(f"Request Error fetching base page {base_url}: {e}", level="error")
        return []
    except Exception as e:
        debug_print(f"An unexpected error occurred while scraping category URLs from {base_url}: {e}", level="error")
        return []


# scrap une liste d'articles d'une page
# utilisé dans ./pages/Scrap_category.py et main.py
def scrape_articles_from_listing(listing_url):
    global headers
    articles_data = []

    try:
        debug_print(f"Fetching listing page: {listing_url}...", level="fetch")
        response_listing = requests.get(listing_url, headers=headers, timeout=10)
        response_listing.raise_for_status()
        soup_listing = BeautifulSoup(response_listing.text, 'html.parser')

        # Trouver les blocs d'aperçu d'articles
        article_tags_html = soup_listing.find_all('article', class_=re.compile(r'\bpost-\d+\b'))

        if not article_tags_html:
            debug_print(f"No article previews found on {listing_url}.", level="warning")
            return []

        debug_print(f"Found {len(article_tags_html)} article previews. Fetching full details for each...", level="info")

        for idx, article_html in enumerate(article_tags_html):
            data = { # Initialiser le dictionnaire pour chaque article
                'url': None, 'title': None, 'thumbnail': None, 'category': None,
                'date_display': None, 'date_iso': None, 'summary': None,
                'author': None, 'content_images': [], 'tags': []
            }
            start_time = time.time() # Pour mesurer le temps par article

            # --- Extraction depuis l'aperçu (fallback ou info primaire) ---
            header_preview = article_html.find('header', class_='entry-header')
            a_tag_preview = header_preview.find('a') if header_preview else None
            article_url = a_tag_preview['href'] if a_tag_preview and a_tag_preview.has_attr('href') else None
            data['url'] = article_url

            title_tag_preview = header_preview.find('h3', class_='entry-title') if header_preview else None
            title_preview = title_tag_preview.get_text(strip=True) if title_tag_preview else "No Title Found"

            img_div_preview = article_html.find('div', class_='post-thumbnail')
            img_tag_preview = img_div_preview.find('img') if img_div_preview else None
            thumbnail_preview = img_tag_preview.get('data-lazy-src') or img_tag_preview.get('src') if img_tag_preview else None
            data['thumbnail'] = thumbnail_preview # Sera potentiellement écrasé par l'image de l'article

            meta_div_preview = article_html.find('div', class_='entry-meta')
            category_tag_preview = meta_div_preview.find('span', class_=re.compile(r'\bfavtag\b')) if meta_div_preview else None
            data['category'] = category_tag_preview.get_text(strip=True) if category_tag_preview else None # Catégorie de l'aperçu

            date_tag_preview = meta_div_preview.find('time', class_='published') if meta_div_preview else None
            if date_tag_preview:
                 data['date_display'] = date_tag_preview.get_text(strip=True)
                 if date_tag_preview.has_attr('datetime'):
                     try:
                         date_iso_str = date_tag_preview['datetime'].replace(' ', 'T')
                         data['date_iso'] = datetime.fromisoformat(date_iso_str.split('T')[0]).strftime('%Y-%m-%d')
                     except (ValueError, IndexError): pass # date_iso reste None

            # --- Si URL trouvée, scraper la page de l'article pour les détails complets ---
            if article_url:
                debug_print(f"  [{idx+1}/{len(article_tags_html)}] Fetching details: {article_url}", level="fetch", end='\r')
                try:
                    # time.sleep(0.2) # Délai très court optionnel
                    response_article = requests.get(article_url, headers=headers, timeout=10)
                    response_article.raise_for_status()
                    soup_article = BeautifulSoup(response_article.text, 'html.parser')

                    # --- Extraction depuis la page article (prioritaire) ---
                    main_header_article = soup_article.find('header', class_='article-header')
                    if main_header_article:
                        # Titre (prioritaire)
                        title_tag_article = main_header_article.find('h1', class_='entry-title')
                        if title_tag_article: data['title'] = title_tag_article.get_text(strip=True)

                        # Résumé
                        summary_div_article = main_header_article.find('div', class_='article-hat')
                        summary_p_article = summary_div_article.find('p') if summary_div_article else None
                        if summary_p_article: data['summary'] = summary_p_article.get_text(strip=True)

                        # Auteur & Date (prioritaire)
                        meta_section_article = main_header_article.find('div', class_=re.compile(r'\bentry-meta\b'))
                        if meta_section_article:
                            meta_info_div_article = meta_section_article.find('div', class_='meta-info')
                            if meta_info_div_article:
                                # Auteur
                                byline_span = meta_info_div_article.find('span', class_='byline')
                                if byline_span:
                                    author_a = byline_span.find('a')
                                    if author_a: data['author'] = author_a.get_text(strip=True)
                                # Date (prioritaire si trouvée)
                                posted_on_span = meta_info_div_article.find('span', class_='posted-on')
                                if posted_on_span:
                                    time_tag_article = posted_on_span.find('time', class_='published')
                                    if time_tag_article:
                                        data['date_display'] = time_tag_article.get_text(strip=True)
                                        if time_tag_article.has_attr('datetime'):
                                            try:
                                                date_iso_str = time_tag_article['datetime'].replace(' ', 'T')
                                                data['date_iso'] = datetime.fromisoformat(date_iso_str.split('T')[0]).strftime('%Y-%m-%d')
                                            except ValueError: pass # date_iso reste celui de l'aperçu ou None

                        # Miniature (Image d'en-tête prioritaire)
                        figure_hat_img = main_header_article.find('figure', class_='article-hat-img')
                        if figure_hat_img:
                            img_tag_hat = figure_hat_img.find('img')
                            if img_tag_hat:
                                data['thumbnail'] = img_tag_hat.get('data-lazy-src') or img_tag_hat.get('src')

                    # Si le titre n'a pas été trouvé sur la page article, utiliser celui de l'aperçu
                    if not data['title']: data['title'] = title_preview

                    # Images du contenu
                    content_div_article = soup_article.find('div', class_='entry-content')
                    if content_div_article:
                        figures = content_div_article.find_all('figure')
                        if figures:
                            for figure in figures:
                                img_tag = figure.find('img')
                                if img_tag:
                                    img_url = img_tag.get('data-lazy-src') or img_tag.get('src')
                                    if not img_url or img_url.startswith('data:image'): continue
                                    figcaption = figure.find('figcaption')
                                    caption = figcaption.get_text(strip=True) if figcaption else img_tag.get('alt', '')
                                    data['content_images'].append({'url': img_url, 'caption_or_alt': caption})
                        else: # Fallback si pas de <figure>
                            images_in_content = content_div_article.find_all('img')
                            for img_tag in images_in_content:
                                img_url = img_tag.get('data-lazy-src') or img_tag.get('src')
                                if not img_url or img_url.startswith('data:image'): continue
                                caption = img_tag.get('alt', '')
                                data['content_images'].append({'url': img_url, 'caption_or_alt': caption})

                    # Tags (depuis la page article)
                    terms_div_article = soup_article.find('div', class_='article-terms')
                    if terms_div_article:
                        tags_list_ul = terms_div_article.find('ul', class_='tags-list')
                        if tags_list_ul:
                            tag_links = tags_list_ul.find_all('a', class_='post-tags')
                            if tag_links:
                                data['tags'] = [link.get_text(strip=True) for link in tag_links]
                                # Si la catégorie de l'aperçu était None, utiliser le premier tag
                                if not data['category'] and data['tags']:
                                    data['category'] = data['tags'][0]

                    # Effacer la ligne de progression
                    elapsed_time = time.time() - start_time
                    print(f"  [{idx+1}/{len(article_tags_html)}] Done: {data.get('title', 'N/A')[:40]}... ({elapsed_time:.2f}s)      ", end='\r')


                except requests.exceptions.RequestException as e_article:
                    print(' ' * 100, end='\r') # Clear line
                    debug_print(f"  [{idx+1}/{len(article_tags_html)}] Request Error for {article_url}: {e_article}", level="error")
                    # Garder les infos de l'aperçu si l'article n'a pas pu être chargé
                    if not data['title']: data['title'] = title_preview
                    # On ne peut pas récupérer summary, author, content_images, tags
                except Exception as e_parse:
                    print(' ' * 100, end='\r') # Clear line
                    debug_print(f"  [{idx+1}/{len(article_tags_html)}] Parsing Error for {article_url}: {e_parse}", level="error")
                    # Garder les infos de l'aperçu et ce qui a pu être parsé avant l'erreur
                    if not data['title']: data['title'] = title_preview

            else:
                # Cas où l'URL n'a pas été trouvée dans l'aperçu
                print(' ' * 100, end='\r') # Clear line
                debug_print(f"  [{idx+1}/{len(article_tags_html)}] Skipping details fetch (no URL found in preview). Title: {title_preview}", level="warning")
                data['title'] = title_preview # Assigner le titre de l'aperçu

            # Ajouter les données (même si incomplètes) si on a au moins une URL ou un titre valide
            if data.get('url') or data.get('title') != "No Title Found":
                articles_data.append(data)

        print() # Saut de ligne après la boucle
        debug_print(f"Successfully scraped {len(articles_data)} articles with details from {listing_url}.", level="success")
        return articles_data

    # gestion des exceptions pour la page de listing principale
    except requests.exceptions.RequestException as e_listing:
        debug_print(f"Request Error fetching listing page {listing_url}: {e_listing}", level="error")
        return []
    except Exception as e_general:
        debug_print(f"An unexpected error occurred while scraping {listing_url}: {e_general}", level="error")
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
            meta_section_header = main_header.find('div', class_=re.compile(r'\bentry-meta\b'))
            if meta_section_header:
                meta_info_div_header = meta_section_header.find('div', class_='meta-info')
                if meta_info_div_header:
                    # extract auteur
                    byline_span = meta_info_div_header.find('span', class_='byline')
                    # debug_print(f"  -> byline_span: {byline_span}", level="debug")
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
                                    date_iso_str = date_iso_str.replace(' ', 'T')
                                    data['date_iso'] = datetime.fromisoformat(date_iso_str.split('T')[0]).strftime('%Y-%m-%d')
                                except ValueError:
                                    debug_print(f"Could not parse date: {time_tag.get('datetime')}", level="warning")
                                    pass

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
                        # Si category n'a pas été trouvée dans l'aperçu (ce qui est le cas ici)
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