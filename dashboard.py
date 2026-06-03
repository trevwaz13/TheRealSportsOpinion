import nfl_data_py as nfl

df = nfl.import_weekly_data([2024])

top_passers = df.groupby(['player_name','recent_team'])['passing_yards'].sum()
top_passers = top_passers.sort_values(ascending=False).head(10).reset_index()

print("THE REAL SPORTS OPINION")
print("Top 10 Passers - 2024 Season")
print("="*40)
for i, row in top_passers.iterrows():
    print(f"{i+1}. {row['player_name']} ({row['recent_team']}): {int(row['passing_yards'])} yds")