__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from typing import Hashable
from django.db.models import Func


class SplitString(Func):
    function = "regexp_split_to_array"
    template = "%(function)s(%(expressions)s, '%(delimiter)s')"
    arg_joiner = ", "


class GetElement(Func):
    template = "(%(expressions)s)[%(index)s]"
    function = ""


##################################################

import time
from contextlib import contextmanager
from django.db import connection


@contextmanager
def postgres_lock(lock_key: Hashable, max_retries: int = 5, retry_delay: float = 2.0):
    """
    Context manager to acquire a PostgreSQL advisory lock and release it after the block.
    Retries acquiring the lock if the first attempt fails.
    :param lock_key: Unique lock key (as a hashable object)
    :param max_retries: Maximum retries for acquiring the lock
    :param retry_delay: Delay between retries in seconds
    """
    # Convert lock_key to a 64-bit integer
    lock_key_int = abs(hash(lock_key)) % (2**63)

    retries = 0
    lock_acquired = False

    while retries < max_retries:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s);", [lock_key_int])
            lock_acquired = cursor.fetchone()[0]

        if lock_acquired:
            break
        else:
            retries += 1
            if retries < max_retries:
                time.sleep(retry_delay)
            else:
                raise RuntimeError(
                    f"Failed to acquire lock for {lock_key} ({lock_key_int}) after {max_retries} retries"
                )

    try:
        # Yield the lock acquisition to the caller, then execute the body of the with statement
        yield lock_key_int
    finally:
        # Release the lock after the critical section is done
        if lock_acquired:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s);", [lock_key_int])
