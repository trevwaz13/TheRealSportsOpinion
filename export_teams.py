import nflreadpy as nfl
import polars as pl
import json

current_season = nfl.get_current_season()
print(f"Loading team data for {current_season}...")

team_stats = nfl.load_team_stats([current_season])
schedules = nfl.load_schedules([current_season])
roster = nfl.load_rosters([current_season])

reg_team = team_stats.filter(pl.col("season_type") == "REG")
reg_sched = schedules.filter(pl.col("game_type") == "REG")
post_sched = schedules.filter(pl.col("game_type") != "REG")

all_teams = reg_team["team"].unique().to_list()
all_teams.sort()

def get_team_record(team, sched):
    home = sched.filter(pl.col("home_team") == team).select(["home_score","away_score"]).to_dicts()
    away = sched.filter(pl.col("away_team") == team).select(["home_score","away_score"]).to_dicts()
    wins = losses = ties = pf = pa = 0
    for g in home:
        if g["home_score"] is None or g["away_score"] is None: continue
        pf += g["home_score"]; pa += g["away_score"]
        if g["home_score"] > g["away_score"]: wins += 1
        elif g["home_score"] < g["away_score"]: losses += 1
        else: ties += 1
    for g in away:
        if g["home_score"] is None or g["away_score"] is None: continue
        pf += g["away_score"]; pa += g["home_score"]
        if g["away_score"] > g["home_score"]: wins += 1
        elif g["away_score"] < g["home_score"]: losses += 1
        else: ties += 1
    return wins, losses, ties, pf, pa

def get_team_schedule(team, sched):
    games = []
    home_games = sched.filter(pl.col("home_team") == team).select(
        ["week","home_team","away_team","home_score","away_score","game_type","stadium"]).to_dicts()
    away_games = sched.filter(pl.col("away_team") == team).select(
        ["week","home_team","away_team","home_score","away_score","game_type","stadium"]).to_dicts()
    for g in home_games:
        played = g["home_score"] is not None
        result = None
        if played:
            result = "W" if g["home_score"] > g["away_score"] else "L" if g["home_score"] < g["away_score"] else "T"
        games.append({"week": g["week"], "home": True, "opponent": g["away_team"],
                      "team_score": g["home_score"], "opp_score": g["away_score"],
                      "result": result, "played": played, "stadium": g["stadium"] or ""})
    for g in away_games:
        played = g["away_score"] is not None
        result = None
        if played:
            result = "W" if g["away_score"] > g["home_score"] else "L" if g["away_score"] < g["home_score"] else "T"
        games.append({"week": g["week"], "home": False, "opponent": g["home_team"],
                      "team_score": g["away_score"], "opp_score": g["home_score"],
                      "result": result, "played": played, "stadium": g["stadium"] or ""})
    games.sort(key=lambda x: x["week"])
    return games

def get_team_stats(team, df):
    t = df.filter(pl.col("team") == team)
    if len(t) == 0: return {}
    return {
        "passing_yards": int(t["passing_yards"].sum()),
        "passing_tds": int(t["passing_tds"].sum()),
        "rushing_yards": int(t["rushing_yards"].sum()),
        "rushing_tds": int(t["rushing_tds"].sum()),
        "receiving_yards": int(t["receiving_yards"].sum()),
        "def_sacks": int(t["def_sacks"].sum()),
        "def_interceptions": int(t["def_interceptions"].sum()),
        "passing_interceptions": int(t["passing_interceptions"].sum()),
    }

def get_top_players(team, df):
    t = df.filter(pl.col("team") == team)
    passers = t.group_by("player_display_name").agg(pl.col("passing_yards").sum()).sort("passing_yards", descending=True).head(1)
    rushers = t.group_by("player_display_name").agg(pl.col("rushing_yards").sum()).sort("rushing_yards", descending=True).head(1)
    receivers = t.group_by("player_display_name").agg(pl.col("receiving_yards").sum()).sort("receiving_yards", descending=True).head(1)
    result = {}
    if len(passers) > 0 and passers[0]["passing_yards"] > 0:
        result["top_passer"] = {"name": passers[0]["player_display_name"], "yards": int(passers[0]["passing_yards"])}
    if len(rushers) > 0 and rushers[0]["rushing_yards"] > 0:
        result["top_rusher"] = {"name": rushers[0]["player_display_name"], "yards": int(rushers[0]["rushing_yards"])}
    if len(receivers) > 0 and receivers[0]["receiving_yards"] > 0:
        result["top_receiver"] = {"name": receivers[0]["player_display_name"], "yards": int(receivers[0]["receiving_yards"])}
    return result

player_stats = nfl.load_player_stats([current_season])
reg_player = player_stats.filter(pl.col("season_type") == "REG")

headshots = roster.select(["full_name","team","headshot_url"]).unique(subset=["full_name","team"])

teams_data = {}
for team in all_teams:
    wins, losses, ties, pf, pa = get_team_record(team, reg_sched)
    schedule = get_team_schedule(team, schedules)
    stats = get_team_stats(team, reg_team)
    top = get_top_players(team, reg_player)

    top_roster = roster.filter(pl.col("team") == team).select(
        ["full_name","position","jersey_number","headshot_url","years_exp"]).to_dicts()
    top_roster = [{"name": r["full_name"], "position": r["position"] or "",
                   "number": str(r["jersey_number"]) if r["jersey_number"] else "",
                   "headshot": r["headshot_url"] or "",
                   "exp": int(r["years_exp"]) if r["years_exp"] else 0}
                  for r in top_roster if r["full_name"]]

    teams_data[team] = {
        "team": team,
        "wins": wins, "losses": losses, "ties": ties,
        "points_for": pf, "points_against": pa,
        "schedule": schedule,
        "stats": stats,
        "top_players": top,
        "roster": top_roster
    }

with open('/Users/trevorwaz/TheRealSportsOpinion/teams.json', 'w') as f:
    json.dump({"season": int(current_season), "teams": teams_data}, f, indent=2)

print(f"Done! {len(teams_data)} teams exported.")
for t in list(teams_data.keys())[:3]:
    d = teams_data[t]
    print(f"  {t}: {d['wins']}-{d['losses']} | PF:{d['points_for']} PA:{d['points_against']}")
