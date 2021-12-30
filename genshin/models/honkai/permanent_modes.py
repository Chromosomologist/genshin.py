import re
from datetime import datetime
from typing import List, Literal, Optional

from genshin import models
from genshin.models.honkai import base
from pydantic import Field, validator

__all__ = [
    "Boss",
    "ELF",
    "OldAbyss",
    "SuperstringAbyss",
    "MemorialBattle",
    "MemorialArena",
    "ElysianRealm",
]

# TODO: decide on whether to keep or not; if so, move to constants?
REMEMBRANCE_SIGILS = {
    119301: ("The MOTH Insignia", 1),
    119302: ("Home Lost", 1),
    119303: ("False Hope", 1),
    119304: ("Tin Flask", 1),
    119305: ("Ruined Legacy", 1),
    119306: ("Burden", 2),
    119307: ("Gold Goblet", 2),
    119308: ("Mad King's Mask", 2),
    119309: ("Light as a Bodhi Leaf", 2),
    119310: ("Forget-Me-Not", 2),
    119311: ("Forbidden Seed", 2),
    119312: ("Memory", 2),
    119313: ("Crystal Rose", 2),
    119314: ("Abandoned", 3),
    119315: ("Good Old Days", 3),
    119316: ("Shattered Shackles", 3),
    119317: ("Heavy as a Million Lives", 3),
    119318: ("Stained Sakura", 3),
    119319: ("The First Scale", 3),
    119320: ("Resolve", 3),
    119321: ("Thorny Crown", 3),
    # Probably ~10 more over the game's lifetime
}


# GENERIC


def _prettify_competitive_tier(tier: int) -> str:
    """Turn the tier returned by the API into the respective tier name displayed in-game"""
    return ["Basic", "Elites", "Masters", "Exalted"][tier - 1]


class Boss(models.APIModel, models.Unique):
    """Represents a Boss encountered in Abyss or Memorial Arena."""

    id: int
    name: str
    icon: str = Field(galias="avatar")

    @validator("icon")
    def __fix_url(cls, url: str) -> str:
        # I noticed that sometimes the urls are returned incorrectly, which appears to be
        # a problem on the hoyolab website too, so I expect this to be fixed sometime.
        # For now, this hotfix seems to work.
        return re.sub(r"/boss_\d+\.", lambda m: str.upper(m[0]), url, flags=re.IGNORECASE)


class ELF(models.APIModel, models.Unique):
    """Represents an ELF equipped for a battle."""

    id: int
    name: str
    icon: str = Field(galias="avatar")
    rarity: str
    upgrade_level: int = Field(galias="star")

    @validator("rarity", pre=True)
    def __fix_rank(cls, rarity: int):
        # ELFs come in rarities A and S, API returns 3 and 4, respectively
        return ["A", "S"][rarity - 3]


# ABYSS


def _prettify_abyss_rank(rank: int, tier: int) -> str:
    """Turn the rank returned by the API into the respective rank name displayed in-game."""

    if tier == 4:
        return (
            "Forbidden",
            "Sinful I",
            "Sinful II",
            "Sinful III",
            "Agony I",
            "Agony II",
            "Agony III",
            "Redlotus",
            "Nirvana",
        )[rank - 1]
    return ("Forbidden", "Sinful", "Agony", "Redlotus")[rank - 1]


class BaseAbyss(models.APIModel):
    """Represents one cycle of abyss (3 days per cycle, 2 cycles per week)"""

    # somewhat feel like this is overkill

    raw_tier: int = Field(galias="area")
    score: int
    lineup: List[base.Battlesuit]
    boss: Boss
    elf: Optional[ELF]

    @property
    def tier(self):
        """The user's Abyss tier as displayed in-game."""
        return _prettify_competitive_tier(self.raw_tier)


class OldAbyss(BaseAbyss):
    """Represents once cycle of Quantum Singularis or Dirac Sea,
    exclusive to players of level 80 and below
    """

    # NOTE endpoint: game_record/honkai3rd/api/newAbyssReport

    end_time: datetime = Field(galias="time_second")
    type: str = Field(mi18n="Quantum")
    result: str = Field(galias="reward_type")
    raw_rank: int = Field(galias="level")

    @validator("type")
    def __parse_type(cls, type_: str) -> str:
        # Parse lazy alias to actual in-game name
        return {"OW": "Dirac Sea", "Quantum": "Q-Singularis"}[type_]

    @validator("raw_rank", pre=True)
    def __normalize_level(cls, rank: str) -> int:
        """The latestOldAbyssReport endpoint returns ranks as D/C/B/A,
        while newAbyssReport returns them as 1/2/3/4(/5) respectively.
        Having them as ints at base seems more useful than strs.
        (in-game, they use the same names (Sinful, Agony, etc.))
        """
        return 69 - ord(rank)

    @property
    def rank(self):
        """The user's Abyss rank as displayed in-game."""
        return _prettify_abyss_rank(self.raw_rank, self.raw_tier)


