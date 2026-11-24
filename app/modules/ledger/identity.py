import hashlib
import json


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',',':'))


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def identity(inputs):
    # 批次编号只由原件内容决定，不含口径版本：同一批数据永远落在同一批次上
    hashes = {key:sha(text) for key,text in inputs.items()}
    return sha(canonical({'files':hashes})), hashes
