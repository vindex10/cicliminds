from cicliminds_lib.bindings import cdo_remapcon_from_data


def safe_drop_bounds(dataset, fields):
    to_drop = []
    for field in fields:
        try:
            bound_name = getattr(dataset, field).bounds
            to_drop.append(bound_name)
        except AttributeError:
            pass
    return dataset.drop_vars(to_drop)


def get_coarsest_grid(model_group):
    lon_dims = []
    lat_dims = []
    time_dims = []
    for model in model_group:
        lat_dims.append(model.lat.shape[0])
        lon_dims.append(model.lon.shape[0])
        time_dims.append(model.time.shape[0])
    return min(time_dims), min(lon_dims), min(lat_dims)


def unify_models_times(model_group, timeslice):
    res = []
    first_time = model_group[0].isel(time=timeslice).time
    for model in model_group:
        new = model.isel(time=timeslice).copy()
        new["time"] = first_time
        res.append(new)
    return res


def regrid_model_group(model_group, lon, lat):
    res = []
    for model in model_group:
        regrided_model = cdo_remapcon_from_data(model, lon, lat)
        res.append(regrided_model)
    return res
