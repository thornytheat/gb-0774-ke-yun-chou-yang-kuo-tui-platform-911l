import pytest

from app.modules.ledger.identity import canonical, sha
from app.pipeline import run
from app.source import sources
from app.specs import SPECS, RuleSet

V2 = 'survey-2099.9'  # 测试专用口径：尾差并列补足顺序相反


def enable_v2(monkeypatch):
    monkeypatch.setitem(SPECS, V2, RuleSet(tie_break=('other','transfer','direct')))
    monkeypatch.setenv('SURVEY_SPEC', V2)


def test_new_caliber_changes_result(monkeypatch, tables):
    before = sha(canonical(run(tables)))
    enable_v2(monkeypatch)
    assert sha(canonical(run(tables))) != before  # 城北三类并列，换序后补 1 的类别不同


def test_late_data_keeps_batch_caliber(client, monkeypatch):
    first = client.post('/api/runs', json={'sample':'dirty'}).json
    assert first['manifest']['version'] == 'survey-2026.1'
    enable_v2(monkeypatch)
    again = client.post('/api/runs', json={'sample':'dirty'})
    assert again.status_code == 200 and again.json['reused']
    assert again.json['id'] == first['id']
    assert again.json['manifest']['version'] == 'survey-2026.1'
    assert len(client.get('/api/runs').json['runs']) == 1  # 不新增第二份留档


def test_rerun_reproduces_original_under_old_caliber(client, monkeypatch, tables):
    first = client.post('/api/runs', json={'sample':'dirty'}).json
    enable_v2(monkeypatch)
    assert sha(canonical(run(tables))) != first['manifest']['result_sha256']  # 按当前口径已算不出原结果
    replay = client.post(f"/api/runs/{first['id']}/rerun")
    assert replay.status_code == 200
    assert replay.json['manifest']['result_sha256'] == first['manifest']['result_sha256']
    assert replay.json['manifest']['version'] == 'survey-2026.1'
    assert len(client.get('/api/runs').json['runs']) == 1


def test_new_batch_uses_current_caliber(client, monkeypatch):
    enable_v2(monkeypatch)
    out = client.post('/api/runs', json={'sample':'clean'}).json
    assert out['manifest']['version'] == V2


def test_mixed_calibers_cannot_share_one_release(client, monkeypatch):
    old = client.post('/api/runs', json={'sample':'dirty'}).json['id']
    enable_v2(monkeypatch)
    new = client.post('/api/runs', json={'sample':'clean'}).json['id']
    mixed = client.post('/api/releases', json={'runs':[old,new]})
    assert (mixed.status_code, mixed.json['code']) == (409,'MIXED_SPECS')


def test_same_caliber_batches_share_one_release(client, tables):
    first = client.post('/api/runs', json={'sample':'dirty'}).json['id']
    variant = {**tables, 'returns': tables['returns'] + '\n'}
    second = client.post('/api/runs', json={'tables':variant}).json['id']
    assert second != first
    combined = client.post('/api/releases', json={'runs':[first,second,second]})
    assert combined.status_code == 200
    assert combined.json['version'] == 'survey-2026.1' and len(combined.json['batches']) == 2
    repeat = client.post('/api/releases', json={'runs':[first,second]})
    assert repeat.json['seal'] == combined.json['seal']  # 同组合重复签发仍是同一签


def test_unregistered_caliber_rejected(client, monkeypatch):
    monkeypatch.setenv('SURVEY_SPEC', 'survey-1999.9')
    answer = client.post('/api/runs', json={'sample':'dirty'})
    assert (answer.status_code, answer.json['code']) == (422,'NO_SPEC')


def test_unregistered_caliber_cannot_replay(client, monkeypatch):
    enable_v2(monkeypatch)
    made = client.post('/api/runs', json={'sample':'dirty'}).json
    assert made['manifest']['version'] == V2
    monkeypatch.delitem(SPECS, V2)  # 口径登记只增不改，被移除的口径不得复算
    gone = client.post(f"/api/runs/{made['id']}/rerun")
    assert (gone.status_code, gone.json['code']) == (422,'NO_SPEC')
