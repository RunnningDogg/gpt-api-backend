# import sseclient
# import requests
# from typing import List
# import re
from functools import wraps
from datetime import datetime
from flask import Flask, request, Response, jsonify
from flask import session
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv
from mypdf import search, gen_prompt, createPDFIndexFromMemory
from flask_mail import Mail, Message
import openai
from sqlalchemy import asc
from utils import calculate_md5

# 导入SQLAlchemy 注意这里把实体类放在别的地方了
from dbs import db
from models import User, Chat, UserFile, ChatFile

# 加载 .env 文件
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openaiUrl = os.getenv("OPEN_AI_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print("load api key")
app = Flask(__name__)

# 跨域请求
CORS(app)  # 全局配置CORS

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('MYSQL_URL')
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
# 是否显示底层执行的SQL语句
app.config['SQLALCHEMY_ECHO'] = True

# 配置邮箱
mail = Mail()
app.config['MAIL_SERVER'] = 'smtp.163.com'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USERNAME'] = '15889666941@163.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PWD')
mail.init_app(app)


# db = SQLAlchemy(app)
db.init_app(app)


def requires_admin(func):
    """
        接口做鉴权
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # 获取用户信息或权限验证逻辑，假设使用 token 验证
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


def requires_login(func):
    """
        接口做鉴权
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # 获取用户信息或权限验证逻辑，假设使用 token 验证
        if 'userid' not in session:
            return jsonify({'message': '该接口需要登录'}), 401
        # 如果权限验证通过，则执行被装饰的函数
        return func(*args, **kwargs)

    return decorated_function


@app.route('/api/users/add', methods=['POST'])
@requires_admin
def create_user():
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


@app.route('/api/users/get', methods=['POST'])
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


@app.route('/api/users/update', methods=['POST'])
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
        session['username'] = users[0].name
        session['userid'] = users[0].id
        # print('登录: ', session['username'], session['userid'])
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
            return jsonify({'success': True}), 200
        else:
            error = 'Invalid username or password'
    return jsonify({'error': error}), 400


@app.route('/api/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
        session.pop('userid', None)
        return {'data': "logout successfully!"}
    else:
        return {'data': "you have already logged out"}


@app.route("/api/status")
def home():
    """判断是否登录"""
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

# 发送邮件
# 1.发送文本


@app.route('/api/mail/subscribe', methods=['post'])
def email_send_charactor():
    """
    subject 为邮件标题
    recipients 为接收邮件账号
    body 为邮箱内容
    :return:
    """

    data = request.get_json()
    email_interest = data.get('email')
    body_message = f'ChatRepos客户营销 : 邮件地址是{email_interest}的用户希望咨询该产品, 请尽快联系谢谢!'
    message = Message(subject='【ChatRepos客户营销】',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=['caijy18@tsinghua.org.cn'],
                      body=body_message)
    try:
        mail.send(message)
        return {
            "data": "'邮件发送成功，请注意查看!'",
            "code": 0
        }, 200

    except Exception as e:
        print(e)
        return {
            "data": '邮件发送失败',
            "code": 0
        }, 400


@app.route('/api/chat/history', methods=['GET'])
@requires_login
def get_chat_history():
    chats = Chat.query.filter(
        Chat.userid == session['userid'], Chat.is_delete == 0)\
        .order_by(asc(Chat.update_time))
    # 将查询结果转换为 JSON 格式
    result = [chat.serialize() for chat in chats]
    return jsonify(result)


def stream_output(input_text, userid):
    # 插入上下文
    app.app_context().push()
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'user', 'content': f"{input_text}"}
        ],
        temperature=0,
        stream=True  # this time, we set stream=True
    )
    question = Chat(
        userid=userid, type=0, content=input_text)
    db.session.add(question)
    answer = ''
    for line in response:
        if 'content' in line['choices'][0]['delta']:
            # print(line['choices'][0]['delta']['content'])
            text = line['choices'][0]['delta']['content']
            answer += text
            yield ('data: {}\n\n'.format(json.dumps(text)))
        elif 'finish_reason' in line['choices'][0] and len(line['choices'][0]['delta']) == 0:
            # 回答完毕,把回答落库
            response = Chat(
                userid=userid, type=1, content=answer)
            db.session.add(response)
            db.session.commit()


@app.route('/api/chat/stream', methods=['POST'])
def completion_api():
    # a ChatCompletion request
    req_data = request.get_json()
    input_text = req_data["messages"]
    return Response(stream_output(input_text, session['userid']), mimetype='text/event-stream')


@app.route('/api/files/list', methods=['GET'])
@requires_login
def get_file_list():
    userid = session["userid"]
    files = UserFile.query.filter(
        UserFile.userid == userid, UserFile.is_delete == 0).all()
    # 将查询结果转换为 JSON 格式
    result = [file.serialize() for file in files]
    return jsonify(result)


