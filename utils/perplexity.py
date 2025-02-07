import requests
import json

def get_info_by_perplexity(prompt):
    url_api = 'https://api.perplexity.ai/chat/completions'
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

    response_api = requests.post(
        url_api, headers=headers, json=payload)
    data = json.loads(response_api.text)
    return data['choices'][0]['message']['content']
