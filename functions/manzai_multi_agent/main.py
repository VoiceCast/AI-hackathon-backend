import random
import functions_framework
import firebase_admin
from firebase_admin import credentials, firestore
from flask import jsonify
from google.cloud.dialogflowcx_v3beta1 import AgentsClient
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
import time
import os
import json


# 🔥 Firebase 初期化
firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS")
if not firebase_admin._apps:  # すでに初期化されていないか確認
    cred = credentials.Certificate(firebase_cred_path)
    firebase_admin.initialize_app(cred)

# Firestore クライアント
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
ALLOWED_ORIGIN = "http://localhost:3000"

def get_random_comedians_data():
    # "Scripts" コレクションからデータを取得
    scripts_ref = db.collection("Comedians")
    docs = list(scripts_ref.stream())
    random_docs = random.sample(docs, 2) if len(docs) >= 2 else docs
    scripts_data = [doc.to_dict() for doc in random_docs]
    print(scripts_data)  # 確認用
    return scripts_data

def create_theme():
    prompt = """
    #指令
    漫才のテーマを5つ考えて下さい。
    考えた5つのテーマをJSON形式で出力して下さい。
    テーマはお笑いの要素を含みつつ独自性のあるものを考えて下さい。

    #形式
    {
        "themes": [
            {
                "theme": "~~~"
                "description":"~~~"
            },
            {
                "theme": "~~~"
                "description":"~~~"
            },
            {
                "theme": "~~~"
                "description":"~~~"
            },
            {
                "theme": "~~~"
                "description":"~~~"
            },
            {
                "theme": "~~~"
                "description":"~~~"
            }
        ]
    }
    """
    response = send_theme_prompt(prompt)

    theme_text = response.candidates[0].content.parts[0].text
    theme_data = json.loads(theme_text)
    theme_list = [item["theme"] for item in theme_data["themes"]]

    return theme_list

def send_theme_prompt(prompt):
    """Gemini API にメッセージを送信し、ボケやツッコミを生成"""
    vertexai.init(
        project="768904645084",
        location="us-central1",
        api_endpoint="us-central1-aiplatform.googleapis.com"
    )

    model = GenerativeModel("gemini-1.5-pro")

    chat = model.start_chat(response_validation=False)  # 変更点

    try:
        result = chat.send_message(
            [prompt],
            generation_config={
                "max_output_tokens": 500,
                "temperature": 1,
                "top_p": 0.9,
            },
            safety_settings=[
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH  # 厳しすぎるフィルタを緩和
                ),
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                ),
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                ),
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                ),
            ]
        )
        return result
    except Exception as e:
        print(f"エラー発生: {e}")
        return ""

def send_message(prompt):
    """Gemini API にメッセージを送信し、ボケやツッコミを生成"""
    vertexai.init(
        project="768904645084",
        location="us-central1",
        api_endpoint="us-central1-aiplatform.googleapis.com"
    )

    model = GenerativeModel(
        "projects/768904645084/locations/us-central1/endpoints/2971453263808823296",
    )

    chat = model.start_chat(response_validation=False)  # 変更点

    try:
        result = chat.send_message(
            [prompt],
            generation_config={
                "max_output_tokens": 30,  # 短文にする
                "temperature": 0.7,  # 一貫性を保つ
                "top_p": 0.9,
            },
            safety_settings=[
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH  # 厳しすぎるフィルタを緩和
                ),
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                ),
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                ),
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                ),
            ]
        )
        return result
    except Exception as e:
        print(f"エラー発生: {e}")
        return ""


def assign_roles(comedians):
    """ボケとツッコミの役割を芸人の情報から決定"""
    boke = None
    tsukkomi = None

    if len(comedians) == 2:
        # `skills['role']` からボケとツッコミを決める
        for comedian in comedians:
            role = comedian.get('skills', {}).get('role', '')

            if 'ボケ' in role and boke is None:
                boke = comedian
            elif 'ツッコミ' in role and tsukkomi is None:
                tsukkomi = comedian

        # 万が一両方ボケ or 両方ツッコミなら、強制的に振り分け
        if not boke:
            boke = comedians[0]
        if not tsukkomi:
            tsukkomi = comedians[1]

    return boke, tsukkomi


