from firestore import db

# Firestoreからデータを取得
comedians_ref = db.collection('Comedians').stream()

# nameごとにIDを管理
name_dict = {}

for doc in comedians_ref:
    data = doc.to_dict()
    name = data.get("name")

    if name:
        if name in name_dict:
            # すでに同じnameがある場合、古いデータを削除
            print(f"重複データ削除: {name} (ID: {doc.id})")
            db.collection('Comedians').document(doc.id).delete()
        else:
            # 初回のみ保持
            name_dict[name] = doc.id

print("重複データの削除が完了しました。")
