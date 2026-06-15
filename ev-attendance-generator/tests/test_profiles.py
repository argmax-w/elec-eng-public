"""Tests for the charging-demand profiles.

The configuration loader is pure parsing and is always tested. The sampling and
aggregation exercise the withheld engine, so those tests are skipped when it is
encrypted and absent (for example on a public CI checkout).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from evattendance.profiles import (
    ENGINE_AVAILABLE,
    TIME_GRID,
    CategorySpec,
    Mixture,
    MixtureComponent,
    build_demand_profile,
    load_fleet_config,
)

EXAMPLE_CONFIG = Path(__file__).resolve().parents[1] / "config" / "profiles.example.yaml"


def test_load_fleet_config_parses_structure():
    fleet = load_fleet_config(EXAMPLE_CONFIG)
    assert [spec.name for spec in fleet] == ["customer", "employee"]
    customer = fleet[0]
    assert isinstance(customer, CategorySpec)
    assert customer.fleet_size == 50
    assert customer.charger_kw == 7.0
    assert isinstance(customer.arrival, Mixture)
    assert isinstance(customer.arrival.components[0], MixtureComponent)


@pytest.mark.skipif(not ENGINE_AVAILABLE, reason="withheld engine not decrypted")
def test_demand_profile_shape_and_totals():
    fleet = load_fleet_config(EXAMPLE_CONFIG)
    profile = build_demand_profile(fleet, TIME_GRID, seed=1)

    assert len(profile) == len(TIME_GRID)
    for spec in fleet:
        counts = profile[f"count_{spec.name}"]
        assert counts.min() >= 0
        assert counts.max() <= spec.fleet_size

    load_columns = [f"load_{spec.name}_kw" for spec in fleet]
    np.testing.assert_allclose(profile["load_total_kw"], profile[load_columns].sum(axis=1))
    assert profile["load_total_kw"].max() > 0


@pytest.mark.skipif(not ENGINE_AVAILABLE, reason="withheld engine not decrypted")
def test_profile_is_reproducible_under_seed():
    fleet = load_fleet_config(EXAMPLE_CONFIG)
    first = build_demand_profile(fleet, TIME_GRID, seed=7)
    second = build_demand_profile(fleet, TIME_GRID, seed=7)
    np.testing.assert_array_equal(first["load_total_kw"], second["load_total_kw"])
