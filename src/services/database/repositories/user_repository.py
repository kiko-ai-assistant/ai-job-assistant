from typing import List, Optional
from src.services.database.repositories.base import BaseRepository
from src.services.database.models import User

class UserRepository(BaseRepository):
    async def create_user(
            self, user_id: int, username: str,
            first_name: str, language: str
    ) -> None:
        """Create user in database"""
        query_name = "create_user"
        query = self._get_query(entity="users", query_name=query_name)

        try:
            row = await self._pool.fetchrow(
                query, user_id, username, first_name, language
            )
            self._logger.log_db_info(
                f"Create new user: user_id={user_id}, "
                f"username={username}, first_name={first_name}"
            )
        except Exception as e:
            self._logger.log_db_error(query_name=query_name, err=e)
            raise

        return User.model_validate(dict(row)) if row else None

    async def get_user(self, user_id: int) -> Optional[User]:
        """Returns user object or None if it doesn't exist in database"""
        query_name = "get_user"
        query = self._get_query(entity="users", query_name=query_name)

        try:
            row = await self._pool.fetchrow(query, user_id)
        except Exception as e:
            self._logger.log_db_error(query_name=query_name, err=e)
            raise

        return User.model_validate(dict(row)) if row else None

    async def check_user_exists(self, user_id: int) -> bool:
        """Returns True if user with specified id exists in database and False otherwise"""
        query_name = "check_user_exists"
        query = self._get_query(entity="users", query_name=query_name)

        try:
            exists = await self._pool.fetchval(query, user_id)
        except Exception as e:
            self._logger.log_db_error(query_name=query_name, err=e)
            raise

        return exists

    async def update_user_language(self, user_id: int, language: str) -> None:
        """Update user's language"""
        query_name = "update_user_language"
        query = self._get_query(entity="users", query_name=query_name)

        try:
            await self._pool.execute(query, user_id, language)
            self._logger.log_db_info(
                f"Update user with id={user_id}: language={language}"
            )
        except Exception as e:
            self._logger.log_db_error(query_name=query_name, err=e)
            raise

    async def update_user_cv(
            self, user_id: int,
            cv_file_id: Optional[str], cv_path: Optional[str]
    ) -> None:
        """Update user's cv"""
        query_name = "update_user_cv"
        query = self._get_query(entity="users", query_name=query_name)

        try:
            await self._pool.execute(query, user_id, cv_file_id, cv_path)
            self._logger.log_db_info(
                f"Update user with id={user_id}: cv_path={cv_path}"
            )
        except Exception as e:
            self._logger.log_db_error(query_name=query_name, err=e)
            raise

    async def delete_user(self, user_id: int) -> None:
        """Delete record about user in database"""
        query_name = "delete_user"
        query = self._get_query(entity="users", query_name=query_name)

        try:
            await self._pool.execute(query, user_id)
            self._logger.log_db_info(f"Delete user with id={user_id}")
        except Exception as e:
            self._logger.log_db_error(query_name=query_name, err=e)
            raise

    async def get_all_users(self, limit: int, offset: int) -> List[User]:
        """Returns a list of users with pagination and amount limit"""
        query_name = "get_all_users"
        query = self._get_query(entity="users", query_name=query_name)

        try:
            rows = await self._pool.fetch(query, limit, offset)
        except Exception as e:
            self._logger.log_db_error(query_name=query_name, err=e)
            raise

        return [User.model_validate(dict(row)) for row in rows]
