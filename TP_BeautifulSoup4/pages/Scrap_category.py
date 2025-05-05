import streamlit as st
from pymongo.errors import PyMongoError #debug pour error mongo
import requests

# custom
import TP_BeautifulSoup4 as scraper
import mongo_connect as db_connector

#CONFIG
BASE_URL = "https://www.blogdumoderateur.com/"

# récupérer les URLs des catégories
@st.cache_data(ttl=3600) # cache 1 heure
def get_category_urls():
    print("Attempting to fetch category URLs...")
    urls = scraper.scrape_category_urls(BASE_URL)
    print(f"Fetched URLs: {urls}")
    return urls

# cache de session
if 'category_articles_to_display' not in st.session_state:
    st.session_state.category_articles_to_display = None
if 'category_url_processed' not in st.session_state:
    st.session_state.category_url_processed = ""
if 'selected_category_url' not in st.session_state:
     st.session_state.selected_category_url = None # Pour stocker la sélection

st.set_page_config(layout="wide")

st.title("🗂️ Scraper une Catégorie d'Articles")
st.write("Choisissez une catégorie dans la liste ci-dessous pour scraper tous les articles listés sur cette page.")

category_urls = get_category_urls()

if category_urls:
    selected_category_url = st.selectbox(
        "Choisissez une catégorie à scraper :",
        options=category_urls,
        index=None, # Ne présélectionne rien
        placeholder="Sélectionnez une catégorie...",
        key="select_category_url" # Clé unique pour le widget
    )
    st.session_state.selected_category_url = selected_category_url # Mettre à jour l'état
else:
    st.error("Impossible de récupérer la liste des catégories depuis le site. Vérifiez la console ou réessayez plus tard.")
    st.stop()

scrape_category_button = st.button(
    "Scraper cette Catégorie",
    key="scrape_category_button",
    disabled=not st.session_state.selected_category_url
)

if scrape_category_button and st.session_state.selected_category_url:
    selected_url = st.session_state.selected_category_url
    with st.spinner(f"Scraping de la catégorie et des détails des articles : {selected_url}..."):
        try:
            # Utiliser la nouvelle fonction fusionnée
            articles_data = scraper.scrape_articles_from_listing(selected_url)

            if not articles_data:
                st.warning("Aucun article trouvé sur cette page ou erreur lors du scraping.")
                st.session_state.category_articles_to_display = None
                st.session_state.category_url_processed = ""
            else:
                st.success(f"Scraping terminé ! {len(articles_data)} article(s) trouvé(s) avec leurs détails.")
                st.session_state.category_articles_to_display = articles_data
                st.session_state.category_url_processed = selected_url

        except requests.exceptions.RequestException as e:
            st.error(f"Erreur de requête lors du scraping de la catégorie : {e}")
            st.session_state.category_articles_to_display = None
            st.session_state.category_url_processed = ""
        except Exception as e:
            st.error(f"Erreur inattendue lors du scraping : {e}")
            st.session_state.category_articles_to_display = None
            st.session_state.category_url_processed = ""

# resultat et btn de sauvegarde
if st.session_state.category_articles_to_display:
    articles_data = st.session_state.category_articles_to_display
    st.subheader(f"Articles trouvés pour : {st.session_state.category_url_processed}")
    st.info(f"{len(articles_data)} article(s) trouvé(s). Prêt(s) à être sauvegardé(s).")

    # mise en page
    num_columns = 2 # nb col
    cols = st.columns(num_columns)
    for i, article in enumerate(articles_data):
        col_index = i % num_columns
        with cols[col_index]:
            with st.container(border=True):
                # titre
                if article.get("title") and article.get("url"):
                    st.subheader(f"[{article['title']}]({article['url']})")
                elif article.get("title"):
                    st.subheader(article['title'])

                # miniature
                if article.get("thumbnail"):
                    st.image(article["thumbnail"], use_column_width=True)

                # auteur, date, tags
                meta_info = []
                if article.get("author"): meta_info.append(f"👤 {article['author']}")
                if article.get("date_iso"): meta_info.append(f"📅 {article['date_iso']}")
                elif article.get("date_display"): meta_info.append(f"📅 {article['date_display']}")
                if article.get("tags"):
                    tags_str = ", ".join(article["tags"]) # joint les tags en une seule chaîne
                    meta_info.append(f"🏷️ Tags: {tags_str}")
                if meta_info: st.caption(" | ".join(meta_info))

                # résumé
                if article.get("summary"):
                    with st.expander("Résumé"): st.write(article["summary"])

                # bouton "Lire l'article"
                if article.get("url"): st.link_button("Lire l'article ↗️", article["url"])

                # images de l'article
                if article.get("content_images"):
                     with st.expander(f"{len(article['content_images'])} image(s) dans le contenu"):
                         for img_data in article["content_images"]:
                             st.image(img_data.get("url"), caption=img_data.get("caption_or_alt", ""), use_column_width=True)

    st.divider()

    # bouton de save
    if st.button(f"Sauvegarder les {len(articles_data)} articles dans MongoDB", key="save_category_articles"):
        collection = db_connector.connect_to_mongo()
        if collection is not None:
            inserted_count = 0
            skipped_count = 0
            error_count = 0
            with st.spinner("Sauvegarde des articles en cours..."):
                for article in articles_data:
                    try:
                        # verif si l'URL existe déjà
                        if article.get('url'):
                            existing = collection.find_one({'url': article['url']})
                            if existing:
                                skipped_count += 1
                                continue
                        collection.insert_one(article)
                        inserted_count += 1
                    except PyMongoError as e:
                        st.warning(f"Erreur MongoDB lors de la sauvegarde de '{article.get('title', 'N/A')}': {e}")
                        error_count += 1
                    except Exception as e:
                        st.warning(f"Erreur inattendue lors de la sauvegarde de '{article.get('title', 'N/A')}': {e}")
                        error_count += 1

            st.success(f"Sauvegarde terminée : {inserted_count} articles insérés.")
            if skipped_count > 0:
                st.info(f"{skipped_count} articles déjà présents ont été ignorés.")
            if error_count > 0:
                st.error(f"{error_count} erreurs rencontrées lors de la sauvegarde.")

        else:
            st.error("Connexion à MongoDB échouée, impossible de sauvegarder.")