def boke_agent(theme, context, geinin_info):
    """ボケエージェントが文脈と芸人情報を踏まえてボケを生成"""
    boke_prompt = f"""

    ## お題
    {theme}

    ## 芸人情報
    {geinin_info}

    ## 会話の流れ
    {context}

    あなたは漫才コンビのボケ担当です。
    以下のルールに必ず従って発言を行ってください：

    ・contextの一番最後の文章がツッコミです。そのフリ（ツッコミ）を受けてユーモアのあるボケを短く生成してください。
    ・長い説明は禁止。発言は長くとも2文まででまとめ、短くインパクトのある表現を心がけること。
    ・芸人情報と会話の流れを参考に回答を生成してください。
    ・生成したボケの文章だけを出力してください。
    """
    return send_message(boke_prompt)


def tsukkomi_agent(theme, context, geinin_info):
    """ツッコミエージェントが文脈と芸人情報を踏まえてツッコミを生成"""
    tsukkomi_prompt = f"""
    ## お題
    {theme}

    ## 芸人情報
    {geinin_info}

    ## 会話の流れ
    {context}

    あなたは漫才コンビのツッコミ担当です。
    以下のルールに従って発言を行ってください：

    ・会話の流れを踏まえて面白くツッコミを行い、その後に次のボケがしやすいフリを発言してください。
    ・ツッコミとフリはそれぞれ1文ずつで、短く簡潔にまとめてください。
    ・芸人情報と会話の流れを参考にしてください。
    ・生成したツッコミの文章以外を出力するのは禁止です。
    """
    return send_message(tsukkomi_prompt)


def first_tsukkomi_agent(theme, geinin_info):
    """ツッコミエージェントが文脈と芸人情報を踏まえてツッコミを生成"""
    tsukkomi_prompt = f"""
    ## お題
    {theme}

    ## 芸人情報
    {geinin_info}

    あなたは漫才コンビのツッコミ担当です。
    以下のルールに従って発言を行ってください：

    ・テーマに沿って次のボケがしやすいフリを発言してください。
    ・フリは1文で、短く簡潔にまとめてください。
    ・芸人情報と会話の流れを参考にしてください。
    ・生成したフリ以外の文章以外を出力するのは禁止です。
    """
    return send_message(tsukkomi_prompt)

def extract_text_from_response(response):
    """Gemini API のレスポンスからツッコミのテキストを抽出"""
    try:
        candidates = response.candidates
        if candidates:
            content = candidates[0].content
            if content:
                parts = content.parts
                if parts:
                    return parts[0].text
    except Exception as e:
        print(f"エラー発生: {e}")
    return ""

# 🎭 Cloud Function のエントリーポイント
@functions_framework.http
def manzai_agents(request):
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight success"})
        response.headers.add("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        response.headers.add("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Max-Age", "3600")  # キャッシュを 1 時間（3600 秒）保持
        return response, 204  # 204 No Content を返す

    """HTTP トリガーのエントリーポイント関数"""
    request_data = request.get_json(silent=True)
    print(request_data)

    comedians = get_random_comedians_data()
    boke_info, tsukkomi_info = assign_roles(comedians)
    boke_voice_characteristics = boke_info.voice_characteristics
    tsukkomi_voice_characteristics = tsukkomi_info.voice_characteristics
    context = "タイムトラベル失敗というテーマで漫才をしてください。"
    themes = create_theme()
    response_list = []
    for theme in themes:
        if boke_info and tsukkomi_info:
            tsukkomi = first_tsukkomi_agent(theme, tsukkomi_info)
            tsukkomi_text = extract_text_from_response(tsukkomi)
            print("ツッコミ:", tsukkomi_text)
            context += f"\n1. ツッコミ: {tsukkomi_text}"

            for i in range(5):
                time.sleep(8)  # API 負荷を減らすために8秒待つ

                boke = boke_agent(theme, context, boke_info)
                boke_text = extract_text_from_response(boke)
                print(f"ボケ: {boke_text}\n")
                context += f"\n{i}. ボケ:{boke_text}"

                tsukkomi = tsukkomi_agent(theme, context, tsukkomi_info)
                tsukkomi_text = extract_text_from_response(tsukkomi)
                print(f"ツッコミ: {tsukkomi_text}\n")

                context += f"\n{i}. ツッコミ: {tsukkomi_text}"

            context += "ツッコミ:　もうええわ。ありがとうございました。"
            print("ツッコミ:　もうええわ。ありがとうございました。")
            response_list.append(
                {
                    "script": context,
                    "theme": theme,
                    "tsukkomi_voice": tsukkomi_voice_characteristics,
                    "boke_voice": boke_voice_characteristics
                }
            )

    response = jsonify({"scripts": response_list,})
    response.headers.add("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
    response.headers.add("Vary", "Origin")
    # 📌 レスポンスを返す
    return response
