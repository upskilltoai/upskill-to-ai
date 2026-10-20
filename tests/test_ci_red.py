def test_ci_must_fail():
    # Deliberately failing: proves CI goes red on a broken test.
    assert 1 == 2
