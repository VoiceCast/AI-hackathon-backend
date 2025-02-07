from utils.firestore import db
from utils.perplexity import get_info_by_perplexity

# 芸人情報を取得
comedians = db.collection("comedians").stream()

for comedian in comedians:
    prompt = f"""
        以下の芸人が芸人のショーレースで審査員を務めたかどうか調査してください。
        ##対象芸人
        {comedian.name}

        ##出力形式
        以下の基準に従って、Boolean値のみを出力してください。
        - 審査員を務めた場合: True
        - 審査員を務めていない場合: False
    """

    response = get_info_by_perplexity(prompt)

    # 審査員は評価基準を調査しJudgesに追加
    if response == 'True':
        prompt = f"""
            {comedian.name}の漫才ショーレース審査員時の評価基準について教えてください。
          語尾は〜する傾向、で締めてください。

          ##例
          - 博多大吉：ネタのテンポや時間配分を厳密にチェックする傾向
          - 若林正恭：独創性や新しい切り口を高く評価する傾向
        """
        criteria = get_info_by_perplexity(prompt)

        db.collection('Judges').add(
            {
                'comedian_id': comedian.id,
                'criteria': criteria
            }
        )
