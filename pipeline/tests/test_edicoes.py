from pipeline.edicoes import ANOS, EDICOES, tem


def test_anos():
    assert ANOS == (1977, 1987, 1997, 2007, 2017, 2023)


def test_recursos():
    assert tem(2023, "raca") and not tem(2017, "raca")
    assert tem(2007, "coords") and not tem(1997, "coords")
    assert EDICOES[1977].area_parcial and not EDICOES[1977].amc146
