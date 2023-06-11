import hashlib


def calculate_md5(file):
    """计算文件的md5值"""
    md5_hash = hashlib.md5()
    while chunk := file.read(8192):
        md5_hash.update(chunk)
    return md5_hash.hexdigest()
