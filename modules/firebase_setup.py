import firebase_admin
from firebase_admin import credentials, firestore

# Load Firebase credentials (replace with your actual JSON file)
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# Test connection
doc_ref = db.collection("test").document("sample_doc")
doc_ref.set({"message": "Hello, Firebase!"})

print("Firestore is connected successfully!")
