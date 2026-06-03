import nflreadpy as nfl
import polars as pl
import json

current_season = nfl.get_current_season()
current_week = nfl.get_current_week()
print(f"Loading season {current_season}, week {current_week}...")

stats = nfl.load_player_stats([current_season])

print("All rows:", stats.shape)

regular_stats = stats.filter(pl.col("season_type") == "REG")
playoff_stats = stats.filter(pl.col("season_type") == "POST")

print("Regular season rows:", regular_stats.shape)
print("Playoff rows:", playoff_stats.shape)

def build_leaderboards(df):
    top_pass = df.group_by(['player_display_name','team']).agg([
        pl.col('passing_yards').sum(),
        pl.col('passing_tds').sum(),
        pl.col('completions').sum(),
        pl.col('attempts').sum(),
    ]).sort('passing_yards', descending=True).head(10)

    top_rush = df.group_by(['player_display_name','team']).agg([
        pl.col('rushing_yards').sum(),
        pl.col('rushing_tds').sum(),
        pl.col('carries').sum(),
    ]).sort('rushing_yards', descending=True).head(10)

    top_rec = df.group_by(['player_display_name','team']).agg([
        pl.col('receiving_yards').sum(),
        pl.col('receiving_tds').sum(),
        pl.col('receptions').sum(),
        pl.col('targets').sum(),
    ]).sort('receiving_yards', descending=True).head(10)

    return {
        "passers": [{"name": r['player_display_name'], "team": r['team'],
                     "yards": int(r['passing_yards']), "tds": int(r['passing_tds']),
                     "completions": int(r['completions']), "attempts": int(r['attempts'])}
                    for r in top_pass.to_dicts()],
        "rushers": [{"name": r['player_display_name'], "team": r['team'],
                     "yards": int(r['rushing_yards']), "tds": int(r['rushing_tds']),
                     "carries": int(r['carries'])}
                    for r in top_rush.to_dicts()],
        "receivers": [{"name": r['player_display_name'], "team": r['team'],
                       "yards": int(r['receiving_yards']), "tds": int(r['receiving_tds']),
                       "receptions": int(r['receptions']), "targets": int(r['targets'])}
                      for r in top_rec.to_dicts()]
    }

reg_weeks = regular_stats['week'].unique().to_list()
last_reg_week = max(reg_weeks) if reg_weeks else 18

playoff_weeks = playoff_stats['week'].unique().to_list()
last_playoff_week = max(playoff_weeks) if playoff_weeks else 0

reg_data = build_leaderboards(regular_stats)
playoff_data = build_leaderboards(playoff_stats)

data = {
    "season": int(current_season),
    "regular_season_week": int(last_reg_week),
    "playoff_week": int(last_playoff_week),
    "has_playoffs": len(playoff_stats) > 0,
    "regular": reg_data,
    "playoffs": playoff_data
}

with open('/Users/trevorwaz/TheRealSportsOpinion/data.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Done! Season {current_season} exported.")
print(f"Regular season through week {last_reg_week}")
print(f"Playoffs: {'Yes' if data['has_playoffs'] else 'No data yet'}")
print(f"Top passer (reg):   {reg_data['passers'][0]['name']} - {reg_data['passers'][0]['yards']} yds, {reg_data['passers'][0]['tds']} TDs")
print(f"Top rusher (reg):   {reg_data['rushers'][0]['name']} - {reg_data['rushers'][0]['yards']} yds, {reg_data['rushers'][0]['tds']} TDs")
print(f"Top receiver (reg): {reg_data['receivers'][0]['name']} - {reg_data['receivers'][0]['yards']} yds, {reg_data['receivers'][0]['tds']} TDs")
