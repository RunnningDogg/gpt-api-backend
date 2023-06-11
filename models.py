from dbs import db


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


class Chat(db.Model):
    """
    针对的是问答场景
    type 0 问题  1 回答
    is_delete 0 未删除 1 逻辑删除
    Args:
        db (_type_): _description_

    Returns:
        _type_: _description_
    """
    __tablename__ = 'chat_history'

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer)
    type = db.Column(db.Integer)
    content = db.Column(db.String(512))
    create_time = db.Column(
        db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    update_time = db.Column(db.TIMESTAMP)
    is_delete = db.Column(db.Integer)

    def __init__(self, userid, type, content):
        self.userid = userid
        self.type = type
        self.content = content
        self.is_delete = 0

    def __repr__(self):
        return '<Chat: %d %d %s>' % (self.id, self.userid, self.content)

    def serialize(self):
        return {
            'userid': self.userid,
            'type': self.type,
            'content': self.content,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }


class UserFile(db.Model):
    """
    上传记录的orm
    id: 文件id
    file_type
    is_delete 0 未删除 1 逻辑删除
    """
    __tablename__ = 'user_file'

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.Integer, nullable=False)
    file_name = db.Column(db.String(100), nullable=False)
    file_md5 = db.Column(db.String(32), nullable=False)
    create_time = db.Column(
        db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    is_delete = db.Column(db.Integer)

    def __init__(self, userid, file_type, file_name, file_md5):
        self.userid = userid
        self.file_type = file_type
        self.file_name = file_name
        self.is_delete = 0
        self.file_md5 = file_md5

    def __repr__(self):
        return '<Chat: %d %d %s>' % (self.id, self.userid, self.content)

    def serialize(self):
        return {
            'fileid': self.id,
            'userid': self.userid,
            'file_type': self.file_type,
            'file_name': self.file_name,
            'create_time': self.create_time.strftime('%Y-%m-%d'),
            'is_delete': self.is_delete
        }


class ChatFile(db.Model):
    """
    针对的是PDF问答场景
    type 0 问题  1 回答
    is_delete 0 未删除 1 逻辑删除
    Args:
        db (_type_): _description_

    Returns:
        _type_: _description_
    """
    __tablename__ = 'chat_file_history'

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer)
    type = db.Column(db.Integer)
    fileid = db.Column(db.Integer)
    content = db.Column(db.String(1024))
    create_time = db.Column(
        db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    update_time = db.Column(db.TIMESTAMP)
    is_delete = db.Column(db.Integer)

    def __init__(self, userid, fileid, type, content):
        self.userid = userid
        self.type = type
        self.fileid = fileid
        self.content = content
        self.is_delete = 0

    def __repr__(self):
        return '<Chat: %d %d %s>' % (self.id, self.userid, self.content)

    def serialize(self):
        return {
            'userid': self.userid,
            'type': self.type,
            'fileid': self.fileid,
            'content': self.content,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }
