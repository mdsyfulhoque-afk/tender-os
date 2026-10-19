from tenderproof.services.tor_normalizer import generate_match_key


def test_same_input_creates_same_match_key():
    a = generate_match_key("TP-1", "methodology", "section 1", "The bidder shall submit a methodology.")
    b = generate_match_key("TP-1", "methodology", "section 1", "The bidder shall submit a methodology.")
    assert a == b


def test_different_requirement_creates_different_match_key():
    a = generate_match_key("TP-1", "methodology", "section 1", "The bidder shall submit a methodology.")
    b = generate_match_key("TP-1", "methodology", "section 1", "The bidder shall submit CVs.")
    assert a != b


def test_whitespace_changes_do_not_change_match_key():
    a = generate_match_key("TP-1", "methodology", "section 1", "The bidder shall submit a methodology.")
    b = generate_match_key("TP-1", "methodology", "section 1", "  The bidder   shall submit a methodology.  ")
    assert a == b

