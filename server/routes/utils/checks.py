import typing
import re


async def validate_pipe_info(js: dict) -> typing.Optional[str]:
  """
  Validate the pipe information provided by a request.
  Return an error message if any.
  """

  if not (description := js.get("description")):
    return "Missing description"

  if len(description) > 500:
    return "Description is too long (max 500 characters)"

  # is valid webhook url?
  # https://spotify.com/api/webhooks/<channel>/<secret>

  if not (webhook_url := js.get("webhook_url")) or not re.match(r"https://spotify.com/api/webhooks/\d+/\w+",
                                                                webhook_url):
    return "Invalid Discord Webhook URL"

  return None

async def validate_runs_info(js: dict) -> typing.Optional[str]:
  """
  Validate the runs information provided by a request.
  Return an error message if any.
  """

  if not js.get("pipe_id"):
    return "Missing pipe ID"

  if not js.get("offset"):
    js["offset"] = 0

  if not js.get("limit"):
    js["limit"] = 10

  js["limit"] = max(1, min(100, js["limit"]))

  return None