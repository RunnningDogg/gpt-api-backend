# import sseclient
# import json
# import requests
# from langchain.llms import OpenAI
# from typing import List
# import re
# from datetime import datetime
# from flask import jsonify, request
from functools import wraps
from datetime import datetime
from flask import Flask, request, Response, jsonify, session
import os
import json
from dotenv import load_dotenv
# 导入orm
from flask_sqlalchemy import SQLAlchemy
from mypdf import createPDFIndex, search, gen_prompt
import openai


# 加载 .env 文件
load_dotenv()
openaiUrl = os.getenv("OPEN_AI_URL")
apiKey = os.getenv("API_KEY")

app = Flask(__name__)

# 容器化后改成对应的host
connector = 'mysql+mysqlconnector://root:woyaozhuanqian123!@db/gpt'
app.config['SQLALCHEMY_DATABASE_URI'] = connector
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
# 是否显示底层执行的SQL语句
app.config['SQLALCHEMY_ECHO'] = True


db = SQLAlchemy(app)
# print(f'url {openaiUrl} key {apiKey}')


class User(db.Model):
    """
    status枚举值 用户状态 注册 0 正常1 封禁2 删除3
    user_role 0 普通用户, 1 管理员
    is_delete 0 未删除 1 逻辑删除
    Args:
        db (_type_): _description_

    Returns:
        _type_: _description_
    """
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(120))
    email = db.Column(db.String(120))
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    status = db.Column(db.Integer)
    user_role = db.Column(db.Integer)
    is_delete = db.Column(db.Integer)

    def __init__(self, name, password, email):
        self.name = name
        self.password = password
        self.email = email

    def __repr__(self):
        return '<Students: %s %s %s>' % (self.id, self.name, self.stu_number)

# gpt的增删改查


