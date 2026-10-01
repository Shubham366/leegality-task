from connection_utils.redis.connection import redis_client


class RedisBackend:
    def __init__(self, client=None):
        self.client = client or redis_client


class CustomKeyMaker:
    def make(self, function, prefix: str) -> str:
        return f"{prefix}:{function.__module__}.{function.__name__}"


class CacheManager:
    def __init__(self):
        self.backend = None
        self.key_maker = None

    def init(self, backend: RedisBackend, key_maker: CustomKeyMaker) -> None:
        self.backend = backend
        self.key_maker = key_maker


Cache = CacheManager()
