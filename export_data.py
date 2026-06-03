import nflreadpy as nfl
import polars as pl
import json

current_season = nfl.get_current_season()
current_week = nfl.get_current_week()
print(f"Loading season {current_season}, week {current_week}...")

stats = nfl.load_player_stats([current_season])

top_pass = stats.group_by(['player_display_name','team']).agg(pl.col('passing_yards').sum()).sort('passing_yards',descending=True).head(10)
top_rush = stats.group_by(['player_display_name','team']).agg(pl.col('rushing_yards').sum()).sort('rushing_yards',descending=True).head(10)
top_rec = stats.group_by(['player_display_name','team']).agg(pl.col('receiving_yards').sum()).sort('receiving_yards',descending=True).head(10)

data = {
    "season": int(current_season),
    "week": int(current_week),
    "passers": [{"name": r['player_display_name'], "team": r['team'], "yards": int(r['passing_yards'])} for r in top_pass.to_dicts()],
    "rushers": [{"name": r['player_display_name'], "team": r['team'], "yards": int(r['rushing_yards'])} for r in top_rush.to_dicts()],
    "receivers": [{"name": r['player_display_name'], "team": r['team'], "yards": int(r['receiving_yards'])} for r in top_rec.to_dicts()]
}

with open('/Users/trevorwaz/TheRealSportsOpinion/data.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Done! Season {current_season} exported.")
print(f"Top passer: {data['passers'][0]['name']} - {data['passers'][0]['yards']} yds")
print(f"Top rusher: {data['rushers'][0]['name']} - {data['rushers'][0]['yards']} yds")
print(f"Top receiver: {data['receivers'][0]['name']} - {data['receivers'][0]['yards']} yds")
