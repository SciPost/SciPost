__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import pyotp

from time import time

from .models import TOTPDevice


class TOTPVerification:

    def __init__(self, user):
        """
        Initiate for a certain user instance.
        """
        self._user = user

        # Next token must be generated at a higher counter value.
        self.number_of_digits = 6
        self.token_validity_period = 30
        self.tolerance = 2  # Gives a 2 minute window to use a code.

    def verify_token(self, token, tolerance=0):
        try:
            # Convert the input token to integer
            token = int(token)
        except ValueError:
            # return False, if token could not be converted to an integer
            return False
        else:
            if not hasattr(self._user, 'devices'):
                # For example non-authenticated users...
                return False

            for device in self._user.devices.all():
                time_int = int(time())
                totp = pyotp.TOTP(
                    device.token, interval=self.token_validity_period, digits=self.number_of_digits)

                # 1. Check if the current counter is higher than the value of last verified counter
                # 2. Check if entered token is correct
                valid_token = totp.verify(token, for_time=time_int, valid_window=self.tolerance)
                if not valid_token:
                    # Token not valid
                    continue
                elif device.last_verified_counter <= 0 or time_int > device.last_verified_counter:
                    # If the condition is true, set the last verified counter value
                    # to current counter value, and return True
                    TOTPDevice.objects.filter(id=device.id).update(last_verified_counter=time_int)
                    return True
        return False