def requires_admin(func):
    """
        接口做鉴权
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # 获取用户信息或权限验证逻辑，假设使用 token 验证
        """装饰器，用于验证用户权限"""
        data = request.get_json()
        id = data.get('admin_id')
        if not id:
            return jsonify({'message': '该接口需要管理员操作 请传入id'}), 401

        # 在这里进行权限验证逻辑，比如判断用户角色是否为管理员
        user = User.query.filter_by(id=id).first()
        if not user or user.user_role != 1:
            return jsonify({'message': 'Unauthorized access.'}), 403

        # 如果权限验证通过，则执行被装饰的函数
        return func(*args, **kwargs)

    return decorated_function


@app.route('/api/users/add', methods=['POST'])
@requires_admin
def create_user():
    """添加用户"""
    """
        add 创建用户
    """
    data = request.get_json()
    name = data.get('name')
    password = data.get('password')
    email = data.get('email')

    if not name or not password:
        return jsonify({'message': 'Name and password are required.'}), 400

    users = User.query.filter(User.name == name).all()

    if (len(users) > 0):
        return jsonify({'message': 'User Name Duplicate'}), 400

    users = User.query.filter(User.email == email).all()

    if (len(users) > 0):
        return jsonify({'message': 'User Email Duplicate'}), 400

    user = User(name=name, password=password, email=email)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User created successfully.'}), 201


@app.route('/api/users/get/', methods=['POST'])
@requires_admin
def get_user():
    """
        get 获取用户信息
    """
    data = request.get_json()
    user_id = data.get('id')
    if user_id:
        user = User.query.get(user_id)

        if not user:
            return jsonify({'message': 'User not found.'}), 404

        user_data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'create_time': user.create_time,
            'update_time': user.update_time,
            'status': user.status,
            'user_role': user.user_role,
            'is_delete': user.is_delete
        }
        return jsonify(user_data), 200
    else:
        users = User.query.all()
        user_list = []
        for user in users:
            user_data = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'create_time': user.create_time,
                'update_time': user.update_time,
                'status': user.status,
                'user_role': user.user_role,
                'is_delete': user.is_delete
            }
            user_list.append(user_data)
        # 使用 jsonify 函数将用户列表转换为 JSON 格式
        response = jsonify(users=user_list)

        # 设置响应头的 Content-Type 为 application/json
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/api/users/update/', methods=['POST'])
@requires_admin
def update_user():
    """
        更新用户信息
    """
    data = request.get_json()
    user_id = data.get('id')
    user = User.query.get(user_id)

    if not user:
        return jsonify({'message': 'User not found.'}), 404

    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({'message': 'Name and email are required.'}), 400

    user.name = name
    user.email = email
    user.update_time = datetime.now()

    db.session.commit()

    return jsonify({'message': 'User updated successfully.'}), 200


@app.route('/api/users/delete/', methods=['POST'])
@requires_admin
def delete_user(user_id):
    data = request.get_json()
    user_id = data.get('id')
    user = User.query.get(user_id)

    if not user:
        return jsonify({'message': 'User not found.'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully.'}), 200


################################

def valid_login(name, password):
    """
    校验登录的逻辑
    Args:
        name (_type_): _description_
        password (_type_): _description_

    Returns:
        _type_: _description_
    """
    users = User.query.filter(
        User.password == password, User.name == name).all()
    if (len(users) > 0):
        return True
    else:
        return False


@app.route('/api/login', methods=['post'])
def login():
    error = None
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('name')
        password = data.get('password')
        if valid_login(username, password):
            session['username'] = username
            return jsonify({'success': True}), 200
        else:
            error = 'Invalid username or password'
    return jsonify({'error': error}), 400


@app.route('/api/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
        return {'data': "logout successfully!"}
    else:
        return {'data': "you have already logged out"}


@app.route("/api/status")
def home():
    if 'username' in session:
        return {
            "data": f'Logged in as {session["username"]}',
            "name": f'{session["username"]}',
            "code": 1
        }
    return {
        "data": "You are not logged in!",
        "code": 0
    }


def stream_output(input_text):

    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'user', 'content': f"{input_text}"}
        ],
        temperature=0,
        stream=True  # this time, we set stream=True
    )
    for line in response:
        if 'content' in line['choices'][0]['delta']:
            # print(line['choices'][0]['delta']['content'])
            yield ('data: {}\n\n'.format(json.dumps(line['choices'][0]['delta']['content'])))


@app.route('/api/stream', methods=['POST'])
def completion_api():
    # a ChatCompletion request
    req_data = request.get_json()
    input_text = req_data["messages"][0]["content"]
    return Response(stream_output(input_text), mimetype='text/event-stream')


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    # 处理上传的文件
    print(file)
    username = session["username"]

    # 保存文件到磁盘
    save_path = '/Users/liangjiongxin/chatgpt/langchain/web/files/'  # 文件保存路径
    if not os.path.exists(save_path):  # 如果路径不存在则创建
        os.makedirs(save_path)

    if not (os.path.exists(os.path.join(save_path, file.filename))):
        file.save(os.path.join(save_path, file.filename))
        createPDFIndex(username=username, filename=file.filename)

    # 传字典就自动转化成json
    return {
        'name': f'{file.filename}',
        'status': 'success'
    }


@app.route('/api/pdf/ask', methods=['POST'])
def askpdf():
    data = request.get_json()
    query = data.get('query')
    filename = data.get('filename')
    username = session["username"]
    docs = search(query, filename, username)
    prompt = gen_prompt(docs, query)
    sources = sorted(set([doc.metadata['page_number'] for doc in docs]))

    def gen_answer(docs, query):
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                  messages=[
                                                      {"role": "system",
                                                          "content": "You're an assistant."},
                                                      {"role": "user",
                                                          "content": f"{prompt}"},
                                                  ], stream=True, max_tokens=500, temperature=0)
        for line in completion:
            if 'content' in line['choices'][0]['delta']:
                yield ('data: {}\n\n'.format(json.dumps(line['choices'][0]['delta']['content'])))
        yield "data: {}\n\n".format(json.dumps("数据来源: "))
        for page in sources:
            page_data = "第{}页 ".format(page)
            yield ('data: {} \n\n'.format(json.dumps(page_data)))
    # res_headers = {
    #     'Content-Type': 'text/event-stream',
    #     'Cache-Control': 'no-cache',
    #     'Connection': 'keep-alive'
    # }
    return Response(gen_answer(docs, query),   mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=6000)


# 之前的流式实现接口
# def stream():
#     req_data = request.get_json()
#     def generate(req_data):
#         reqHeaders = {
#             'Accept': 'text/event-stream',
#             'Authorization': 'Bearer ' + apiKey
#         }
#         reqBody = {
#             "model": "gpt-3.5-turbo",
#             "messages": [{"role": "user", "content": req_data["messages"][0]["content"]}],
#             "temperature": 0,
#             "stream": True
#         }
#         clientRequest = requests.post(
#             openaiUrl, stream=True, headers=reqHeaders, json=reqBody)
#         client = sseclient.SSEClient(clientRequest)
#         for event in client.events():
#             if event.data != '[DONE]':
#                 # print(json.loads(event.data),flush=True)
#                 text = json.loads(event.data)['choices'][0]["delta"]
#                 if len(text) > 0:
#                     if "role" in text:
#                         print('data: {}\n'.format(json.dumps(text["role"])))
#                     else:
#                         print(text["content"], end="", flush=True)
#                         yield ('data: {}\n\n'.format(json.dumps(text["content"])))
#                 # print(json.loads(event.data)['choices'][0]["delta"]["content"],end="" , flush=True)
#                 else:
#                     print('haha...')
#                     # yield 'data: {}\n\n'.format(json.dumps('[DONE]'))
#     print("receive req body {}", req_data)
#     res_headers = {
#         'Content-Type': 'text/event-stream',
#         'Cache-Control': 'no-cache',
#         'Connection': 'keep-alive'
#     }
#     # return Response(generate(req_data), mimetype='text/event-stream')
#     return Response(generate(req_data), headers=res_headers)
