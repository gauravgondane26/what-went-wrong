from fastapi import APIRouter, HTTPException, Request

from app.models.frame import GoalSummary, MatchSummary
from app.services import data_loader, possession

router = APIRouter(tags=["matches"])


@router.get(
    "/competitions/{competition_id}/seasons/{season_id}/matches",
    response_model=list[MatchSummary],
)
async def list_matches(
    competition_id: int, season_id: int, request: Request
) -> list[MatchSummary]:
    """
    Returns matches for the given competition/season that have 360 data available.
    Filtered by `match_status_360 == "available"`.
    """
    try:
        matches = await data_loader.load_matches(
            request.app.state.http_client, competition_id, season_id
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load matches: {exc}")

    result = []
    for m in matches:
        if m.get("match_status_360") != "available":
            continue
        result.append(
            MatchSummary(
                match_id=m["match_id"],
                match_date=m.get("match_date", ""),
                home_team_id=m["home_team"]["home_team_id"],
                home_team_name=m["home_team"]["home_team_name"],
                away_team_id=m["away_team"]["away_team_id"],
                away_team_name=m["away_team"]["away_team_name"],
                home_score=m.get("home_score", 0),
                away_score=m.get("away_score", 0),
                competition_stage=m.get("competition_stage", {}).get("name", ""),
            )
        )
    return result


@router.get("/matches/{match_id}/goals", response_model=list[GoalSummary])
async def list_goals(match_id: int, request: Request) -> list[GoalSummary]:
    """
    Returns all goals in a match with metadata for the goal selector UI.
    Loads event data but NOT 360 data (keeps this endpoint fast).
    """
    try:
        events = await data_loader.load_events(
            request.app.state.http_client, match_id
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load events: {exc}")

    goal_events = possession.find_goal_events(events)

    # Build a team ID → name lookup from event data
    team_lookup: dict[int, str] = {}
    for e in events:
        team = e.get("team", {})
        if team.get("id") and team.get("name"):
            team_lookup[team["id"]] = team["name"]

    # Build possession-team ID → team ID lookup
    # (for identifying the conceding team = the non-attacking team)
    all_team_ids = list(team_lookup.keys())

    result = []
    for g in goal_events:
        type_name = g.get("type", {}).get("name", "")
        scoring_team_id = g["possession_team"]["id"]
        scoring_team_name = g["possession_team"]["name"]

        # Conceding team is whichever team is NOT the possession team
        conceding_team_id = next(
            (tid for tid in all_team_ids if tid != scoring_team_id), scoring_team_id
        )
        conceding_team_name = team_lookup.get(conceding_team_id, "Unknown")

        xg: float | None = None
        if type_name == "Shot":
            xg = (g.get("shot") or {}).get("statsbomb_xg")

        seq_len = possession.sequence_length_for_goal(events, g)

        result.append(
            GoalSummary(
                goal_event_id=g["id"],
                goal_event_index=g["index"],
                minute=g.get("minute", 0),
                second=g.get("second", 0),
                period=g.get("period", 1),
                scoring_team_id=scoring_team_id,
                scoring_team_name=scoring_team_name,
                conceding_team_id=conceding_team_id,
                conceding_team_name=conceding_team_name,
                xg=xg,
                possession_number=g.get("possession", 0),
                is_penalty=g.get("period", 1) == 5,
                sequence_length=seq_len,
            )
        )
    return result
