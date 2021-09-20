def apply_scenario_filter(datasets, mask, scenarios):
    new_mask = mask.copy()
    scenarios_set = set(scenarios)
    columns_without_scenario = [i for i in datasets.columns if i not in ["scenario", "timespan"]]
    for _, group in datasets[mask].groupby(columns_without_scenario):
        group_scenarios = set(group["scenario"].values)
        if not scenarios_set - group_scenarios:
            continue
        new_mask[group.index] = False
    return new_mask


def get_scenario_pairs(scenarios):
    if "historical" not in scenarios:
        return [[scenario] for scenario in scenarios]
    if len(scenarios) == 1:
        return [["historical"]]
    return [["historical", scenario] for scenario in scenarios if scenario != "historical"]
