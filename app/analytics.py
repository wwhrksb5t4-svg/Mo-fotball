import math
import re
from difflib import SequenceMatcher


def clean_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def best_team_match(query: str, teams: list[dict]) -> dict:
    normalized = clean_name(query)
    scored = []
    for team in teams:
        names = (team.get("name", ""), team.get("shortName", ""))
        score = max(
            (SequenceMatcher(None, normalized, clean_name(name)).ratio() for name in names),
            default=0.0,
        )
        scored.append((score, team))

    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored or scored[0][0] < 0.55:
        raise ValueError(f"Could not confidently match team name: {query}")
    return scored[0][1]


def team_averages(team_id: int, matches: list[dict]) -> tuple[float, float, int]:
    scored, conceded = [], []
    for match in matches:
        score = match.get("score", {}).get("fullTime", {})
        home_goals, away_goals = score.get("home"), score.get("away")
        if home_goals is None or away_goals is None:
            continue

        if match.get("homeTeam", {}).get("id") == team_id:
            scored.append(home_goals)
            conceded.append(away_goals)
        elif match.get("awayTeam", {}).get("id") == team_id:
            scored.append(away_goals)
            conceded.append(home_goals)

    if not scored:
        raise ValueError("Not enough completed match data for this team.")
    return sum(scored) / len(scored), sum(conceded) / len(conceded), len(scored)


def _poisson_probability(lam: float, goals: int) -> float:
    lam = max(0.05, min(lam, 6.0))
    return math.exp(-lam) * (lam**goals) / math.factorial(goals)


def calculate_probabilities(home_xg: float, away_xg: float) -> dict[str, float]:
    home = draw = away = over_25 = 0.0
    for home_goals in range(9):
        for away_goals in range(9):
            probability = _poisson_probability(home_xg, home_goals) * _poisson_probability(away_xg, away_goals)
            if home_goals > away_goals:
                home += probability
            elif home_goals == away_goals:
                draw += probability
            else:
                away += probability
            if home_goals + away_goals >= 3:
                over_25 += probability
    return {"home": home, "draw": draw, "away": away, "over25": over_25}
