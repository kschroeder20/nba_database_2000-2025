---
title: NBA Database 2000-2025
emoji: 🏀
colorFrom: red
colorTo: yellow
sdk: docker
pinned: false
---

# NBA Database (2000-2025)

An interactive database of NBA statistics from the 1999-2000 through 2024-25 seasons, powered by [Datasette](https://datasette.io/).

## What's Inside

This database contains comprehensive NBA data scraped from Basketball Reference:

- **Players**: Biographical info, height, weight, position, draft details
- **Teams**: Team identifiers with conference and division
- **Player Season Stats**: Per-game and advanced stats (points, rebounds, assists, PER, true shooting %, win shares, BPM, VORP)
- **Team Season Stats**: Team records, pace, offensive/defensive ratings, SRS
- **Games**: Individual game results with dates, teams, scores

## How to Use

- Browse tables and filter data using the interface
- Run custom SQL queries
- Export data as JSON or CSV
- Use the API endpoints for programmatic access

## Technical Details

- **Database Size**: 4.3 MB
- **Format**: SQLite
- **Interface**: Datasette
- **Data Source**: Basketball Reference

## Example Queries

Try these SQL queries:

```sql
-- Top scorers in 2023-24 season
SELECT player_name, team_id, points_per_game
FROM player_season_stats
WHERE season = '2023-24'
ORDER BY points_per_game DESC
LIMIT 10;

-- Teams with best records
SELECT season, team_id, wins, losses
FROM team_season_stats
ORDER BY wins DESC
LIMIT 20;
```

---