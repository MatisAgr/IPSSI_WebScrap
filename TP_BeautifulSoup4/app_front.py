import streamlit as st
import subprocess # pour exécuter un script Python
import sys
import os # pour aller à un fichier 

st.set_page_config(
    layout="wide",
    page_title="BDM Scraper & Explorer",
    page_icon="📰"
)

st.sidebar.success("Sélectionnez une page ci-dessus.")

st.write("# Bienvenue sur l'outil BDM Scraper ! 🤖")
st.divider()

col1, col2, col3 = st.columns(3)

# redirection vers ./pages/IHM_mongo.py
with col1:
    with st.container(border=True):
        st.subheader("📊 Explorer les Articles")
        st.write("Recherchez, filtrez et visualisez les articles stockés dans la BDD MongoDB.")
        st.page_link("pages/IHM_mongo.py", label="Accéder à l'Explorateur", icon="🔎", use_container_width=True)


# redirection vers ./pages/Scrap_article.py
with col2:
    with st.container(border=True):
        st.subheader("⚙️ Scraper un Article Spécifique")
        st.write("Scrapez les détails complets d'un seul article en fournissant son URL.")
        st.page_link("pages/Scrap_article.py", label="Scraper un Article", icon="🎯", use_container_width=True)


# redirection vers ./pages/Scrap_category.py
with col3:
    with st.container(border=True):
        st.subheader("🗂️ Scraper par Catégorie")
        st.write("Scrapez tous les articles listés sur une page de catégorie spécifique.")
        st.page_link("pages/Scrap_category.py", label="Scraper une Catégorie", icon="📚", use_container_width=True)


st.divider()

# lancer ./main.py
st.subheader("🚀 Lancer un Scraping Complet")
st.write("Démarrez un nouveau processus de scraping complet pour récupérer les derniers articles de la page d'accueil du Blog du Modérateur et les insérer dans la base de données. La sortie de la console s'affichera ci-dessous.")

console_output_placeholder = st.empty()
console_output_placeholder.code("La sortie du script apparaîtra ici...", language=None)

if st.button("Lancer le Scraping Complet", use_container_width=True, type="primary"):
    console_output = ""
    console_output_placeholder.code("Lancement du scraping...", language=None)
    try:
        # Détermine le chemin vers le script main.py
        script_path = os.path.join(os.path.dirname(__file__), "main.py")
        # Utilise l'interpréteur Python actuel pour exécuter le script
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Redirige stderr vers stdout
            text=True,
            # --- Modification ici ---
            encoding='utf-8',
            errors='replace', # Remplace les caractères invalides par '?'
            # -----------------------
            bufsize=1 # Line-buffered
        )

        # Lit la sortie ligne par ligne et l'affiche en temps réel
        for line in iter(process.stdout.readline, ''):
            console_output += line
            console_output_placeholder.code(console_output, language=None)
            # Optionnel: petit délai pour le rafraîchissement Streamlit
            # time.sleep(0.01)

        process.stdout.close()
        return_code = process.wait()

        if return_code == 0:
            console_output += "\n--- Scraping terminé avec succès ---"
            st.success("Scraping complet terminé avec succès !")
        else:
            console_output += f"\n--- Erreur lors du scraping (code de sortie: {return_code}) ---"
            st.error(f"Le scraping s'est terminé avec une erreur (code: {return_code}). Vérifiez la sortie ci-dessus.")
        console_output_placeholder.code(console_output, language=None)

    except FileNotFoundError:
        error_msg = f"Erreur: Le script '{script_path}' est introuvable."
        console_output_placeholder.code(error_msg, language=None)
        st.error(error_msg)
    except Exception as e:
        error_msg = f"Une erreur inattendue est survenue : {e}"
        # Afficher l'erreur dans la console simulée aussi
        if console_output: # S'il y a déjà eu de la sortie
                console_output += f"\n{error_msg}"
        else: # Si l'erreur survient avant toute sortie
                console_output = error_msg
        console_output_placeholder.code(console_output, language=None)
        st.error(error_msg)
