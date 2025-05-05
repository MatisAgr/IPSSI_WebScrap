import streamlit as st
import TP_BeautifulSoup4 as scraper # Importe le module de scraping
import requests # Nécessaire pour définir les headers

# --- Titre spécifique à la page ---
st.title("🚀 Scraper un Article Spécifique")
st.write("Entrez l'URL d'un article du Blog du Modérateur pour en extraire les informations.")

# --- Champ d'entrée pour l'URL ---
article_url = st.text_input("URL de l'article à scraper", placeholder="https://www.blogdumoderateur.com/...")

# --- Bouton pour lancer le scraping ---
scrape_button = st.button("Scraper cet Article")

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
                # Note: Nous supposons que scrape_article_details récupère TOUTES les infos
                # Si ce n'est pas le cas, il faudra adapter TP_BeautifulSoup4.py
                # ou créer une fonction dédiée pour scraper *tous* les champs d'un seul article.
                # Pour l'instant, on utilise la fonction existante.
                article_data = scraper.scrape_article_details(article_url, headers)

                if not article_data or (article_data.get('summary') is None and article_data.get('author') is None):
                     st.error("Impossible de scraper les détails de cet article. Vérifiez l'URL ou la structure de la page.")
                else:
                    st.success("Scraping terminé !")

                    # Afficher les informations récupérées
                    st.subheader(f"Détails pour : {article_url}") # On n'a pas le titre ici, sauf si on modifie la fonction

                    if article_data.get("author"):
                        st.write(f"👤 **Auteur:** {article_data['author']}")
                    # On n'a pas la date ou la catégorie avec la fonction actuelle
                    # if article_data.get("date_iso"): st.write(f"📅 **Date:** {article['date_iso']}")
                    # if article_data.get("subcategory"): st.write(f"🏷️ **Catégorie:** {article['subcategory']}")

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
                        for img_data in content_images:
                            st.image(img_data.get("url"), caption=img_data.get("caption_or_alt", ""), use_column_width=True)
                    else:
                        st.write("Aucune image trouvée dans le contenu.")

                    # Optionnel : Bouton pour sauvegarder dans MongoDB
                    # Nécessiterait d'importer mongo_connect et d'ajouter la logique d'insertion ici
                    # if st.button("Sauvegarder cet article dans MongoDB"):
                    #     collection = db_connector.connect_to_mongo()
                    #     if collection is not None:
                    #         try:
                    #             # Il faudrait récupérer TOUTES les données (titre, thumb, etc.) pour que ce soit utile
                    #             # insert_result = collection.insert_one(article_data_complet)
                    #             # st.success(f"Article sauvegardé avec l'ID: {insert_result.inserted_id}")
                    #             st.warning("Fonctionnalité de sauvegarde non implémentée avec les données actuelles.")
                    #         except Exception as e:
                    #             st.error(f"Erreur lors de la sauvegarde : {e}")
                    #     else:
                    #         st.error("Connexion à MongoDB échouée, impossible de sauvegarder.")


            except requests.exceptions.RequestException as e:
                st.error(f"Erreur de requête lors du scraping : {e}")
            except Exception as e:
                st.error(f"Erreur inattendue lors du scraping : {e}")

elif scrape_button and not article_url:
    st.warning("Veuillez entrer une URL.")
