import json
from typing import List, Optional, Dict, Any
from src.services.database.repositories.base import BaseRepository
from src.services.database.models import UserSettings


class UserSettingsRepository(BaseRepository):
    async def create_user_settings(
            self,
            user_id: int,
            skills: Optional[List[Dict[str, Any]]] = None,
            grade: Optional[str] = None,
            job_type: Optional[str] = None,
            location: Optional[str] = None
    ) -> UserSettings:
        """Create user settings in database"""
        query_name = "create_user_settings"
        query = self._get_query(entity="user_settings", query_name=query_name)

        skills_json = json.dumps(skills if skills else [])

        try:
            row = await self._pool.fetchrow(
                query, user_id, skills_json, grade, job_type, location
            )

            self._logger.log_db_info(
                f"Create new user settings: user_id={user_id}, "
                f"skills={skills_json}, grade={grade}, job_type={job_type}, "
                f"location={location}"
            )

            return UserSettings.model_validate(dict(row))
        except Exception as e:
            self._logger.log_db_error(query_name=query_name, err=e)
            raise

    async def get_user_settings(self, user_id: int) -> Optional[UserSettings]:
        """Returns user settings object or None if it doesn't exist in database"""
        query_name = "get_user_settings"
        query = self._get_query(entity="user_settings", query_name=query_name)

        try:
            row = await self._pool.fetchrow(query, user_id)
        except Exception as e:
            self._logger.log_db_error(query_name=query_name, err=e)
            raise

        return UserSettings.model_validate(dict(row)) if row else None

    async def update_user_settings(
            self,
            user_id: int,
            skills: Optional[List[Dict[str, Any]]] = None,
            grade: Optional[str] = None,
            job_type: Optional[str] = None,
            location: Optional[str] = None
    ) -> None:
        """Update user settings"""
        query_name = "update_user_settings"
        query = self._get_query(entity="user_settings", query_name=query_name)

        skills_json = json.dumps(skills) if skills is not None else json.dumps([])

        try:
            await self._pool.execute(
                query, user_id, skills_json,
                grade, job_type, location
            )
            self._logger.log_db_info(
                f"Update user with id={user_id}: skills={skills}, grade={grade}, "
                f"job_type={job_type}, location={location}"
            )
        except Exception as e:
            self._logger.log_db_error(query_name=query_name, err=e)
            raise

    async def delete_user_settings(self, user_id: int) -> None:
        """Delete user settings in database"""
        query_name = "delete_user_settings"
        query = self._get_query(entity="user_settings", query_name=query_name)

        try:
            await self._pool.execute(query, user_id)
            self._logger.log_db_info(f"Delete user settings with id={user_id}")
        except Exception as e:
            self._logger.log_db_error(query_name=query_name, err=e)
            raise
