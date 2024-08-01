import asyncio
from functools import wraps
from fastapi import HTTPException, status


class RateLimiter:
    def __init__(self, max_concurrent: int):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    def limit(self):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.semaphore.locked():
                    async with self.semaphore:
                        try:
                            return await func(*args, **kwargs)
                        except HTTPException as e:
                            raise e
                        except Exception as e:
                            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal "
                                                                                                          "Server "
                                                                                                          "Error")
                else:
                    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="服务器繁忙，请稍后重试")

            return wrapper

        return decorator


rate_limiter = RateLimiter(max_concurrent=10)  # 默认限流器
ws_rate_limiter = RateLimiter(max_concurrent=10)  # WebSocket专用限流器
