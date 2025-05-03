import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import os
import tempfile

# Create a temporary file for Firebase credentials
firebase_credentials = os.environ['FIREBASE_CREDENTIALS']

# Write the credentials to a temporary file
with tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', encoding='utf-8') as temp_file:
    temp_file.write(firebase_credentials)
    temp_file_path = temp_file.name

# Initialize Firebase using the temporary credentials file
cred = credentials.Certificate(temp_file_path)
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# Load CSV data
df = pd.read_csv('sc_bills_parsed_session_126.csv')

# Iterate through each row and upload the data to Firebase
for _, row in df.iterrows():
    # Set the document ID to bill_number (this will ensure each bill has a unique document)
    bill_ref = db.collection(u'bills').document(str(row['bill_number']))  # Convert bill_number to string

    # Set the fields for the document
    bill_ref.set({
        'bill_number': row['bill_number'],
        'session': row['session'],
        'format': row['format'],
        'text': row['text'],
        'bill_url': row['bill_url'],
        'fiscal_impact': row['fiscal_impact'],
        'current_status': row['current_status'],
        'bill_name': row['bill_name'],
        'bill_summary': row['bill_summary']
    })

print("Data has been successfully uploaded to Firebase.")
