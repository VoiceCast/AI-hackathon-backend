import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from utillibs.firestore import db
from utillibs.perplexity import get_info_by_perplexity

results = []  # 各コンビ毎の情報を格納するリスト
# 例として対象のリストページURL（実際のURLに合わせて変更してください）
# 現状1ページ目と4ページ目は完了
for page in range(2, 478):
    try:
        base_url = "https://www.m-1gp.com/combi/"
        list_url = urljoin(
            base_url,
            f"list.php?searchbtn=1&searchclr=&search_name=&search_holdyear=2024&search_orga_year_from=未選択&search_orga_year_to=未選択&search_belong=1&search_entryno=&search_allSingle=all&page={page}"
        )

        response = requests.get(list_url)
        response.raise_for_status()

        comedian_urls = []
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="footable")
        rows = table.find_all("tr")

        for row in rows:
            a_tag = row.find("a")
            if a_tag:
                tds = row.find_all("td")
                if len(tds) >= 2:
                    status_text = tds[1].get_text(strip=True)
                    if ("敗者復活戦" in status_text) or ("決勝" in status_text):
                        relative_link = a_tag.get("href")
                        detail_url = urljoin(base_url, relative_link)
                        comedian_name = a_tag.get_text(strip=True)
                        comedian_urls.append((comedian_name, detail_url))
                        print("芸人名:", comedian_name)
                        print("詳細ページURL:", detail_url)
                        print("-" * 40)

        for comedian_name, detail_url in comedian_urls:
            print("=== 詳細情報の取得中 ===")
            print("コンビ名:", comedian_name)
            detail_response = requests.get(detail_url)
            detail_response.raise_for_status()

            comedian_data = {
                "コンビ名": comedian_name,
                "詳細ページURL": detail_url,
                "所属": "不明",
                "メンバー": []
            }

            detail_soup = BeautifulSoup(detail_response.text, "html.parser")
            profile_info = detail_soup.find('div', class_='profile-info')
            member_agency = "不明"
            if profile_info:
                dl = profile_info.find('dl')
                if dl:
                    dt_tags = dl.find_all('dt')
                    dd_tags = dl.find_all('dd')
                    info = {dt.get_text(strip=True): dd.get_text(strip=True) for dt, dd in zip(dt_tags, dd_tags)}
                    member_agency = info.get('所属', '不明')
                    comedian_data["所属"] = member_agency
                    print("所属:", member_agency)

            member_containers = detail_soup.select("div.member-list-con")
            if member_containers:
                for member in member_containers:
                    dl = member.find("dl")
                    if dl:
                        dt_tags = dl.find_all("dt")
                        dd_tags = dl.find_all("dd")
                        info = {dt.get_text(strip=True): dd.get_text(strip=True) for dt, dd in zip(dt_tags, dd_tags)}
                        member_name = info.get("名前", "不明")
                        member_birthday = info.get("生年月日", "不明")

                        prompt = f'''{member_name}に関する情報を教えてください。
                        ##必要事項
                        - 所属事務所(agency)→{member_agency}
                        - gender
                        - ボケかツッコミか(role)
                        - 特徴(specialty_topics)
                        - 声の特徴(voice_characteristics)
                        - 生年月日(birthdate)→{member_birthday}
                        - ネタを書く能力(writing_skill)→1~5の5段階評価

                        ##出力形式
                        - JSON形式だけを厳密に出力してください
                        - ```jsonなども不要。{{}}で囲んでください。```
                        - 例
                        {{
                            "name": "ジョン・ドウ",
                            "agency": "{member_agency}",
                            "gender": "male",
                            "birthdate": "1990-01-01",
                            "skills": {{
                            "role": "performer",
                            "voice_characteristics": "深い声",
                            "specialty_topics": "独特の言葉選びや予想外の展開を用いた知的なワードセンスのボケを展開。",
                            "writing_skill": 5,
                            }}
                        }}
                        '''
                        payload = {
                            'model': 'sonar',
                            'messages': [
                                {
                                    'role': 'system',
                                    'content': 'Be precise and concise',
                                },
                                {
                                    'role': 'user',
                                    'content': prompt,
                                }
                            ],
                        }
                        headers = {
                            'Authorization': 'Bearer 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',
                            'Content-Type': 'application/json',
                        }

                        response = get_info_by_perplexity(prompt)
                        print("APIからのレスポンス:", response)

                        try:
                            content_dict = json.loads(response)
                            results.append(content_dict)
                        except json.JSONDecodeError as e:
                            print("JSONのパースに失敗しました:", e)
                            print("受け取った内容:", response)
                            continue
            print("-" * 40)
    except requests.RequestException as e:
        print(f"ページの取得に失敗しました。エラー: {e}")
    except Exception as e:
        print(f"予期しないエラーが発生しました。エラー: {e}")

# JSON形式に整形して出力
json_output = json.dumps(results, ensure_ascii=False, indent=2)
print(json_output)

# Firestoreに保存
for result in results:
    db.collection('Comedians').add(result)
    print("Firestoreにデータを保存しました")
