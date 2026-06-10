from pydantic import BaseModel


class MatchCompleteResponse(BaseModel):
    phase: str
    round_num: int
    season_year: int
    status_message: str | None
