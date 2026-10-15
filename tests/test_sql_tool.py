from app.sql_tool import get_schema, run_query, validate_query


def test_schema_keeps_comments(tiny_db):
    assert "team name, or 'Draw'" in get_schema(tiny_db)


def test_select_returns_rows(tiny_db):
    out = run_query("SELECT COUNT(*) AS wins FROM matches WHERE winner = 'Tunisia'", tiny_db)
    assert out.splitlines() == ["wins", "3"]


def test_with_clause_allowed(tiny_db):
    out = run_query("WITH t AS (SELECT * FROM matches) SELECT COUNT(*) FROM t", tiny_db)
    assert "4" in out


def test_write_queries_are_refused(tiny_db):
    for q in ["DELETE FROM matches", "DROP TABLE matches", "UPDATE matches SET winner = 'x'",
              "SELECT 1; DROP TABLE matches", "PRAGMA table_info(matches)"]:
        assert run_query(q, tiny_db).startswith("ERROR"), q
    assert "4" in run_query("SELECT COUNT(*) FROM matches", tiny_db)  # table still intact


def test_sql_error_is_returned_as_text(tiny_db):
    out = run_query("SELECT goals FROM matches", tiny_db)
    assert out.startswith("ERROR") and "no such column" in out


def test_empty_result_gives_a_hint(tiny_db):
    assert "no rows" in run_query("SELECT * FROM matches WHERE home_team = 'USA'", tiny_db)


def test_validate_query():
    assert validate_query("select * from matches;") is None
    assert validate_query("") is not None
