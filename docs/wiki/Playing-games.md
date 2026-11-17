# Playing games

Almost every Windows game runs on Sidewinder through **Proton**, which is built into Steam.

## Steam
1. Click **Steam** in the panel and log in.
2. Install and play like on Windows.
3. Check how a game runs before you buy it at **protondb.com**.

If a game won't start: right-click it, then **Properties**, then **Compatibility**, tick the box and pick **Proton Experimental**.

## Epic and GOG: Heroic
Open **Heroic**, log in to Epic or GOG, and install your games. It handles Proton for you.

## Everything else: Lutris
Battle.net, EA, Ubisoft and others: open **Lutris** and search for the launcher you need. It installs it with the right settings.

## Games that don't work
Some online games block Linux with their anti-cheat, for example Valorant and Fortnite. Check a game at **areweanticheatyet.com**.

## Extras
| Want | Do this (Steam: right-click the game, Properties, Launch options) |
|---|---|
| FPS counter | `mangohud %command%` |
| Extra boost | `gamemoderun %command%` |
| Both | `gamemoderun mangohud %command%` |

**ProtonUp-Qt** installs other Proton versions like GE-Proton, which fix some games. After installing one, pick it in the game's Compatibility settings.
