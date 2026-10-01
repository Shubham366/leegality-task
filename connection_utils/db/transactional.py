from contextvars import ContextVar
from functools import wraps

from connection_utils.db.session import session

_atomic_scope: ContextVar[bool] = ContextVar("atomic_scope", default=False)


def in_atomic_scope() -> bool:
    return _atomic_scope.get()


class Transactional:
    def __call__(self, func):
        @wraps(func)
        async def _transactional(*args, **kwargs):
            if in_atomic_scope():
                return await func(*args, **kwargs)
            try:
                result = await func(*args, **kwargs)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

            return result

        return _transactional
