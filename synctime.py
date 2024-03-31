import ntptime
import time

try:
    from configs import NTP_SERVER
except ImportError:
    NTP_SERVER = "pool.ntp.org"
try:
    from configs import TZ_OFFSET
except ImportError:
    TZ_OFFSET = 0


def localtime():
    """localtime wrapper to add timezone offset

    Returns
    -------
    tupled time.localtime() with timezone offset added
    """
    return time.localtime(time.time() + TZ_OFFSET * 3600)


def sync_time(max_try=3):
    print(f"Time before sync: {time.localtime()}")
    ntptime.host = NTP_SERVER
    tries = 1
    while tries <= max_try:
        # ntp throws an error if it does not need to sync, so we can ignore the exception
        try:
            ntptime.settime()
        except Exception as e:
            print(f"{e}, try {tries}/{max_try}")
            print(f"Time: {time.localtime()}")
            tries += 1
            time.sleep(0.5)
            continue
    print(f"Time after sync: {time.localtime()} after {tries} tries")
    return time.localtime()
