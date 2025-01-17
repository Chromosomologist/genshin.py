# Battle Chronicle

The main feature of genshin.py is the [Battle Chronicle](https://webstatic-sea.hoyolab.com/app/community-game-records-sea/index.html#/ys). It contains various features such as statistics, character equipment, spiral abyss runs, exploration progress, etc.

To request any of the Battle Chronicle endpoints you must first be logged in. Refer to [the authentication section](authentication.md) for more information.

## Quick example

```py
# get general user info:
user = await client.get_user(710785423)

# get spiral abyss runs:
data = await client.get_spiral_abyss(710785423, previous=True)

# get activities:
data = await client.get_activities(710785423)
```

## Real-Time Notes

Thanks to a relatively new feature added to battle chronicles you may now view your own resin count, explorations, comissions and similar data just using the API.

Currently you may only get your own data using your own cookies but a uid is still required.

```py
notes = await client.get_notes(710785423)
print(f"Resin: {notes.current_resin}/{notes.max_resin}")
print(f"Comissions: {notes.completed_comissions}/{notes.max_comissions}")
```

## Optimizations

Under the hood, `get_user` has to make two requests: one for the user and another for character equipment. If you do not care about character equipment, you should use `get_partial_user`.

```py
user = await client.get_partial_user(710785423)
print(user.stats.days_active)
```

On the other hand, if you want to request as much information as possible, you should use `get_full_user` which adds spiral abyss runs and activities to the user.

```py
user = await client.get_full_user(710785423)
print(user.abyss.previous.total_stars)
```
