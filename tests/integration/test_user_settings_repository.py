import pytest

@pytest.mark.asyncio
async def test_create_and_get_user_settings(user_settings_repo):
    test_uid = 145
    test_grade = "Junior"

    # Create user settings in advance
    await user_settings_repo.create_user_settings(
        user_id=test_uid, grade=test_grade
    )

    # Get user settings
    user_settings = await user_settings_repo.get_user_settings(user_id=test_uid)

    assert user_settings.user_id == test_uid
    assert user_settings.grade == test_grade

@pytest.mark.asyncio
async def test_update_user_settings(user_settings_repo):
    test_uid = 145
    test_grade = "Senior"
    test_job_type = "Remote"

    # Create user settings in advance
    await user_settings_repo.create_user_settings(user_id=test_uid)

    # Update user settings
    await user_settings_repo.update_user_settings(
        user_id=test_uid, grade=test_grade, job_type=test_job_type
    )

    # Check if the update was successful
    user_settings = await user_settings_repo.get_user_settings(user_id=test_uid)

    assert user_settings.user_id == test_uid
    assert user_settings.grade == test_grade
    assert user_settings.job_type == test_job_type

@pytest.mark.asyncio
async def test_delete_user_settings(user_settings_repo):
    test_uid = 145

    # Create user settings in advance
    await user_settings_repo.create_user_settings(user_id=test_uid)

    # Delete user settings
    await user_settings_repo.delete_user_settings(user_id=test_uid)

    # Check if the update was successful
    user_settings = await user_settings_repo.get_user_settings(user_id=test_uid)

    assert user_settings is None
