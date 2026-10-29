"""平台调用执行内核的唯一入口。路由里禁止写执行过程。"""

from runner.core.executor import execute


def run_task(task: dict) -> dict:
    return execute(task)
