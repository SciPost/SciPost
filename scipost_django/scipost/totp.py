__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import time
import pyotp

from .models import TOTPDevice


class TOTPVerification:
    number_of_digits = 6
    token_validity_period = 30
    tolerance = 2  # Gives a 2 minute window to use a code.

    def __init__(self, user):
        """
        Initiate for a certain user instance.
        """
        self._user = user

    def verify_code(self, code):
        """
        Verify a time-dependent code for a certain User.
        """
        try:
            # Try to see if input token is convertible to integer.
            # Do not actually make it an integer, because it'll lose the leading 0s.
            assert int(code) > 0
        except (ValueError, AssertionError):
            # return False, if token could not be converted to an integer
            return False
        else:
            if not hasattr(self._user, 'devices'):
                # For example non-authenticated users...
                return False

            for device in self._user.devices.all():
                time_int = int(time.time())
                totp = pyotp.TOTP(
                    device.token, interval=self.token_validity_period, digits=self.number_of_digits)

                # 1. Check if the current counter is higher than the value of last verified counter
                # 2. Check if entered token is correct
                valid_token = totp.verify(code, for_time=time_int, valid_window=self.tolerance)

                if not valid_token:
                    # Token not valid
                    continue
                elif device.last_verified_counter <= 0 or time_int > device.last_verified_counter:
                    # If the condition is true, set the last verified counter value
                    # to current counter value, and return True
                    TOTPDevice.objects.filter(id=device.id).update(last_verified_counter=time_int)
                    return True
        return False

    @classmethod
    def verify_token(cls, secret_key, code):
        """
        Independently verify a secret_key/code combination at current time.
        """
        try:
            # Try to see if input token is convertible to integer.
            # Do not actually make it an integer, because it'll lose the leading 0s.
            assert int(code) > 0
        except (ValueError, AssertionError):
            # return False, if token could not be converted to an integer
            return False
        time_int = int(time.time())
        totp = pyotp.TOTP(secret_key, interval=cls.token_validity_period, digits=cls.number_of_digits)
        return totp.verify(code, for_time=time_int, valid_window=cls.tolerance)
