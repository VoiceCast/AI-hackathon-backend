import time
import requests
import json

def get_info_by_perplexity(prompt, retries=3, wait_time=5):
    url_api = 'https://api.perplexity.ai/chat/completions'
    payload = {
        'model': 'sonar',
        'messages': [
            {'role': 'system', 'content': 'Be precise and concise'},
            {'role': 'user', 'content': prompt}
        ],
    }
    headers = {
        'Authorization': 'Bearer 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',
        'Content-Type': 'application/json',
    }

    for attempt in range(retries):
        try:
            response_api = requests.post(url_api, headers=headers, json=payload)
            print(f"Attempt {attempt + 1}: Status Code {response_api.status_code}")

            if response_api.status_code == 200:
                data = json.loads(response_api.text)
                return data['choices'][0]['message']['content']
            else:
                print(f"Error: {response_api.text}")

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")

        print(f"Retrying in {wait_time} seconds...")
        time.sleep(wait_time)

    raise Exception("Perplexity API request failed after multiple attempts.")
