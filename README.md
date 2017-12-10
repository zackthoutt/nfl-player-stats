# NFL Football Stats
My family has always been serious about fantasy football. I've managed my own team since elementary school. It's a fun reason to talk with each other on a weekly basis for almost half the year. 

Ever since I was in 8th grade I've dreamed of building an AI that could draft players and choose lineups for me. I started off in Excel and have since worked my way up to more sophisticated machine learning. The one thing that I've been lacking is really good data, which is why I decided to scrape `pro-football-reference.com` for all recorded NFL player data. 

From what I've been able to determine researching, this is the most complete public source of NFL player stats available online. I scraped every NFL player in their database going back to the 1940s. That's over 25,000 players who have played over 1,000,000 football games. 

I finished in last place this year in fantasy football, so hopefully this data will help me improve my performance next year. Only 8 months until draft day! 

My ultimate goal is to create an AI that ranks players every week, which could be used to set lineups and draft players. I'm also interested in predicting the winners of games. If you have any ideas or would like to collaborate, please [contact me](mailto:me@zackthoutt.com)!

# Featured on Kaggle

**The data was scraped 12/1/17-12/4/17**

[Kaggle Dataset](https://www.kaggle.com/zynicide/nfl-football-player-stats)

---

The data is broken into two parts. There is a players table where each player has been asigned an ID and a game stats table that has one entry per game played. These tables can be linked together using the player ID.

## Player Profile Fields

- *Player ID*: The assigned ID for the player.
- *Name*: The player's full name.
- *Position*: The position the player played abbreviated to two characters. If the player played more than one position, the position field will be a comma-separated list of positions (i.e. "hb,qb").
- *Height*: The height of the player in feet and inches. The data format is <feet>-<inches>. So 6-5 would be six feet and five inches tall.
- *Weight*: The weight of the player in pounds.
- *Current Team*: The three-letter code of the team the player plays for. This is null if they are not currently active.
- *Birth Date*: The day, month, and year the player was born. This is null if unknown.
- *Birth Place*: The city, state or city, country the player was born in. This is null if unknown.
- *Death Date*: The day, month, and year the player died. This is null if they are still alive.
- *College*: The name of the college they played football at. This is null if they did not play football in college.
- *High School*: the city, state or city, country the player went to high school. This is null if the player didn't go to high school or if the school is unknown.
- *Draft Team*: The three letter code of the team that drafted the player. This is null if the player was not drafted. 
- *Draft Position*: The draft position number the player was taken. Again, null if the player was not drafted.
- *Draft Round*: The round of the draft the player was drafted in. Null if the player was not drafted.
- *Draft Position*: The position the player was drafted at as a two-letter code. Null if the player was not drafted.
- *Draft Year*: The year the player was drafted. Null if the player was not drafted.
- *Current Salary Cap Hit*: The player's current salary hit for their current team. Null if the player is not currently active on a team.
- *Hall of Fame Induction Year*: The year the player was inducted into the NFL Hall of Fame. Null if the player has not been inducted into the HOF yet.

### Game Stats Fields

Note that if there are games missing in the season for a player (i.e. the player has logs for games 1, 2, 3, 5, 6,...), then they didn't play in game 4 because of injury, suspension, etc. 

**Game Info:**

- *Player ID*: The assigned ID for the player.
- *Year*: The year the game took place.
- *Game ID*: The assigned ID for the game (format YYYYMMDD0\<hometeam\>).
- *Date*: The date the game took place.
- *Game Number*: The number of the game when all games in a season are numbered sequentially. 
- *Age*: The age of the player when the game was played. This is in the format <years>-<days>. So 22-344 would be 22 years and 344 days old. 
- *Team*: The three-letter code of the team the player played for.
- *Game Location*: One of H, A, or N. H=Home, A=Away, and N=Neutral.
- *Opponent*: The three-letter code of the team the game was played against.
- *Player Team Score*: The score of the team the player played for.
- *Opponent Score*: The score of the team the player played against. You can use this field and the last field to determine if the player's team won.

**Passing Stats:**

- *Passing Attempts*: The number of passes thrown by the player.
- *Passing Completions*: The number of completions thrown by the player.
- *Passing Yards*: The number of passing yards thrown by the player.
- *Passing Rating*: The NFL passer rating for the player in that game.
- *Passing Touchdowns*: The number of passing touchdowns the player threw.
- *Passing Interceptions*: The number of interceptions the player threw.
- *Passing Sacks*: The number of times the player was sacked.
- *Passing Sacks Yards Lost*: The cumulative yards lost from the player being sacked.

**Rushing Stats:**

- *Rushing Attempts*: The number of times the the player attempted a rush.
- *Rushing Yards*: The number of yards the player rushed for.
- *Rushing Touchdowns*: The number of touchdowns the player rushed for.

**Receiving Stats:**

- *Receiving Targets*: The number of times the player was thrown to.
- *Receiving Receptions*: The number of times the player caught a pass thrown to them.
- *Receiving Yards*: The number of yards the player gained through receiving.
- *Receiving Touchdowns*: The number of touchdowns scored through receiving.

**Kick/Punt Return Stats**

- *Kick Return Attempts*: The number of times the player attempted to return a kick.
- *Kick Return Yards*: The cumulative number of yards the player returned kicks for.
- *Kick Return Touchdowns*: The number of touchdowns the player scored through kick returns.
- *Punt Return Attempts*: The number of times the player attempted to return a punt.
- *Punt Return Yards*: The cumulative number of yards the player returned punts for.
- *Punt Return Touchdowns*: The number of touchdowns the player scored through punt returns.

**Kick/Punt Stats**

- *Point After Attempts*: The number of PAs the player attempted kicking.
- *Point After Makes*: The number of PAs the player made.
- *Field Goal Attempts*: The number of field goals the player attempted.
- *Field Goal Makes*: The number of field goals the player made.

**Defense Stats**

- *Sacks*: The number of sacks the player got.
- *Tackles*: The number of tackles the player got.
- *Tackle Assists*: The number of tackles the player assisted on.
- *Interceptions*: The number of times the player intercepted the ball.
- *Interception Yards*: The number of yards the player gained after interceptions.
- *Interception Touchdowns*: The number of touchdowns the player scored after interceptions.
- *Safeties*: The number of safeties the player caused.

### Futute Improvements

1. Format data in an SQLite database
2. Extract Team IDs to make relating players across teams and games easier
3. Scrape college data (there are links on the website that shouldn't be too difficult to scrape)
4. Figure out another method of scraping some additional data that isn't available on pro-football-reference.com, such as fumbles, passes defended, etc.
5. Resolve blocking stats back to lineman based on the team they played for and the QB's sack stats for that game.

### Contributing

If you would like to contribute, please feel free to put up a PR or reach out to me with ideas. I would love to collaborate with some fellow football fans on this project. 

# Connect with me

If you'd like to collaborate on a project, learn more about me, or just say hi, feel free to contact me using any of the social channels listed below.

- [Personal Website](https://zackthoutt.com)
- [Email](mailto:zackarey.thoutt@colorado.edu)
- [LinkedIn](https://www.linkedin.com/in/zack-thoutt-57275655/)
- [Twitter](https://twitter.com/zthoutt)
- [Medium](https://medium.com/@zthoutt)
- [Quora](https://www.quora.com/profile/Zack-Thoutt)
- [HackerNews](https://news.ycombinator.com/submitted?id=zthoutt)
- [Reddit](https://www.reddit.com/user/zthoutt/)
- [Kaggle](https://www.kaggle.com/zynicide)
- [Instagram](https://www.instagram.com/zthoutt/)
- [500px](https://500px.com/zthoutt)
