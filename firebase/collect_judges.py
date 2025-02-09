import sys
import os

# `utils` の親ディレクトリを `sys.path` に追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utillibs.firestore import db
from utillibs.perplexity import get_info_by_perplexity

# 芸人情報を取得
comedians = db.collection("Comedians").get()

for comedian in comedians:
    id = comedian.id
    data = comedian.to_dict()

    prompt = f"""
        以下の芸人が芸人のショーレースで審査員を務めた経験があるかどうか調査してください。
        ##対象芸人
        {data['name']}

        ##出力形式
        以下の基準に従って、Boolean値のみを出力してください。
        - 審査員を務めた場合: True
        - 審査員を務めていない場合: False
    """

    response = get_info_by_perplexity(prompt)
    print('Boolean: ' + response)

    # 審査員は評価基準を調査しJudgesに追加
    if 'True' in response:
        print('審査基準を取得中')
        prompt = f"""
            {data['name']}の漫才ショーレース審査員時の評価基準について教えてください。
          語尾は〜する傾向、で締めてください。

          ##例
          - 博多大吉：ネタのテンポや時間配分を厳密にチェックする傾向
          - 若林正恭：独創性や新しい切り口を高く評価する傾向
        """
        criteria = get_info_by_perplexity(prompt)

        print('Firestoreに追加中')
        db.collection('Judges').add(
            {
                'comedian_id': id,
                'criteria': criteria
            }
        )
