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
                try:
                    async with self.semaphore:
                        return await func(*args, **kwargs)
                except HTTPException as e:
                    raise e
                except Exception as e:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
            return wrapper
        return decorator


rate_limiter = RateLimiter(max_concurrent=10)  # 默认限流器
