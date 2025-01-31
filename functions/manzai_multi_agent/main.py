import uuid

import functions_framework
import firebase_admin
from firebase_admin import credentials, firestore
from flask import jsonify
from google.cloud import dialogflowcx_v3beta1
from google.cloud.dialogflowcx_v3beta1 import AgentsClient


# 🔥 Firebase 初期化
cred = credentials.Certificate("path/to/firebase_credentials.json")  # Firebase 認証キー
firebase_admin.initialize_app(cred)
db = firestore.client()

# 🎭 Vertex AI クライアント
vertex_client = AgentsClient()
PROJECT_ID = "ai-agent-hackathon-447707"
LOCATION = "asia-northeast1"
BOKE_AGENT_ID = "7f52fb64-6967-435f-b19d-85104576551a"
TSUKKOMI_AGENT_ID = "29af0432-abd8-40ed-b788-27e4bc17c13d"
JUDGE_AGENT_ID = "2aee97f2-0d98-40b1-ac23-8e446b1633db"
SESSION_ID = "10b063a6-fe87-40c1-a44e-a53d29baabf6"
ENVIRONMENT_ID = "-"  # デフォルト環境を使用


# 🎤 Firebase から芸人データを取得
def get_comedian_data(comedian_id):
    doc_ref = db.collection("comedians").document(comedian_id)
    doc = doc_ref.get()
    return doc.to_dict() if doc.exists else None


# 🎭 Vertex AI エージェントとの会話
def send_message(agent_id, message):
    client_options = {"api_endpoint": "asia-northeast1-dialogflow.googleapis.com"}
    client = dialogflowcx_v3beta1.SessionsClient(client_options=client_options)
    SESSION_ID = str(uuid.uuid4())
    session_path = f"projects/{PROJECT_ID}/locations/{LOCATION}/agents/{agent_id}/environments/{ENVIRONMENT_ID}/sessions/{SESSION_ID}"
    request = dialogflowcx_v3beta1.DetectIntentRequest(
        session=session_path,
        query_input={
            "text": {"text": message},
            "language_code": "ja"
        }
    )
    response = client.detect_intent(request=request)
    return response.query_result.response_messages[0].text.text[0]

def boke_agent(tsukkomi_message):
    # 📌 ボケエージェントの発言
    boke_data = get_comedian_data("takahira_kuruma")
    boke_prompt = f"""
        あなたは {boke_data['name']} です。
        スタイル: {boke_data['style']}
        口癖: {boke_data['catchphrase']}

        以下のツッコミに対してボケ返してください:
        {tsukkomi_message}
        """
    boke_message = send_message(BOKE_AGENT_ID, boke_prompt)
    return boke_message

def tsukkomi_agent(boke_message):
    # 📌 ツッコミエージェントの発言
    tsukkomi_data = get_comedian_data("matsui_kemuri")
    tsukkomi_prompt = f"""
        あなたは {tsukkomi_data['name']} です。
        スタイル: {tsukkomi_data['style']}
        口癖: {tsukkomi_data['catchphrase']}

        以下のボケに対してツッコミを入れてください:
        {boke_message}
        """
    tsukkomi_message = send_message("tsukkomi-agent", tsukkomi_prompt)
    return tsukkomi_message

# 🎭 Cloud Function のエントリーポイント
@functions_framework.http
def manzai_agents():
    """HTTP トリガーのエントリーポイント関数"""

    manzai = ""
    boke_message = boke_agent("")
    manzai += f"{boke_message}\n"
    tsukkomi_message = tsukkomi_agent(boke_message)
    manzai += f"{tsukkomi_message}\n"

    #TODO: 何ターンか会話する, 会話の流れを汲めるようにする
    #for i in range(30):
        #boke_message = boke_agent("")
        #tsukkomi_message = tsukkomi_agent(boke_message)


    # 📌 審査員エージェントの評価
    judge_prompt = f"""
    以下の漫才のやり取りを採点してください。
    - ボケ: {boke_message}
    - ツッコミ: {tsukkomi_message}

    評価基準：
    - ボケの独創性
    - ツッコミの的確さ
    - 会話のテンポ

    採点結果は以下のフォーマットでお願いします：
    ボケ: XX点 / ツッコミ: XX点 / 合計: XX点
    """
    judge_message = send_message("judge-agent", judge_prompt)

    # 📌 レスポンスを返す
    return jsonify({
        "ボケ": boke_message,
        "ツッコミ": tsukkomi_message,
        "審査員": judge_message
    })
