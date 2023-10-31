import firebase_admin
from firebase_admin import credentials, storage



# Initialize the Firebase Admin 
cred = credentials.Certificate("")
firebase_admin.initialize_app(cred, {""})

#firebase_admin.initialize_app(cred, {"storageBucket": "gs://your-project-id.appspot.com"}, name='unique-app-name')


# Specify the path to your local files (JSON and JPG)
local_files = {
    "json_file": "settings.json",
    "jpg_file": "captured_image_1.jpg",
}

# Initialize the Firebase Storage client
bucket = storage.bucket()

# Specify the destination paths in Firebase Storage
destination_paths = {
    "json_file": "appropriate-json file",
    "jpg_file": "appropriate-img file",
}

# Upload the files to Firebase Storage
for file_type, local_path in local_files.items():
    blob = bucket.blob(destination_paths[file_type])
    blob.upload_from_filename(local_path)
    print(f"File {local_path} uploaded to Firebase Storage at {destination_paths[file_type]}")
