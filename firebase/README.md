# Firestore データ構造

このドキュメントは、Firebase Firestore を利用してお笑い芸人、スキル、スクリプト、評価などの情報を管理するためのデータ構造について説明します。

---

## コレクション概要

Firestore はドキュメントベースの NoSQL 構造を持ちます。それぞれのコレクションにはドキュメントが含まれ、一部のドキュメントはサブコレクションやネストされたデータを持つ場合があります。

### 主なコレクション

- **Comedians** (芸人情報)
- **Units** (ユニット情報)
- **Scripts** (スクリプト情報)
- **Judges** (審査員情報)
- **Evaluations** (評価情報)

---

## コレクション詳細

### 1. `Comedians`

お笑い芸人の基本情報とスキルを管理します。

#### ドキュメントフィールド:

- `id` (string): 芸人のユニーク ID。
- `name` (string): 芸人の名前。
- `agency` (string): 所属事務所やグループ。
- `gender` (string): 性別。
- `birthdate` (string): 生年月日。
- `skills` (map): 芸人のスキル情報。
  - `role` (string): 役割（例: パフォーマー、作家）。
  - `voice_characteristics` (string): 声の特徴（例: 深い声、高音）。
  - `writing_skill` (number): 作文スキル（1〜5）。
  - `specialty_topics` (array of strings): 得意なトピック（例: サタイア、即興）。

---

### 3. `Scripts`

芸人によって作成されたスクリプト情報を管理します。

#### ドキュメントフィールド:

- `id` (string): スクリプトのユニーク ID。
- `comedian_ids` (array of strings): このスクリプトに関与した芸人の ID リスト。
- `content` (string): スクリプトの内容。

---

### 4. `Judges`

審査員の情報を管理します。

#### ドキュメントフィールド:

- `id` (string): 審査員のユニーク ID。
- `comedian_id` (string): 審査員が芸人である場合、その芸人 ID。
- `criteria`(string): 審査基準

---

### 5. `Evaluations`

スクリプトに対する評価やフィードバック情報を管理します。

#### ドキュメントフィールド:

- `id` (string): 評価のユニーク ID。
- `judge_id` (string): 評価を行った審査員の ID。
- `script_id` (string): 評価対象のスクリプト ID。
- `total_score` (number): 審査員による総合得点。
- `feedback` (string): 審査員からのフィードバック。
- `details` (array of maps): 評価の詳細（スコアとコメント）。
  - `score` (number): 特定の評価項目のスコア。
  - `comment` (string): 評価項目に関するコメント。

---

## 関係性

- **Comedians & Scripts**: スクリプトは `comedian_ids` を通じて芸人を参照します。
- **Judges & Comedians**: 審査員は `comedian_id` を通じて芸人に関連付けられる場合があります。
- **Evaluations & Judges/Scripts**: 評価は `judge_id` と `script_id` を通じて審査員とスクリプトを参照します。

---

## ドキュメント例

### Comedians の例

```json
{
  "id": "comedianId1",
  "name": "ジョン・ドウ",
  "agency": "お笑い事務所",
  "gender": "male",
  "birthdate": "1990-01-01",
  "skills": {
    "role": "performer",
    "voice_characteristics": "深い声",
    "writing_skill": 5,
    "specialty_topics": ["サタイア", "即興"]
  }
}
```

### Judgesの例
```json
{
  "comedian_id": comedian_id,
  "criteria": "制限時間に厳しい"
}

### Evaluations の例

```json
{
  "id": "evaluationId1",
  "judge_id": "judgeId1",
  "script_id": "scriptId1",
  "total_score": 85,
  "feedback": "素晴らしいパフォーマンス！",
  "details": [
    {
      "score": 20,
      "comment": "演技が素晴らしい"
    },
    {
      "score": 25,
      "comment": "独創的な脚本"
    }
  ]
}
```
