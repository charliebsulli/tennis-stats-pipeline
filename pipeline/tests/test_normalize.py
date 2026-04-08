from pipeline.transform.normalize import ROUND_ORDER
from pipeline.transform.player_id_helper import normalize_name


def test_normalize_accents():
    assert normalize_name("Jiří Lehečka") == "jiri lehecka"


def test_normalize_name_hyphens():
    assert normalize_name("Botic van de Zandschulp") == normalize_name(
        "botic van-de-Zandschulp"
    )


def test_normalize_name_case():
    assert normalize_name("Rafael Nadal") == normalize_name("rafael nadal")


def test_normalize_round_order_same():
    assert ROUND_ORDER.get("QF") == ROUND_ORDER.get("Quarterfinals")


def test_normalize_round_order_later():
    assert ROUND_ORDER.get("F") > ROUND_ORDER.get("SF")
