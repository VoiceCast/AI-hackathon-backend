import functions_framework

# Cloud Functionのエントリーポイント
@functions_framework.http
def hello_world(request):
    """HTTPトリガーのエントリーポイント関数"""
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'name' in request_json:
        name = request_json['name']
    elif request_args and 'name' in request_args:
        name = request_args['name']
    else:
        name = 'World'

    return f"Hello, {name}!"
