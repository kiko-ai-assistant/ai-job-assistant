from roles import enabled_targets


def test_enabled_targets_filters_groups():
    targets = enabled_targets(("it",))
    assert targets
    assert all(target.group == "it" for target in targets)
