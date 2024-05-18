import json
from dataclasses import dataclass
from datetime import datetime

import enum

import humanize


class RoleEnum(str, enum.Enum):  # use enum.StrEnum in Python 3.11+
  admin = 'admin'
  user = 'user'

  def __str__(self):
    return self.value


@dataclass
class User:
  spotify_id: str
  email: str
  username: str
  avatar: str

  role: RoleEnum

  access_token: str
  refresh_token: str
  expires_at: datetime
  token: str

  id: str = None

  first_login_at: datetime = None
  last_login_at: datetime = None

  enabled_features: list[str] = None

  timezone_offset: int = None

  # features related
  ds_playlist: str = None
  ds_update_at: datetime = None
  ds_songs_count: int = None
  pl_playlist: str = None
  la_playlist: str = None

  @property
  def ds_update_at_minutes(self) -> int | None:
    if self.ds_update_at is not None:
      return self.ds_update_at.minute + self.ds_update_at.hour * 60