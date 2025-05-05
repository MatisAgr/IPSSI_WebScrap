import streamlit as st
import mongo_connect as db_connector # Assurez-vous que mongo_connect.py est accessible
from datetime import datetime, time
import re
from bson import ObjectId

# --- Titre spécifique à la page ---
st.title("🔎 Recherche d'Articles dans la Base de Données")
st.write("Filtrez et explorez les articles précédemment scrapés et stockés dans MongoDB.")

# --- Connexion à MongoDB ---
@st.cache_resource # Cache la ressource de connexion
def get_db_collection():
    """Tente de se connecter à MongoDB et retourne l'objet collection."""
    # Chemin relatif pour remonter d'un niveau si nécessaire, mais Python devrait gérer l'import direct
    collection = db_connector.connect_to_mongo()
    if collection is None:
        st.error("❌ Échec de la connexion à MongoDB. Vérifiez que le serveur est lancé et accessible.")
    return collection

articles_collection = get_db_collection()

# --- Fonction pour construire la requête MongoDB ---
def build_mongo_query(start_date, end_date, author, category, title_substring):
    """Construit le dictionnaire de requête MongoDB basé sur les filtres."""
    query = {}
    date_query = {}
    if start_date:
        date_query["$gte"] = start_date.strftime('%Y-%m-%d')
    if end_date:
        date_query["$lte"] = end_date.strftime('%Y-%m-%d')
    if date_query:
        query["date_iso"] = date_query
    if author:
        query["author"] = {"$regex": re.escape(author), "$options": "i"}
    if category:
        query["subcategory"] = {"$regex": re.escape(category), "$options": "i"}
    if title_substring:
        query["title"] = {"$regex": re.escape(title_substring), "$options": "i"}
    return query

# --- Interface de Filtrage dans la Sidebar ---
st.sidebar.header("🔍 Filtres de Recherche")
start_date_input = st.sidebar.date_input("Date de début", value=None, key="search_start_date")
end_date_input = st.sidebar.date_input("Date de fin", value=None, key="search_end_date")
author_input = st.sidebar.text_input("Auteur contient", key="search_author")
category_input = st.sidebar.text_input("Catégorie/Sous-catégorie contient", key="search_category")
title_input = st.sidebar.text_input("Titre contient", key="search_title")
# apply_filters = st.sidebar.button("Appliquer les Filtres", key="search_apply") # Le bouton n'est pas strictement nécessaire

# --- Affichage des Articles ---
if articles_collection is not None:
    query = build_mongo_query(start_date_input, end_date_input, author_input, category_input, title_input)
    st.subheader(f"Résultats ({'Filtres actifs' if query else 'Tous les articles'})")

    try:
        filtered_articles = list(articles_collection.find(query).sort("date_iso", -1))
        if not filtered_articles:
            st.warning("Aucun article ne correspond à vos critères.")
        else:
            st.info(f"{len(filtered_articles)} article(s) trouvé(s).")
            num_columns = 3
            cols = st.columns(num_columns)
            for i, article in enumerate(filtered_articles):
                col_index = i % num_columns
                with cols[col_index]:
                    with st.container(border=True):
                        if article.get("title") and article.get("url"):
                            st.subheader(f"[{article['title']}]({article['url']})")
                        elif article.get("title"):
                            st.subheader(article['title'])
                        if article.get("thumbnail"):
                            st.image(article["thumbnail"], use_column_width=True)
                        meta_info = []
                        if article.get("author"): meta_info.append(f"👤 {article['author']}")
                        if article.get("date_iso"): meta_info.append(f"📅 {article['date_iso']}")
                        elif article.get("date_display"): meta_info.append(f"📅 {article['date_display']}")
                        if article.get("subcategory"): meta_info.append(f"🏷️ {article['subcategory']}")
                        if meta_info: st.caption(" | ".join(meta_info))
                        if article.get("summary"):
                            with st.expander("Résumé"): st.write(article["summary"])
                        if article.get("url"): st.link_button("Lire l'article ↗️", article["url"])
                        if article.get("content_images"):
                             with st.expander(f"{len(article['content_images'])} image(s)"):
                                 for img_data in article["content_images"]:
                                     st.image(img_data.get("url"), caption=img_data.get("caption_or_alt", ""), use_column_width=True)
    except Exception as e:
        st.error(f"Erreur lors de la récupération des articles : {e}")
else:
    st.info("Connexion à MongoDB en attente ou échouée.")
