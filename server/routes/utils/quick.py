from datetime import datetime, timedelta, UTC, time as dttime

def to_user_now(timezone_offset: int) -> datetime:
  """
  Calculate the user's current time,
  based on their timezone_offset
  which is brought by the client using `new Date().getTimezoneOffset()` (js)
  """

  dt = datetime.now(UTC) + timedelta(hours=timezone_offset / -60 or 0)
  return dt

def to_local_time(day_mins: int, timezone_offset: int) -> dttime:
  """
  Calculate the local time based on the user's timezone_offset

  Accepts minutes since the start of the day (00:00)
  """

  # timezone_offset is offset from UTC
  # we need to know what hour:min of the user is in UTC, and then convert it to local our time

  # TODO
  hours, mins = divmod(day_mins, 60)
  return dttime(hours, mins)