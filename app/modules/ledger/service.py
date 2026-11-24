from datetime import UTC, datetime
from time import perf_counter_ns

from app import specs
from app.errors import SurveyProblem
from app.pipeline import run

from .identity import canonical, identity, sha


def archive(service, tables, previous=None):
    start = perf_counter_ns()
    key, hashes = identity(tables)
    # 每批只认一个口径：已有批次（含晚到、重复提交）沿用归档口径，新批次绑定当前口径
    prior = previous or service.find(key)
    spec = prior['version'] if prior else specs.current()
    results = run(tables, version=spec)
    digest = sha(canonical(results))
    if prior and (prior['id'],prior['result_sha256']) != (key,digest):
        raise SurveyProblem('REPLAY_DIFFERENCE','复算与原归档不一致',409)
    summary=dict(id=key,files=hashes,version=spec,created=datetime.now(UTC).isoformat(timespec='seconds'),
                 result_sha256=digest, elapsed_ms=(perf_counter_ns()-start)//1_000_000)
    fresh = service.add(summary,tables,results)
    manifest,_,_ = service.read(key)
    if manifest['result_sha256'] != digest:
        raise SurveyProblem('REPLAY_DIFFERENCE','同源归档摘要存在冲突',409)
    return dict(id=key,manifest=manifest,reused=not fresh,balance=results['balance'])
