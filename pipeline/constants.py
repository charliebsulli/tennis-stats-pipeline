K_FACTOR = 32
ATP_CATEGORY_ID = "3"
CHALLENGER_CATEGORY_ID = "72"

# Sources that arrive as API rows and need player ids resolved through the
# crosswalk, with the raw_matches columns holding each source's player ids.
API_SOURCES = {
    "rapidapi": {
        "winner_id_col": "rapidapi_winner_id",
        "loser_id_col": "rapidapi_loser_id",
    },
    "livetennisapi": {
        "winner_id_col": "ltapi_winner_id",
        "loser_id_col": "ltapi_loser_id",
    },
}
