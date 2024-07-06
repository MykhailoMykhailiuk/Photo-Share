import contextlib

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from src.conf.config import config


class DatabaseSessionManager:
    def __init__(self, url: str):
        print(url)
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """The session function is a context manager that provides a transactional scope around a series of operations.
            It will automatically rollback the session if an exception occurs, or commit the session otherwise.

        Yields:
            Generator: A generator object
        """
        if self._session_maker is None:
            raise Exception("Session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except Exception as err:
            print(err)
            raise err
            await session.rollback()
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(config.SQLALCHEMY_DATABASE_URL)


async def get_db():
    async with sessionmanager.session() as session:
        yield session
