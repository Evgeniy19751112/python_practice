from sqlalchemy import insert

from server_app.database import Followers, Likes, Medias, Tweets, Users
from server_app.database.db import DatabaseSessionManager


def fake_some_data(db: DatabaseSessionManager):
    db.execute(
        insert(Users).values(
            [
                {"api_key": "test", "username": "test only"},
                {"api_key": "dream", "username": "dream team"},
                {"api_key": "team", "username": "team dream"},
                # first
                {
                    "api_key": "=914d1151ebf54d7e030600fde29c05a1e11fce0fc087"
                    "c533ebba164edb812f7749a7a9db1727194f929ff9c94"
                    "518d58cd21b7f949c7341326c862683557b298acc3718"
                    "9d1d377b9e2ef4788ce53a1895efb56823ad64d586719"
                    "69a6e7bf9f256a540432729e50a23dcbc97584d388d77"
                    "041b24142cd038909c68bd26264209",
                    "username": "Mr. First",
                },
                # second
                {
                    "api_key": "=aa5c2730b708212656705ddfbc0a00d1948ca5e0c028"
                    "3124662cd688bec6ba00e46e0b747b53c55fe762122ee"
                    "92f01faf285d3f423e52907ab21e577c8dab06ffa6152"
                    "3a8be987ab09956c317192ec580faa5dd208ff70cf910"
                    "a2d782b79f03eb01584f0239760f5220e8086309be778"
                    "f82f01f00550bddf21919aed5db639",
                    "username": "Mr. Second",
                },
            ]
        )
    )
    db.execute(
        insert(Tweets).values(
            [
                {"user_id": 1, "text": "1One Two Three"},
                {"user_id": 2, "text": "2Three Two One"},
                {"user_id": 2, "text": "3One Two Three Again"},
                {"user_id": 5, "text": "4Three Two One Again"},
                {"user_id": 4, "text": "5Test. Test? Test!"},
            ]
        )
    )
    db.execute(
        insert(Medias).values(
            [
                {
                    "tweet_id": 1,
                    "filename": "nothing1",
                    "local_file": "/anything1",
                },
                {
                    "tweet_id": 4,
                    "filename": "nothing2",
                    "local_file": "/anything2",
                },
                {"tweet_id": 3, "filename": "ccc", "local_file": "/ccc.ext"},
                {"tweet_id": 2, "filename": "bbb", "local_file": "/bbb.ext"},
                {"tweet_id": 2, "filename": "ddd", "local_file": "/ddd.ext"},
            ]
        )
    )
    db.execute(
        insert(Likes).values(
            [
                {"user_id": 1, "tweet_id": 2, "name": "heart"},
                {"user_id": 2, "tweet_id": 2, "name": "star"},
                {"user_id": 1, "tweet_id": 1, "name": "smile"},
                {"user_id": 2, "tweet_id": 1, "name": "smile"},
            ]
        )
    )
    db.execute(
        insert(Followers).values(
            [
                {"follower_id": 1, "following_id": 2},
                {"follower_id": 3, "following_id": 2},
                {"follower_id": 3, "following_id": 1},
            ]
        )
    )
