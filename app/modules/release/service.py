from app.errors import SurveyProblem
from app.modules.ledger.identity import canonical, sha

from .audit import authenticate


def release(manifest,tables,results):
    authenticate(manifest,tables,results)
    excluded = {
        'intake':results['returns']['rejected'], 'alignment':results['frame']['invalid'],
        'nonresponse':results['frame']['nonresponse'],
    }
    payload = dict(manifest=manifest,originals=tables,results=results,excluded=excluded)
    return dict(**payload,seal=sha(canonical(payload)),verified=True)


def release_all(archives):
    if not archives:
        raise SurveyProblem('EMPTY_RELEASE','没有可签发的批次')
    batches = [release(manifest,tables,results) for manifest,tables,results in archives]
    found = {batch['manifest']['version'] for batch in batches}
    if len(found) != 1:
        raise SurveyProblem('MIXED_SPECS','不同口径的批次不能拼成一次签发',409)
    payload = dict(version=found.pop(),batches=batches)
    return dict(**payload,seal=sha(canonical(payload)),verified=True)
