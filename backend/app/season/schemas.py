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
    starting_xi: list[str] | None = None
    impact_sub_name: str | None = None
    wicketkeeper: str = ""


class RetentionRequest(BaseModel):
    players: list[str]


class RenameRequest(BaseModel):
    kind: str  # "team" | "player"
    old_name: str
    new_name: str
