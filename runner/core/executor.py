def execute(task: dict) -> dict:
    """档位一执行内核。

    M0 只固定这个入口。任务快照进、结果出，路由函数不得内联执行过程。
    M1 在这里接 pytest。换执行档位时只改投递，不改这个函数的签名。
    """
    if not isinstance(task, dict) or "protocol_version" not in task:
        raise ValueError("任务缺少 protocol_version")
    raise NotImplementedError("execute(task) 在 M1 实现")
