from typing import Any, Dict, List
from pydantic import Field

from ..base import APIModel

__all__ = [
    "GenshinAccount",
    "RecordCardData",
    "RecordCardSetting",
    "RecordCard",
]


class GenshinAccount(APIModel):
    """A genshin account"""

    uid: int = Field(galias="game_uid")
    level: int
    nickname: str
    server: str = Field(galias="region")
    server_name: str = Field(galias="region_name")


class RecordCardData(APIModel):
    """A data entry of a record card"""

    name: str
    value: str


class RecordCardSetting(APIModel):
    """A privacy setting of a record card"""

    id: int = Field(galias="switch_id")
    description: str = Field(galias="switch_name")
    public: bool = Field(galias="is_public")

    @property
    def name(self) -> str:
        return {
            1: "Battle Chronicle",
            2: "Character Details",
            3: "Real-Time Notes",
        }.get(self.id, "")


class RecordCard(GenshinAccount):
    """A genshin record card containing very basic user info"""

    uid: int = Field(galias="game_role_id")

    data: List[RecordCardData]
    privacy_settings: List[RecordCardSetting] = Field(galias="data_switches")

    # unknown meaning
    background_image: str
    has_uid: bool = Field(galias="has_role")
    public: bool = Field(galias="is_public")

    @property
    def days_active(self) -> int:
        return int(self.data[0].value)

    @property
    def characters(self) -> int:
        return int(self.data[1].value)

    @property
    def achievements(self) -> int:
        return int(self.data[2].value)

    @property
    def spiral_abyss(self) -> str:
        return self.data[3].value

    @property
    def html_url(self) -> str:
        """The html url"""
        return f"https://webstatic-sea.hoyolab.com/app/community-game-records-sea/index.html?uid={self.uid}#/ys"

    def as_dict(self) -> Dict[str, Any]:
        """Helper function which turns fields into properly named ones"""
        return {d.name: (int(d.value) if d.value.isdigit() else d.value) for d in self.data}
