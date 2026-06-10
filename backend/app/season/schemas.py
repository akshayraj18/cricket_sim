from pydantic import BaseModel


class DraftPickRequest(BaseModel):
    player_name: str


class AutodraftRequest(BaseModel):
    mode: str = "user"  # "user" | "all"


class LeadershipRequest(BaseModel):
    captain: str
    vice: str
    wicketkeeper: str = ""


class PresetsRequest(BaseModel):
    batting_order: list[str] = []
    bowling_order: list[str] = []
    batting_first_xi: list[str] | None = None
    bowling_first_xi: list[str] | None = None
    bat_to_bowl: dict[str, str] | None = None
    bowl_to_bat: dict[str, str] | None = None
    wicketkeeper: str = ""


class RetentionRequest(BaseModel):
    players: list[str]
