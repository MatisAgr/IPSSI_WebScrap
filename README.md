# BDM Scraper & Explorer

Ce projet est un outil de web scraping conçu pour extraire des informations d'articles du site "Blog du Modérateur" (blogdumoderateur.com) et les stocker dans une base de données MongoDB. Il fournit également une interface web simple construite avec Streamlit pour lancer des scrapings et explorer les données collectées.

![image](https://github.com/user-attachments/assets/2e6569bb-b4e9-4792-aad8-0c642034cc35)

## Fonctionnalités

*   **Scraping de Catégories :** Extrait les URL de toutes les catégories d'articles depuis le menu principal.
*   **Scraping d'Articles par Catégorie :** Scrape tous les articles listés sur une page de catégorie spécifique, incluant les détails complets (titre, auteur, date, résumé, image principale, images du contenu, tags).
*   **Scraping d'Article Unique :** Scrape les détails complets d'un article spécifique en fournissant son URL.
*   **Scraping Complet :** Lance un scraping de toutes les catégories trouvées sur la page d'accueil et sauvegarde les articles dans MongoDB, en évitant les doublons basés sur l'URL.
*   **Stockage MongoDB :** Sauvegarde les données scrapées dans une base de données MongoDB.
*   **Interface Web (Streamlit) :**
    *   Permet de lancer un scraping complet directement depuis l'interface.
    *   Permet de scraper une catégorie spécifique via une liste déroulante.
    *   Permet de scraper un article unique via son URL.
    *   Permet de rechercher et filtrer les articles stockés dans MongoDB par titre, auteur, tag/catégorie et date.

## Technologies Utilisées

*   **Python 3.11**
*   **Bibliothèques Python :**
    *   `requests` : Pour effectuer les requêtes HTTP.
    *   `beautifulsoup4` : Pour parser le HTML et extraire les données.
    *   `streamlit` : Pour créer l'interface web interactive.
    *   `pymongo` : Pour interagir avec la base de données MongoDB.
*   **Base de Données :** MongoDB

## Installation

1.  **Cloner le dépôt :**
    ```sh
    git clone https://github.com/MatisAgr/IPSSI_WebScrap.git
    cd IPSSI_WebScrap
    ```
2.  **Installer les dépendances Python :**
    Assurez-vous d'avoir Python et pip installés. Il est recommandé d'utiliser un environnement virtuel.
    ```sh
    python -m venv venv
    ```
    Installez les bibliothèques nécessaires (fichier `requirements.txt` si besoin) :
    ```sh
    pip install requests beautifulsoup4 streamlit pymongo
    ```
    ou
    ```sh
    pip install -r requirements.txt
    ```


3.  **Configurer MongoDB :**
    *   Assurez-vous qu'une instance MongoDB est en cours d'exécution. Par défaut, le script se connecte à `mongodb://localhost:27017/`.
    *   Vous pouvez modifier l'URI de connexion, le nom de la base de données (`ipssi_webscraping`) et le nom de la collection (`data`) dans le fichier `mongo_connect.py` si nécessaire.

## Utilisation

1.  **Lancer l'interface Streamlit :**
    Depuis le répertoire racine du projet (`TP_BeautifulSoup4`), exécutez la commande suivante dans votre terminal :
    ```sh
    streamlit run app_front.py
    ```
    ou
    ```sh
    python -m streamlit run .\app_front.py
    ```
    
    Cela ouvrira l'application dans votre navigateur web. Vous pourrez alors :
    *   Naviguer vers les différentes pages via la barre latérale.
    *   Lancer un scraping complet depuis la page d'accueil.
    *   Scraper des catégories ou des articles spécifiques depuis leurs pages dédiées.
    *   Explorer les données dans la page "Explorer les Articles".

2.  **Lancer un scraping complet via la ligne de commande (alternative) :**
    Vous pouvez également lancer le scraping complet directement en exécutant le script [main.py](http://_vscodecontentref_/0) :
    ```sh
    python main.py
    ```
    La progression et les résultats s'afficheront dans la console.