class SuperstringAbyss(BaseAbyss):
    """Represents one cycle of Superstring Abyss, exclusive to players of level 81 and up."""

    # NOTE endpoint: game_record/honkai3rd/api/latestOldAbyssReport

    end_time: datetime = Field(galias="updated_time_second")
    raw_tier: int = 4  # Not returned by API, always the case
    placement: int = Field(galias="rank")
    trophies_gained: int = Field(galias="settled_cup_number")
    end_trophies: int = Field(galias="cup_number")
    raw_start_rank: int = Field(galias="level")
    raw_end_rank: int = Field(galias="settled_level")

    @property
    def start_rank(self) -> str:
        """The rank the user started the abyss cycle with, as displayed in-game."""
        return _prettify_abyss_rank(self.raw_start_rank, self.raw_tier)

    @property
    def end_rank(self) -> str:
        """The rank the user ended the abyss cycle with, as displayed in-game."""
        return _prettify_abyss_rank(self.raw_end_rank, self.raw_tier)

    @property
    def start_trophies(self) -> int:
        return self.end_trophies - self.trophies_gained


# MEMORIAL ARENA


def _prettify_MA_rank(rank: int) -> str:
    """Turn the rank returned by the API into the respective rank name displayed in-game."""
    brackets = (0, 0.20, 2, 7, 17, 35, 65)
    return f"{brackets[rank - 1]:1.2f} ~ {brackets[rank]:1.2f}"


class MemorialBattle(models.APIModel):
    """Represents weekly performance against a single Memorial Arena boss."""

    score: int
    lineup: List[base.Battlesuit]
    elf: Optional[ELF]
    boss: Boss


class MemorialArena(models.APIModel):
    """Represents aggregate weekly performance for the entire Memorial Arena rotation."""

    score: int
    ranking: float = Field(galias="ranking_percentage")
    raw_rank: int = Field(galias="rank")
    raw_tier: int = Field(galias="area")
    end_time: datetime = Field(galias="time_second")
    battle_data: List[MemorialBattle] = Field(galias="battle_infos")

    @property
    def rank(self) -> str:
        """The user's Memorial Arena rank as displayed in-game."""
        return _prettify_MA_rank(self.raw_rank)

    @property
    def tier(self) -> str:
        """The user's Memorial Arena tier as displayed in-game."""
        return _prettify_competitive_tier(self.raw_tier)


# ELYSIAN REALMS
# TODO: Implement a way to link response_json["avatar_transcript"] data to be added to
#       ER lineup data; will require new Battlesuit subclass.


class Condition(models.APIModel):
    """Represents a debuff picked at the beginning of an Elysian Realms run."""

    name: str
    description: str = Field(galias="desc")
    difficulty: int


class Signet(models.APIModel):
    """Represents a buff Signet picked in an Elysian Realms run."""

    id: int
    icon: str
    number: int

    @property
    def name(self) -> str:
        return [
            "Deliverance",
            "Gold",
            "Decimation",
            "Bodhi",
            "Setsuna",
            "Infinity",
            "Vicissitude",
            "■■",
        ][self.id - 1]

    def get_scaled_icon(self, scale: Literal[1, 2, 3] = 2) -> str:
        if not 1 <= scale <= 3:
            raise ValueError("Scale must lie between 1 and 3.")
        return self.icon.replace("@2x", "" if scale == 1 else f"@{scale}x")


class RemembranceSigil(models.APIModel):
    """Represents a Remembrance Sigil from Elysian Realms."""

    icon: str

    @property
    def id(self):
        match = re.match(r".*/(\d+).png", self.icon)
        return match[1] if match else 0

    @property
    def name(self):
        sigil = REMEMBRANCE_SIGILS.get(self.id)
        return sigil[0] if sigil else "Unknown"

    @property
    def rarity(self):
        sigil = REMEMBRANCE_SIGILS.get(self.id)
        return sigil[1] if sigil else "Unknown"


class ElysianRealm(models.APIModel):
    """Represents one completed run of Elysean Realms."""

    completed_at: datetime = Field(galias="settle_time_second")
    floors_cleared: int = Field(galias="level")
    score: int
    difficulty: int = Field(galias="punish_level")
    conditions: List[Condition]
    signets: List[Signet] = Field(galias="buffs")
    leader: base.Battlesuit = Field(galias="main_avatar")
    supports: List[base.Battlesuit] = Field(galias="support_avatars")
    elf: Optional[ELF]
    remembrance_sigil: RemembranceSigil = Field(galias="extra_item_icon")

    @validator("remembrance_sigil", pre=True)
    def __extend_sigil(cls, icon_url: str) -> RemembranceSigil:
        return RemembranceSigil(icon=icon_url)

    @property
    def lineup(self) -> List[base.Battlesuit]:
        return [self.leader, *self.supports]
