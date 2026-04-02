from fastapi import APIRouter, Request

from app.models.frame import CompetitionSummary
from app.services.data_loader import load_competitions

router = APIRouter(tags=["competitions"])

# Cache competitions list in module memory (static data, never changes)
_competitions_cache: list[dict] | None = None


@router.get("/competitions", response_model=list[CompetitionSummary])
async def list_competitions(request: Request) -> list[CompetitionSummary]:
    """
    Returns competitions that have StatsBomb 360 data available.
    Filtered by `match_available_360` field in competitions.json.
    """
    global _competitions_cache
    if _competitions_cache is None:
        _competitions_cache = await load_competitions(request.app.state.http_client)

    return [
        CompetitionSummary(
            competition_id=c["competition_id"],
            season_id=c["season_id"],
            competition_name=c["competition_name"],
            season_name=c["season_name"],
            country_name=c["country_name"],
        )
        for c in _competitions_cache
        if c.get("match_available_360") is not None
    ]
