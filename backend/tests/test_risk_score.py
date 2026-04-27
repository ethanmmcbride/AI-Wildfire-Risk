from ai_wildfire_tracker.api.server import _fallback_risk


def test_fallback_risk_increases_with_brightness():
    low = _fallback_risk(300.0, 20.0)
    high = _fallback_risk(350.0, 20.0)
    assert high > low


def test_fallback_risk_increases_with_frp():
    low = _fallback_risk(320.0, 10.0)
    high = _fallback_risk(320.0, 40.0)
    assert high > low


def test_fallback_risk_ranks_severe_fire_higher_than_mild():
    mild = _fallback_risk(300.0, 10.0)
    severe = _fallback_risk(360.0, 55.0)
    assert severe > mild


def test_fallback_risk_same_inputs_same_score():
    a = _fallback_risk(333.0, 22.0)
    b = _fallback_risk(333.0, 22.0)
    assert a == b


def test_fallback_risk_handles_missing_values():
    assert _fallback_risk(None, 20.0) >= 0
    assert _fallback_risk(320.0, None) >= 0
    assert _fallback_risk(None, None) == 0.0
