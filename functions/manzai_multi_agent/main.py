import random
import functions_framework
import firebase_admin
from firebase_admin import credentials, firestore
from flask import jsonify, Response
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
import time
import os
import json
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_vertexai import ChatVertexAI
from typing import Annotated, List, Sequence
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict
import asyncio
from datetime import datetime

# 🔥 Firebase 初期化
firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS")
if not firebase_admin._apps:  # すでに初期化されていないか確認
    cred = credentials.Certificate(firebase_cred_path)
    firebase_admin.initialize_app(cred)

# Firestore クライアント
db = firestore.client()

PROJECT_ID = "ai-agent-hackathon-447707"
ALLOWED_ORIGIN = "http://localhost:3000"

def get_random_comedians_data():
    # "Scripts" コレクションからデータを取得
    scripts_ref = db.collection("Comedians")
    docs = list(scripts_ref.stream())
    random_docs = random.sample(docs, 2) if len(docs) >= 2 else docs
    scripts_data = [doc.to_dict() for doc in random_docs]
    print(scripts_data)  # 確認用
    return scripts_data

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
    try:
        response = send_message(boke_prompt)
        return response
    except Exception as e:
        print(f"error on boke agent: {e}")
        return ""


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
    try:
        response = send_message(tsukkomi_prompt)
        return response
    except Exception as e:
        print(f"error on tsukkomi agent: {e}")
        return ""



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
    try:
        response = send_message(tsukkomi_prompt)
        return response
    except Exception as e:
        print(f"error on tsukkomi agent: {e}")
        return ""

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

def get_random_judge_criteria():
    # "Scripts" コレクションからデータを取得
    scripts_ref = db.collection("Judges")
    docs = list(scripts_ref.stream())
    random_docs = random.sample(docs, 1) if len(docs) >= 2 else docs
    scripts_data = [doc.to_dict() for doc in random_docs]
    return scripts_data[0]["criteria"]

judge_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "あなたは、お笑いコンテストの審査員です。"
                "与えられた漫才スクリプトに対して、評価コメントを作成してください。"
                "漫才のテーマは変えてはいけません。"
                "次の評価基準を踏まえて回答を生成してください。\n\n{criteria}"
                "漫才のスクリプトは次の通りです。"
                "{manzai_script}",
            ),
            MessagesPlaceholder(variable_name="criteria"),
        ]
    )

reflection_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "あなたは漫才師のネタ作成担当です。与えらた評価コメントを踏まえてネタを作成しなおします。"
                "漫才のテーマは変えてはいけません。"
                "元のネタは次の通りです。\n\n{manzai_script}"
                "評価コメントは次の通りです。\n\n{judge_comment}"
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

# Agentに渡す状態を定義
class State(TypedDict):
    messages: Annotated[list, add_messages]
    manzai_script: str
    criteria: str
    judge_comment: str
    iteration: int  # ループ回数を管理


async def judgement(manzai_script):
    criteria = get_random_judge_criteria()
    llm = ChatVertexAI(model_name='gemini-1.5-pro')

    async def generation_node(state: State) -> State:
        return {
            "messages": state["messages"],
            "manzai_script": state["manzai_script"],
            "criteria": state["criteria"],
            "judge_comment": state["judge_comment"],
            "iteration": state["iteration"],
        }

    async def judge_node(state: State) -> State:
        judge_prompt_partial = judge_prompt.partial(judge_data=state["criteria"], manzai_script=state["manzai_script"])
        response = await (judge_prompt_partial | llm).ainvoke(state["messages"])
        return {
            "messages": state["messages"] + [response],
            "manzai_script": state["manzai_script"],
            "criteria": state["criteria"],
            "judge_comment": response.content,
            "iteration": state["iteration"],
        }

    async def reflection_node(state: State) -> State:
        cls_map = {"ai": HumanMessage, "human": AIMessage}
        translated = [state["messages"][0]] + [
            cls_map[msg.type](content=msg.content) for msg in state["messages"][1:]
        ]
        reflect_prompt_partial = reflection_prompt.partial(
            manzai_script=state["manzai_script"], judge_comment=state["judge_comment"]
        )
        response = await (reflect_prompt_partial | llm).ainvoke(state["messages"])
        new_iteration = state["iteration"] + 1
        print(f"Reflection 完了。iteration {state['iteration']} -> {new_iteration}")

        return {
            "messages": state["messages"] + [response],
            "manzai_script": response.content,
            "criteria": state["criteria"],
            "judge_comment": state["judge_comment"],
            "iteration": new_iteration,
        }

    builder = StateGraph(State)
    builder.add_node("generate", generation_node)
    builder.add_node("judge", judge_node)
    builder.add_node("reflect", reflection_node)
    builder.add_edge(START, "generate")
    builder.add_edge("generate", "judge")
    builder.add_edge("judge", "reflect")

    MAX_ITERATIONS = 3

    def should_continue(state: State):
        if state["iteration"] >= MAX_ITERATIONS:
            return END
        return "generate"

    builder.add_conditional_edges("reflect", should_continue)
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    config = {"configurable": {"thread_id": "2"}}

    latest_script = manzai_script  # 初期値を設定
    start_time = datetime.now()  # 実行開始時間を記録
    script_list = []

    async def run_graph():
        nonlocal latest_script
        async for event in graph.astream(
            {
                "messages": [
                    HumanMessage(
                        content="審査員は与えられたmanzai_scriptを審査してコメントしてください。漫才師のネタ作り担当は審査コメントを元に修正してください。"
                    )
                ],
                "manzai_script": manzai_script,
                "criteria": str(criteria),
                "judge_comment": "",
                "iteration": 0,
            },
            config,
        ):
            latest_script = event.get("generate", {}).get("manzai_script", latest_script)
            print(latest_script)
            script_list.append(latest_script)
            if (datetime.now() - start_time).total_seconds() > 90:
                print("⚠ タイムアウト: 90秒経過したため終了します。")
                return latest_script
        return script_list

    try:
        return await asyncio.wait_for(run_graph(), timeout=60)
    except asyncio.TimeoutError:
        print("⚠ asyncio.TimeoutError: 60秒経過したため終了します。")
        return latest_script


