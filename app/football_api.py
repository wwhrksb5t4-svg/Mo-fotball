import httpx

FOOTBALL_BASE = "https://api.football-data.org/v4"


async def fetch_competition_teams(competition_code: str, token: str):
    headers = {"X-Auth-Token": token}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{FOOTBALL_BASE}/competitions/{competition_code}/teams",
            headers=headers,
        )
        response.raise_for_status()
        return response.json().get("teams", [])


async def fetch_team_matches(team_id: int, token: str, limit: int = 10):
    headers = {"X-Auth-Token": token}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{FOOTBALL_BASE}/teams/{team_id}/matches",
            headers=headers,
            params={"status": "FINISHED", "limit": limit},
        )
        response.raise_for_status()
        return response.json().get("matches", [])
