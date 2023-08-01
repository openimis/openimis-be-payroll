from api_fhir_r4.utils import DbManagerUtils
from core.models import User
from core.services import create_or_update_interactive_user, create_or_update_core_user
from location.models import Location
from payroll.models import PaymentPoint
from payroll.services import PaymentPointService


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


class PaymentPointHelper:
    _TEST_DATA_PAYMENT_POINT = {
        "name": "TestPaymentPoint",
        "location": Location.objects.filter(validity_to__isnull=True, type='V').first()
    }

    def get_or_create_payment_point_api(self, **kwargs):
        payment_point = PaymentPoint.objects.filter(name={**self._TEST_DATA_PAYMENT_POINT, **kwargs}["name"]).first()
        if payment_point is None:
            payment_point = self.__create_payment_point(**kwargs)
        return payment_point

    def __create_payment_point(self, **kwargs):
        user = LogInHelper().get_or_create_user_api()
        name = {**self._TEST_DATA_PAYMENT_POINT, **kwargs}["name"],
        location = {**self._TEST_DATA_PAYMENT_POINT, **kwargs}["location"]
        payment_point = PaymentPoint(
            name=name,
            location=location,
            ppm=user
        )
        payment_point.save(username=user.username)
        return payment_point
