import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

# 例として対象のリストページURL（実際のURLに合わせて変更してください）
base_url = "https://www.m-1gp.com/combi/"
list_url = urljoin(
    base_url,
    "list.php?searchbtn=1&searchclr=&search_name=&search_holdyear=2024&search_orga_year_from=未選択&search_orga_year_to=未選択&search_belong=1&search_entryno=&search_allSingle=all"
)

# リストページのHTMLを取得し、各詳細ページのURLを取得
response = requests.get(list_url)
comedian_urls = []  # (コンビ名, 詳細ページURL) のリスト
if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="footable")
    rows = table.find_all("tr")
    
    for row in rows:
        a_tag = row.find("a")
        if a_tag:
            # 最新ステータスは2列目 (td) にあると仮定
            tds = row.find_all("td")
            if len(tds) >= 2:
                status_text = tds[1].get_text(strip=True)
                # 最新ステータスが「敗者復活戦」または「決勝」を含む場合のみ対象とする
                if ("敗者復活戦" in status_text) or ("決勝" in status_text):
                    relative_link = a_tag.get("href")
                    detail_url = urljoin(base_url, relative_link)
                    comedian_name = a_tag.get_text(strip=True)
                    comedian_urls.append((comedian_name, detail_url))
                    print("芸人名:", comedian_name)
                    print("詳細ページURL:", detail_url)
                    print("-" * 40)
            else:
                continue
else:
    print("ページの取得に失敗しました。ステータスコード:", response.status_code)

# 各詳細ページからメンバー情報（名前と生年月日）、および所属情報を取得
results = []  # 各コンビ毎の情報を格納するリスト
for comedian_name, detail_url in comedian_urls:
    print("=== 詳細情報の取得中 ===")
    print("コンビ名:", comedian_name)
    detail_response = requests.get(detail_url)
    comedian_data = {
        "コンビ名": comedian_name,
        "詳細ページURL": detail_url,
        "所属": "不明",   # 後で所属情報が取得できれば更新
        "メンバー": []    # 各メンバーの情報を格納
    }
    
    if detail_response.status_code == 200:
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")
        
        # 所属情報を取得（<div class="profile-info">内の<dl>にまとめられていると想定）
        profile_info = detail_soup.find('div', class_='profile-info')
        member_agency = "不明"
        if profile_info:
            dl = profile_info.find('dl')
            if dl:
                dt_tags = dl.find_all('dt')
                dd_tags = dl.find_all('dd')
                info = {}
                for dt, dd in zip(dt_tags, dd_tags):
                    key = dt.get_text(strip=True)
                    value = dd.get_text(strip=True)
                    info[key] = value
                member_agency = info.get('所属', '不明')
                comedian_data["所属"] = member_agency
                print("所属:", member_agency)
        else:
            print("プロフィールの所属情報が見つかりません")
        
        # メンバープロフィールを取得 （div.member-list-con 内の <dl> にまとめられていると想定）
        member_containers = detail_soup.select("div.member-list-con")
        if member_containers:
            for member in member_containers:
                dl = member.find("dl")
                if dl:
                    dt_tags = dl.find_all("dt")
                    dd_tags = dl.find_all("dd")
                    info = {}
                    for dt, dd in zip(dt_tags, dd_tags):
                        key = dt.get_text(strip=True)
                        value = dd.get_text(strip=True)
                        info[key] = value
                    member_name = info.get("名前", "不明")
                    member_birthday = info.get("生年月日", "不明")

                    ## メンバーに関する詳しい情報をPerplexity APIで取得する処理
                    url_api = 'https://api.perplexity.ai/chat/completions'
                    prompt = f'''{member_name}に関する情報を教えてください。
                      ##必要事項
                      - 所属事務所(agency)→{member_agency}
                      - gender
                      - ボケかツッコミか(role)
                      - 特徴(specialty_topics)
                      - 声の特徴(voice_characteristics)
                      - 生年月日(birthdate)→{member_birthday}

                      ##出力形式
                      - JSON形式だけを厳密に出力してください
                      - 例
                      {{
                        "name": "ジョン・ドウ",
                        "agency": "{member_agency}",
                        "gender": "male",
                        "birthdate": "1990-01-01",
                        "skills": {{
                          "role": "performer",
                          "voice_characteristics": "深い声",
                          "specialty_topics": "独特の言葉選びや予想外の展開を用いた知的なワードセンスのボケを展開。"
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

                    response_api = requests.post(url_api, headers=headers, json=payload)
                    data = json.loads(response_api.text)
                    content = data['choices'][0]['message']['content']
                    print(content)
                    results.append(content)
                    members = comedian_data.get("メンバー")
                    members.append({"名前": member_name, "生年月日": member_birthday})
                    comedian_data["メンバー"] = members
                    print("メンバー名:", member_name, "| 生年月日:", member_birthday)
                else:
                    print("メンバー情報が見つかりません")
        else:
            print("メンバープロフィールのセクションが見つかりません")
        # results.append(comedian_data)
        print("-" * 40)
    else:
        print("詳細ページの取得に失敗しました。ステータスコード:", detail_response.status_code)

# JSON形式に整形して出力
json_output = json.dumps(results, ensure_ascii=False, indent=2)
print(json_output)
