import streamlit as st
import TP_BeautifulSoup4 as scraper # Importe le module de scraping
import requests # Nécessaire pour définir les headers
import mongo_connect as db_connector # Importer pour la sauvegarde optionnelle
from pymongo.errors import PyMongoError # Pour la sauvegarde optionnelle

# --- Titre spécifique à la page ---
st.title("🚀 Scraper un Article Spécifique")
st.write("Entrez l'URL d'un article du Blog du Modérateur pour en extraire les informations.")

# --- Champ d'entrée pour l'URL ---
article_url = st.text_input("URL de l'article à scraper", placeholder="https://www.blogdumoderateur.com/...", key="scrape_url")

# --- Bouton pour lancer le scraping ---
scrape_button = st.button("Scraper cet Article", key="scrape_button")

# --- Logique de scraping et affichage ---
if scrape_button and article_url:
    if not article_url.startswith("https://www.blogdumoderateur.com/"):
        st.warning("Veuillez entrer une URL valide commençant par 'https://www.blogdumoderateur.com/'")
    else:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        with st.spinner(f"Scraping de l'article : {article_url}..."):
            try:
                # Utiliser la nouvelle fonction pour obtenir tous les détails
                article_data = scraper.scrape_article_full_details(article_url, headers)

                if article_data is None or article_data.get('title') is None: # Vérifier si le scraping a échoué ou n'a rien trouvé d'essentiel
                     st.error("Impossible de scraper les détails de cet article. Vérifiez l'URL ou la structure de la page.")
                else:
                    st.success("Scraping terminé !")

                    # Afficher les informations récupérées
                    if article_data.get("title"):
                        st.subheader(f"Article : {article_data['title']}")
                    else:
                         st.subheader(f"Détails pour : {article_url}")

                    # Afficher la miniature principale
                    if article_data.get("thumbnail"):
                        st.image(article_data["thumbnail"], caption="Image principale", use_column_width=True)

                    # Métadonnées
                    meta_info = []
                    if article_data.get("author"): meta_info.append(f"👤 **Auteur:** {article_data['author']}")
                    if article_data.get("date_iso"): meta_info.append(f"📅 **Date:** {article_data['date_iso']}")
                    elif article_data.get("date_display"): meta_info.append(f"📅 **Date:** {article_data['date_display']}")
                    # Subcategory n'est pas scrapée ici, donc on ne l'affiche pas
                    # if article_data.get("subcategory"): meta_info.append(f"🏷️ **Catégorie:** {article_data['subcategory']}")
                    if meta_info: st.write(" | ".join(meta_info))


                    # Afficher le résumé
                    if article_data.get("summary"):
                        st.write("**Résumé (Chapeau) :**")
                        st.info(article_data["summary"])
                    else:
                        st.warning("Résumé non trouvé.")

                    # Afficher les images du contenu
                    content_images = article_data.get("content_images", [])
                    if content_images:
                        st.write(f"**{len(content_images)} Image(s) trouvée(s) dans le contenu :**")
                        with st.expander("Voir les images du contenu"):
                            for img_data in content_images:
                                st.image(img_data.get("url"), caption=img_data.get("caption_or_alt", ""), use_column_width=True)
                    else:
                        st.write("Aucune image trouvée dans le contenu.")

                    # Bouton pour sauvegarder dans MongoDB
                    st.divider()
                    if st.button("Sauvegarder cet article dans MongoDB", key="save_scraped"):
                        collection = db_connector.connect_to_mongo()
                        if collection is not None:
                            try:
                                # Vérifier si l'URL existe déjà pour éviter les doublons
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


            except requests.exceptions.RequestException as e:
                st.error(f"Erreur de requête lors du scraping : {e}")
            except Exception as e:
                st.error(f"Erreur inattendue lors du scraping : {e}")

elif scrape_button and not article_url:
    st.warning("Veuillez entrer une URL.")