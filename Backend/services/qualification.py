# pyrefly: ignore [missing-import]
from leaderboard import top_players


def qualified(uid, players):

    winners = top_players(players)

    for player in winners:

        if player["uid"] == uid:

            return True

    return False