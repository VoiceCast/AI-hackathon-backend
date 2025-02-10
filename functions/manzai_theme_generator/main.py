import functions_framework
from flask import jsonify, Response
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
import json

PROJECT_ID = "ai-agent-hackathon-447707"
ALLOWED_ORIGIN = "http://localhost:3000"

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

    return theme_data

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

@functions_framework.http
def manzai_theme_generator(request):
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

    themes = create_theme()

    response_data = {"themes": themes}
    json_response = json.dumps(response_data, ensure_ascii=False)  # Unicodeエスケープを防ぐ
    response = Response(json_response, content_type="application/json; charset=utf-8")
    response.headers.add("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
    response.headers.add("Vary", "Origin")
    # 📌 レスポンスを返す
    return response