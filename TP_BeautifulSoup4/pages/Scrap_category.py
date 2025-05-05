import streamlit as st
import sys
import os
from pymongo.errors import PyMongoError
import requests
import re # Importer re pour la mise en page

# --- Configuration et Imports ---
# Assurez-vous que le répertoire parent est dans le path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import TP_BeautifulSoup4 as scraper # Importe depuis le répertoire parent
import mongo_connect as db_connector # Importe depuis le répertoire parent

# --- Constantes ---
BASE_URL = "https://www.blogdumoderateur.com/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- Fonction pour récupérer les URLs des catégories (avec cache) ---
@st.cache_data(ttl=3600) # Cache les résultats pendant 1 heure
def get_category_urls():
    """Récupère les URLs des catégories depuis le site."""
    print("Attempting to fetch category URLs...") # Pour le débogage
    urls = scraper.scrape_category_urls(BASE_URL, HEADERS)
    print(f"Fetched URLs: {urls}") # Pour le débogage
    return urls

# --- Initialiser l'état de session ---
if 'category_articles_to_display' not in st.session_state:
    st.session_state.category_articles_to_display = None
if 'category_url_processed' not in st.session_state:
    st.session_state.category_url_processed = ""
if 'selected_category_url' not in st.session_state:
     st.session_state.selected_category_url = None # Pour stocker la sélection

# --- Titre spécifique à la page ---
st.title("🗂️ Scraper une Catégorie d'Articles")
st.write("Choisissez une catégorie dans la liste ci-dessous pour scraper tous les articles listés sur cette page.")

# --- Récupérer les URLs des catégories ---
category_urls = get_category_urls()

# --- Afficher la liste déroulante ou un message d'erreur ---
if category_urls:
    # Créer une liste d'options pour le selectbox (URL -> Nom lisible si possible)
    # Ici, on utilise juste les URLs comme options pour simplifier
    # On pourrait extraire le nom de la catégorie de l'URL ou du texte du lien si scrape_category_urls le retournait
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
    st.stop() # Arrête l'exécution du script si les catégories ne peuvent pas être chargées

# --- Bouton pour lancer le scraping (maintenant basé sur la sélection) ---
# Désactiver le bouton si aucune catégorie n'est sélectionnée
scrape_category_button = st.button(
    "Scraper cette Catégorie",
    key="scrape_category_button",
    disabled=not st.session_state.selected_category_url # Désactivé si rien n'est sélectionné
)

# --- Logique de scraping (utilise st.session_state.selected_category_url) ---
if scrape_category_button and st.session_state.selected_category_url:
    selected_url = st.session_state.selected_category_url
    # La validation startswith n'est plus nécessaire car les URLs viennent de notre scraping
    with st.spinner(f"Scraping de la catégorie : {selected_url}..."):
        try:
            # Utilise la fonction qui récupère aussi les détails (summary, author, etc.)
            articles_data = scraper.scrape_article_previews(selected_url)

            if not articles_data:
                st.warning("Aucun article trouvé sur cette page ou erreur lors du scraping.")
                st.session_state.category_articles_to_display = None
                st.session_state.category_url_processed = ""
            else:
                st.success(f"Scraping terminé ! {len(articles_data)} article(s) trouvé(s).")
                st.session_state.category_articles_to_display = articles_data
                st.session_state.category_url_processed = selected_url # Stocker l'URL traitée

        except requests.exceptions.RequestException as e:
            st.error(f"Erreur de requête lors du scraping : {e}")
            st.session_state.category_articles_to_display = None
            st.session_state.category_url_processed = ""
        except Exception as e:
            st.error(f"Erreur inattendue lors du scraping : {e}")
            st.session_state.category_articles_to_display = None
            st.session_state.category_url_processed = ""

# --- Affichage des résultats ET bouton de sauvegarde (basé sur l'état de session) ---
if st.session_state.category_articles_to_display:
    articles_data = st.session_state.category_articles_to_display
    st.subheader(f"Articles trouvés pour : {st.session_state.category_url_processed}")
    st.info(f"{len(articles_data)} article(s) trouvé(s). Prêt(s) à être sauvegardé(s).")

    # --- Début de la mise en page similaire à IHM_mongo.py ---
    num_columns = 2 # Ou 1 si vous préférez une seule colonne
    cols = st.columns(num_columns)
    for i, article in enumerate(articles_data):
        col_index = i % num_columns
        with cols[col_index]:
            with st.container(border=True):
                # Titre cliquable
                if article.get("title") and article.get("url"):
                    st.subheader(f"[{article['title']}]({article['url']})")
                elif article.get("title"):
                    st.subheader(article['title'])

                # Miniature
                if article.get("thumbnail"):
                    st.image(article["thumbnail"], use_column_width=True)

                # Métadonnées (Auteur, Date, Tags)
                meta_info = []
                if article.get("author"): meta_info.append(f"👤 {article['author']}")
                if article.get("date_iso"): meta_info.append(f"📅 {article['date_iso']}")
                elif article.get("date_display"): meta_info.append(f"📅 {article['date_display']}")
                if article.get("tags"): # Vérifie si la clé 'tags' existe et si la liste n'est pas vide
                    tags_str = ", ".join(article["tags"]) # Joint les tags en une seule chaîne
                    meta_info.append(f"🏷️ Tags: {tags_str}") # Ajoute la chaîne formatée
                if meta_info: st.caption(" | ".join(meta_info))

                # Résumé
                if article.get("summary"):
                    with st.expander("Résumé"): st.write(article["summary"])

                # Bouton Lire l'article
                if article.get("url"): st.link_button("Lire l'article ↗️", article["url"])

                # Images du contenu
                if article.get("content_images"):
                     with st.expander(f"{len(article['content_images'])} image(s) dans le contenu"):
                         for img_data in article["content_images"]:
                             st.image(img_data.get("url"), caption=img_data.get("caption_or_alt", ""), use_column_width=True)
    # --- Fin de la mise en page ---

    st.divider() # Garder le séparateur avant le bouton de sauvegarde

    # Bouton de sauvegarde (reste inchangé)
    if st.button(f"Sauvegarder les {len(articles_data)} articles dans MongoDB", key="save_category_articles"):
        collection = db_connector.connect_to_mongo()
        if collection is not None:
            inserted_count = 0
            skipped_count = 0
            error_count = 0
            with st.spinner("Sauvegarde des articles en cours..."):
                for article in articles_data:
                    try:
                        # Vérifier si l'article existe déjà par URL
                        if article.get('url'):
                            existing = collection.find_one({'url': article['url']})
                            if existing:
                                skipped_count += 1
                                continue # Passer au suivant
                        # Insérer s'il n'existe pas ou si l'URL manque
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
            # Optionnel : Réinitialiser après sauvegarde pour éviter re-sauvegarde accidentelle
            # st.session_state.category_articles_to_display = None
            # st.session_state.category_url_processed = ""
            # st.session_state.selected_category_url = None # Réinitialiser la sélection aussi
            # st.rerun()
        else:
            st.error("Connexion à MongoDB échouée, impossible de sauvegarder.")