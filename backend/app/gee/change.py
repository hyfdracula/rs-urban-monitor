"""Year-over-year change calculations for GEE results."""

from __future__ import annotations


def compute_change_partial(yearly_results: dict, years: list[int], indicators: list[str]) -> dict:
    """Calculate change metrics for selected indicators only."""
    first_year = years[0]
    last_year = years[-1]
    first = yearly_results.get(first_year, {})
    last = yearly_results.get(last_year, {})

    change = {
        "first_year": first_year,
        "last_year": last_year,
    }

    if "construction" in indicators:
        built_first = first.get("built_area_km2", 0)
        built_last = last.get("built_area_km2", 0)
        change["new_built_area"] = round(built_last - built_first, 2)
        if built_first > 0 and last_year > first_year:
            cagr = ((built_last / built_first) ** (1 / (last_year - first_year)) - 1) * 100
            change["expansion_rate"] = round(cagr, 2)
        else:
            change["expansion_rate"] = 0.0
        change["built_first"] = built_first
        change["built_last"] = built_last
    else:
        change["new_built_area"] = 0
        change["expansion_rate"] = 0.0
        change["built_first"] = 0
        change["built_last"] = 0

    if "rsei" in indicators:
        rsei_first = first.get("rsei_mean", 0)
        rsei_last = last.get("rsei_mean", 0)
        change["rsei_change"] = round(rsei_last - rsei_first, 4)
    else:
        change["rsei_change"] = 0

    if "population" in indicators:
        pop_first = first.get("population", 0)
        pop_last = last.get("population", 0)
        change["pop_growth_rate"] = round(((pop_last / max(pop_first, 1)) - 1) * 100, 2) if pop_first > 0 else None
    else:
        change["pop_growth_rate"] = None

    if "nightLight" in indicators:
        ntl_first = first.get("ntl_sum")
        ntl_last = last.get("ntl_sum")
        ntl_change = None
        if ntl_first and ntl_last and ntl_first > 0:
            ntl_change = round(((ntl_last / ntl_first) - 1) * 100, 2)
        change["ntl_change_rate"] = ntl_change
    else:
        change["ntl_change_rate"] = None

    return change


def compute_change(yearly_results: dict, years: list[int]) -> dict:
    """Calculate full change metrics across the selected years."""
    first_year = years[0]
    last_year = years[-1]
    first = yearly_results.get(first_year, {})
    last = yearly_results.get(last_year, {})

    built_first = first.get("built_area_km2", 0)
    built_last = last.get("built_area_km2", 0)
    new_built = round(built_last - built_first, 2)

    if built_first > 0 and last_year > first_year:
        cagr = ((built_last / built_first) ** (1 / (last_year - first_year)) - 1) * 100
        expansion_rate = round(cagr, 2)
    else:
        expansion_rate = 0.0

    rsei_first = first.get("rsei_mean", 0)
    rsei_last = last.get("rsei_mean", 0)
    rsei_change = round(rsei_last - rsei_first, 4)

    pop_first = first.get("population", 0)
    pop_last = last.get("population", 0)
    pop_growth = round(((pop_last / max(pop_first, 1)) - 1) * 100, 2) if pop_first > 0 else None

    ntl_first = first.get("ntl_sum")
    ntl_last = last.get("ntl_sum")
    ntl_change = None
    if ntl_first and ntl_last and ntl_first > 0:
        ntl_change = round(((ntl_last / ntl_first) - 1) * 100, 2)

    return {
        "first_year": first_year,
        "last_year": last_year,
        "new_built_area": new_built,
        "expansion_rate": expansion_rate,
        "rsei_change": rsei_change,
        "pop_growth_rate": pop_growth,
        "ntl_change_rate": ntl_change,
        "built_first": built_first,
        "built_last": built_last,
    }
