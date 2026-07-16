def test_sourced_value():
    source = "authoritative"
    assert source == "authoritative"


def test_property_invariant():
    value = 2
    assert value * 2 == 4
