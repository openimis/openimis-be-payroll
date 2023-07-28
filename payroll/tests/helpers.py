from api_fhir_r4.utils import DbManagerUtils
from core.models import User
from core.services import create_or_update_interactive_user, create_or_update_core_user


class LogInHelper:
    _TEST_DATA_USER = {
        "username": "TestUserTest2",
        "last_name": "TestUserTest2",
        "password": "TestPasswordTest2",
        "other_names": "TestUserTest2",
        "user_types": "INTERACTIVE",
        "language": "en",
        "roles": [1, 3, 5, 7, 9],
    }

    def get_or_create_user_api(self, **kwargs):
        user = User.objects.filter(username={**self._TEST_DATA_USER, **kwargs}["username"]).first()
        if user is None:
            user = self.__create_user_interactive_core(**kwargs)
        return user

    def __create_user_interactive_core(self, **kwargs):
        i_user, i_user_created = create_or_update_interactive_user(
            user_id=None, data={**self._TEST_DATA_USER, **kwargs}, audit_user_id=999, connected=False)
        create_or_update_core_user(
            user_uuid=None, username={**self._TEST_DATA_USER, **kwargs}["username"], i_user=i_user)
        return DbManagerUtils.get_object_or_none(User, username={**self._TEST_DATA_USER, **kwargs}["username"])
