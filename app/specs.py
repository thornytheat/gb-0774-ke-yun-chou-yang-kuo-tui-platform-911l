"""口径（规则版本）登记。

每批首次归档时绑定当时启用的口径，此后只认该口径：晚到数据沿用所属批次的
口径，复算按归档口径重算并须复现原结果。登记条目只增不改，保证已签发批次的
口径永远可以复算；新口径上线只需追加条目并切换 SURVEY_SPEC。
"""

import os
from dataclasses import dataclass

from app.errors import SurveyProblem


@dataclass(frozen=True)
class RuleSet:
    """一个口径版本的全部计算参数。"""

    tie_break: tuple = ('direct', 'transfer', 'other')  # 整数尾差并列时的补足顺序


SPECS = {'survey-2026.1': RuleSet()}
DEFAULT_SPEC = 'survey-2026.1'


def rules(name):
    try:
        return SPECS[name]
    except KeyError:
        raise SurveyProblem('NO_SPEC', f'口径 {name} 未登记') from None


def current():
    name = os.getenv('SURVEY_SPEC', DEFAULT_SPEC)
    rules(name)
    return name
