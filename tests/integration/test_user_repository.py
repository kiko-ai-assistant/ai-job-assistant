import pytest

@pytest.mark.asyncio
async def test_create_and_get_user_and_exists(user_repo):
    test_uid = 145

    # Create a user in advance
    await user_repo.create_user(
        user_id=test_uid, username="zervany",
        first_name="Vladimir", language="en"
    )

    # Get the user
    user = await user_repo.get_user(user_id=test_uid)

    # Check its existing
    exists = await user_repo.check_user_exists(user_id=test_uid)

    assert user.username == "zervany"
    assert exists

@pytest.mark.asyncio
async def test_update_user_language(user_repo):
    test_uid = 145
    test_language = "ru"

    # Create a user in advance
    await user_repo.create_user(
        user_id=test_uid, username="zervany",
        first_name="Vladimir", language="en"
    )

    # Update the user
    await user_repo.update_user_language(user_id=test_uid, language=test_language)

    # Check if the update was successful
    user = await user_repo.get_user(user_id=test_uid)

    assert user.language == test_language

@pytest.mark.asyncio
async def test_update_user_cv(user_repo):
    test_uid = 145
    test_cv_file_id = "file_id"
    test_cv_path = "path/to/cv"

    # Create a user in advance
    await user_repo.create_user(
        user_id=test_uid, username="zervany",
        first_name="Vladimir", language="en"
    )

    # Update the user
    await user_repo.update_user_cv(
        user_id=test_uid, cv_file_id=test_cv_file_id, cv_path=test_cv_path
    )

    # Check if the update was successful
    user = await user_repo.get_user(user_id=test_uid)

    assert user.cv_file_id == test_cv_file_id
    assert user.cv_path == test_cv_path

@pytest.mark.asyncio
async def test_delete_user(user_repo):
    test_uid = 145

    # Create a user in advance
    await user_repo.create_user(
        user_id=test_uid, username="zervany",
        first_name="Vladimir", language="en"
    )

    # Delete the user
    await user_repo.delete_user(user_id=test_uid)

    # Check if the update was successful
    user = await user_repo.get_user(user_id=test_uid)

    assert user is None

@pytest.mark.asyncio
async def test_get_all_users(user_repo):
    test_pairs = [
        (145, "zervany"),
        (2, "shishi"),
        (1, "kuka")
    ]

    # Create users in advance
    for pair in test_pairs:
        await user_repo.create_user(
            user_id=pair[0], username=pair[1],
            first_name="Vladimir", language="en"
        )

    # Get all users
    users = await user_repo.get_all_users(limit=2, offset=1)

    assert users
    assert len(users) == 2
    assert users[0].username == test_pairs[1][1]
    assert users[1].username == test_pairs[2][1]

