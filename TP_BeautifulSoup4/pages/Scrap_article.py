import streamlit as st
import requests
from pymongo.errors import PyMongoError

# custom
import TP_BeautifulSoup4 as scraper
import mongo_connect as db_connector

# cache de session
if 'article_data_to_display' not in st.session_state:
    st.session_state.article_data_to_display = None

st.title("🚀 Scraper un Article Spécifique")
st.write("Entrez l'URL d'un article du Blog du Modérateur pour en extraire les informations.")

# input url
article_url = st.text_input("URL de l'article à scraper", placeholder="https://www.blogdumoderateur.com/...", key="scrape_url")

# bouton start scraping (article)
scrape_button = st.button("Scraper cet Article", key="scrape_button")

if scrape_button and article_url:
    if not article_url.startswith("https://www.blogdumoderateur.com/"):
        st.warning("Veuillez entrer une URL valide commençant par 'https://www.blogdumoderateur.com/'")
        st.session_state.article_data_to_display = None # Réinitialiser en cas d'URL invalide
    else:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        with st.spinner(f"Scraping de l'article : {article_url}..."):
            try:
                article_data = scraper.scrape_article_full_details(article_url, headers)

                if article_data is None or article_data.get('title') is None:
                     st.error("Impossible de scraper les détails de cet article. Vérifiez l'URL ou la structure de la page.")
                     st.session_state.article_data_to_display = None
                else:
                    st.success("Scraping terminé !")
                    st.session_state.article_data_to_display = article_data

            # gestion des exceptions
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur de requête lors du scraping : {e}")
                st.session_state.article_data_to_display = None
            except Exception as e:
                st.error(f"Erreur inattendue lors du scraping : {e}")
                st.session_state.article_data_to_display = None

elif scrape_button and not article_url:
    st.warning("Veuillez entrer une URL.")
    st.session_state.article_data_to_display = None # reset

# si l'article a été scrappé, afficher les détails 
if st.session_state.article_data_to_display:
    article_data = st.session_state.article_data_to_display

    # utiliser titre sinon url
    if article_data.get("title"):
        st.subheader(f"Article : {article_data['title']}")
    else:
         st.subheader(f"Détails pour : {article_data['url']}")

    if article_data.get("thumbnail"):
        st.image(article_data["thumbnail"], caption="Image principale", use_column_width=True)

    meta_info = []
    if article_data.get("author"): meta_info.append(f"👤 **Auteur:** {article_data['author']}")
    if article_data.get("date_iso"): meta_info.append(f"📅 **Date:** {article_data['date_iso']}")
    elif article_data.get("date_display"): meta_info.append(f"📅 **Date:** {article_data['date_display']}")
    if meta_info: st.write(" | ".join(meta_info))

    if article_data.get("summary"):
        st.write("**Résumé :**")
        st.info(article_data["summary"])
    else:
        st.warning("Résumé non trouvé.")

    content_images = article_data.get("content_images", [])
    if content_images:
        st.write(f"**{len(content_images)} Image(s) trouvée(s) dans le contenu :**")
        with st.expander("Voir les images du contenu"):
            for img_data in content_images:
                st.image(img_data.get("url"), caption=img_data.get("caption_or_alt", ""), use_column_width=True)
    else:
        st.write("Aucune image trouvée dans le contenu.")

    st.divider()
    if st.button("Sauvegarder cet article dans MongoDB", key="save_scraped"):
        collection = db_connector.connect_to_mongo()
        if collection is not None:
            try:
                existing = collection.find_one({'url': article_data['url']})
                if existing:
                    st.warning(f"Cet article (URL: {article_data['url']}) existe déjà dans la base de données (ID: {existing['_id']}).")
                else:
                    insert_result = collection.insert_one(article_data)
                    st.success(f"Article sauvegardé avec succès ! (ID: {insert_result.inserted_id})")
            except PyMongoError as e:
                st.error(f"Erreur MongoDB lors de la sauvegarde : {e}")
            except Exception as e:
                st.error(f"Erreur inattendue lors de la sauvegarde : {e}")
        else:
            st.error("Connexion à MongoDB échouée, impossible de sauvegarder.")
