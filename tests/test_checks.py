from eval.checks import check_keywords, check_sql, value_in_answer


def test_numbers_and_names():
    assert check_sql("Tunisia won 296, drew 189 and lost 196 matches.", [296, 189, 196])
    assert not check_sql("Tunisia won 296 and drew 189 matches.", [296, 189, 196])
    assert value_in_answer("Samuel Eto'o", "The top scorer is Samuel Eto’o with 18 goals")
    assert value_in_answer(1105, "Sweden played 1,105 matches")
    assert value_in_answer(22.7, "About 23% of matches end in a draw")
    assert not value_in_answer(21, "Messi scored 213 goals")


def test_keywords():
    assert check_keywords("Uruguay beat Brazil in 1950", [["uruguay"], ["brazil"], ["1950"]])
    assert check_keywords("Only 3 teams played", [["three", "3"]])
    assert not check_keywords("Brazil lost", [["uruguay"], ["brazil"]])
