"""领域异常。

服务层只抛领域异常，不直接依赖 FastAPI；由 main.py 统一注册处理器转换成 HTTP 响应。
"""


class AppError(Exception):
    """所有业务异常的基类。"""


class NotFoundError(AppError):
    """目标资源不存在。"""

    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    """请求内容不合法（如上传了非图片文件、超出体积上限）。"""

    def __init__(self, message: str = "请求内容不合法") -> None:
        super().__init__(message)
        self.message = message
