from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

#CONFIG
MONGO_URI = "mongodb://localhost:27017/" 
DATABASE_NAME = "ipssi_webscraping"
COLLECTION_NAME = "data"

# connection mangodb
def connect_to_mongo():
    try:
        # création client mongo
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) # Timeout after 5 seconds
        client.admin.command('ismaster')
        print("MongoDB connection successful!")

        # accès à la database
        db = client[DATABASE_NAME]

        # accès à la table
        collection = db[COLLECTION_NAME]
        print(f"Successfully accessed database '{DATABASE_NAME}' and collection '{COLLECTION_NAME}'.")

        return collection

    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# insert la data dans la bdd
def insert_sample_data(collection, sample_data):
    if collection is None:
        print("Cannot insert data, collection object is None.")
        return None
    try:
        insert_result = collection.insert_one(sample_data)
        print(f"Successfully inserted document with id: {insert_result.inserted_id}")
        return insert_result.inserted_id
    except Exception as e:
        print(f"Error inserting data: {e}")
        return None

# récup la data de la bdd
def find_all_data(collection):
    if collection is None:
        print("Cannot find data, collection object is None.")
        return
    try:
        print("\n--- Finding all documents ---")
        documents = collection.find()
        count = 0
        for doc in documents:
            print(doc)
            count += 1
        if count == 0:
            print("No documents found in the collection.")
        print("---------------------------\n")
    except Exception as e:
        print(f"Error finding data: {e}")


if __name__ == "__main__":
    data_collection = connect_to_mongo()

    if data_collection is not None:
        find_all_data(data_collection)
