import sys
import os
import json
import uuid

# `utils` の親ディレクトリを `sys.path` に追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utillibs.firestore import db
from utillibs.perplexity import get_info_by_perplexity

# 芸人情報を取得
prompt = f"""
    ## 命令
    M1の歴代審査員について網羅的に調査し、以下の情報を出力してください。

    ##必要情報
    - 名前(name)
    - 審査基準(criteria)
    - 所属事務所(agency)
    - gender
    - ボケかツッコミか(role)
    - 特徴(specialty_topics)
    - 声の特徴(voice_characteristics)
    - 生年月日(birthdate)
    - ネタを書く能力(writing_skill)

    ##出力形式
    - リスト化されたJSON形式だけを厳密に出力してください.そのほかの文章は一切出力してはなりません。
    - ```jsonなども不要。{{}}で囲んでください。```
    - 例
    [
        {{
            "name": "ジョン・ドウ",
            "criteria": "制限時間に厳しい",
            "agency": "吉本興業",
            "gender": "male",
            "birthdate": "1990-01-01",
            "skills": {{
            "role": "performer",
            "voice_characteristics": "深い声",
            "specialty_topics": "独特の言葉選びや予想外の展開を用いた知的なワードセンスのボケを展開。",
            "writing_skill": 5,
            }}
        }},
        {{
            "name": "ジョン・ドウ",
            "criteria": "制限時間に厳しい",
            "agency": "吉本興業",
            "gender": "male",
            "birthdate": "1990-01-01",
            "skills": {{
            "role": "performer",
            "voice_characteristics": "深い声",
            "specialty_topics": "独特の言葉選びや予想外の展開を用いた知的なワードセンスのボケを展開。",
            "writing_skill": 5,
            }}
        }},
    ]
"""

response = get_info_by_perplexity(prompt)

try:
    res = json.loads(response)

    for comedian in res:
        comedian_id = str(uuid.uuid4())

        # Comediansコレクションに追加
        comedian_ref = db.collection("Comedians").document(comedian_id)
        comedian_ref.set({
            "name": comedian["name"],
            "agency": comedian["agency"],
            "gender": comedian["gender"],
            "birthdate": comedian["birthdate"],
            "skills": {
                "role": comedian["skills"]["role"],
                "voice_characteristics": comedian["skills"]["voice_characteristics"],
                "writing_skill": comedian["skills"]["writing_skill"],
                "specialty_topics": comedian["skills"]["specialty_topics"]
            }
        })

        # Judges コレクションに追加（ComediansのIDを参照）
        judge_ref = db.collection("Judges").document()
        judge_ref.set({
            "comedian_id": comedian_id,
            "criteria": comedian["criteria"]
        })
except json.JSONDecodeError as e:
    print('パースに失敗しました', e)
    print('response: ', response)