# 🎭 Cloud Function のエントリーポイント
@functions_framework.http
def manzai_agents(request):
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight success"})
        response.headers.add("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        response.headers.add("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Max-Age", "3600")  # 1時間キャッシュ
        return response, 204  # 204 No Content

    """HTTP トリガーのエントリーポイント関数"""
    request_data = request.get_json(silent=True)
    print(request_data)

    comedians = get_random_comedians_data()
    boke_info, tsukkomi_info = assign_roles(comedians)
    boke_voice_characteristics = boke_info["skills"]["voice_characteristics"]
    tsukkomi_voice_characteristics = tsukkomi_info["skills"]["voice_characteristics"]
    theme = request_data['theme']
    context = f"{theme}というテーマで漫才をしてください。"

    # 🔹 初期のレスポンスデータ
    response_script = {
        "script": "",
        "theme": theme,
        "tsukkomi_voice": tsukkomi_voice_characteristics,
        "boke_voice": boke_voice_characteristics
    }

    if boke_info and tsukkomi_info:
        try:
            start_time = time.time()  # 処理開始時刻を記録
            TIMEOUT = 180  # タイムアウト時間（秒）

            async def async_main():
                nonlocal context  # スクリプトの更新を可能にする

                tsukkomi = first_tsukkomi_agent(theme, tsukkomi_info)
                tsukkomi_text = extract_text_from_response(tsukkomi)
                print("ツッコミ:", tsukkomi_text)
                context += f"\n1. ツッコミ: {tsukkomi_text}"

                for i in range(5):
                    if time.time() - start_time > TIMEOUT:
                        print("⚠ タイムアウト: 90秒経過したため処理を終了します。")
                        break

                    await asyncio.sleep(8)

                    boke = boke_agent(theme, context, boke_info)
                    boke_text = extract_text_from_response(boke)
                    print(f"ボケ: {boke_text}\n")
                    context += f"\n{i + 2}. ボケ: {boke_text}"

                    tsukkomi = tsukkomi_agent(theme, context, tsukkomi_info)
                    tsukkomi_text = extract_text_from_response(tsukkomi)
                    print(f"ツッコミ: {tsukkomi_text}\n")
                    context += f"\n{i + 2}. ツッコミ: {tsukkomi_text}"

                context += "\nツッコミ: もうええわ。ありがとうございました。"
                print("ツッコミ: もうええわ。ありがとうございました。")

            # 🔹 非同期処理を同期的に実行
            asyncio.run(async_main())

        except Exception as e:
            print(f"エラー発生: {e}")
            response_script["script"] = context  # 🔹 途中までのスクリプトを格納
            response_script["error"] = str(e)  # 🔹 エラーメッセージを追加

    # 🔹 90秒経過時でも `context` を確実にセット
    response_script["script"] = context

    # 🔹 `judgement(context)` が非同期関数なら `asyncio.run()` で実行
    updated_script = asyncio.run(judgement(context))

    response_script["script"] = updated_script
    json_response = json.dumps(response_script, ensure_ascii=False)
    response = Response(json_response, content_type="application/json; charset=utf-8")
    response.headers.add("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
    response.headers.add("Vary", "Origin")

    # 📌 レスポンスを返す
    return response