@app.route('/api/files/upload', methods=['POST'])
@requires_login
def upload():
    file = request.files['file']
    # 处理上传的文件
    username = session["username"]
    userid = session["userid"]
    file_md5 = calculate_md5(file)  # 计算文件md5

    # 判断是否上传过,如果上传过则不处理
    user_file = UserFile.query.filter(UserFile.userid == userid,
                                      UserFile.file_md5 == file_md5,
                                      UserFile.is_delete == 0).first()

    if not user_file:
        # 已经上传过
        newUserFile = UserFile(userid=userid, file_type=0,
                               file_name=file.filename,
                               file_md5=file_md5)

        # createPDFIndex(username=username, filename=file.filename)
        try:
            createPDFIndexFromMemory(
                username=username, filename=file.filename, file=file)
        except Exception as e:
            print(e)
            return {
                'status': 'fail',
                "code": 0
            }, 400
        db.session.add(newUserFile)
        db.session.commit()
        # 传字典就自动转化成json
        return {
            'name': f'{file.filename}',
            'fileid': newUserFile.id,
            'status': 'success'
        }, 201
    else:
        user_files = UserFile.query.filter(UserFile.userid == userid,
                                           UserFile.file_md5 == file_md5,
                                           UserFile.is_delete == 0).all()
        if len(user_files) > 1:
            return {
                'name': f'{file.filename}',
                'fileid': user_file.id,
                'status': 'fail',
                'desc': '上传文件存在多个重复值,请联系管理员操作'
            }, 400
        return {
            'name': f'{file.filename}',
            'fileid': user_file.id,
            'status': 'success'
        }, 201

    # 保存文件到磁盘
    # save_path = '/Users/liangjiongxin/chatgpt/langchain/web/files/'   # 文件保存路径
    # if not os.path.exists(save_path):  # 如果路径不存在则创建
    #     os.makedirs(save_path)

    # if not (os.path.exists(os.path.join(save_path, file.filename))):
    #     file.save(os.path.join(save_path, file.filename))
    #     createPDFIndex(username=username, filename=file.filename)


@app.route('/api/pdf/ask', methods=['POST'])
def askpdf():
    data = request.get_json()
    query = data.get('query')
    filename = data.get('filename')
    fileid = data.get('fileid')

    username = session["username"]
    userid = session["userid"]
    docs = search(query, filename, username)
    prompt = gen_prompt(docs, query)
    sources = sorted(set([doc.metadata['page_number'] for doc in docs]))

    # 根据用户传过来的fileid，获取对应的pdf文件
    # user_file = UserFile.query.filter(UserFile.userid == userid,
    #                                   UserFile.id == fileid).first()

    # 落库问题
    userMessage = ChatFile(userid=userid, fileid=fileid,
                           type=0, content=query)
    db.session.add(userMessage)
    db.session.commit()

    def gen_answer(docs, query):
        # 插入上下文
        app.app_context().push()
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                  messages=[
                                                      {"role": "system",
                                                          "content": "You're an assistant."},
                                                      {"role": "user",
                                                          "content": f"{prompt}"},
                                                  ], stream=True, max_tokens=500, temperature=0)
        answer = ''
        for line in completion:
            if 'content' in line['choices'][0]['delta']:
                text = line['choices'][0]['delta']['content']
                answer += text
                yield ('data: {}\n\n'.format(json.dumps(text)))

        answer += "数据来源: "
        yield "data: {}\n\n".format(json.dumps("数据来源: "))
        for page in sources:
            page_data = "第{}页 ".format(page)
            answer += page_data
            yield ('data: {} \n\n'.format(json.dumps(page_data)))

        # 落库
        aiMessage = ChatFile(userid=userid, fileid=fileid,
                             type=1, content=answer)
        db.session.add(aiMessage)
        db.session.commit()

    # res_headers = {
    #     'Content-Type': 'text/event-stream',
    #     'Cache-Control': 'no-cache',
    #     'Connection': 'keep-alive'
    # }
    return Response(gen_answer(docs, query),   mimetype='text/event-stream')


@app.route('/api/pdf/history', methods=['POST'])
@requires_login
def get_chat_file_history():
    data = request.get_json()
    fileid = data.get('fileid')
    chats = ChatFile.query.filter(
        ChatFile.userid == session['userid'], ChatFile.fileid == fileid)\
        .order_by(asc(ChatFile.update_time))
    # 将查询结果转换为 JSON 格式
    result = [chat.serialize() for chat in chats]
    return jsonify(result)


@app.route('/api/hello', methods=['GET'])
def test_connection():
    return jsonify({"data": "hello world"}), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=6000)


# 之前的流式实现接口
