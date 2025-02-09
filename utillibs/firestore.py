import firebase_admin
from firebase_admin import credentials, firestore
import os

# `firestore.py` のあるディレクトリを基準に `serviceAccountKey.json` を取得
json_path = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")

# 絶対パスを指定
cred = credentials.Certificate(json_path)
app = firebase_admin.initialize_app(cred)
db = firestore.client()
