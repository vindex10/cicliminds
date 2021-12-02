import numpy as np
import cftime
from cicliminds_lib.bindings import cdo_remapcon_from_data

REFERENCE_YEAR = 1800
REFERENCE_CALENDAR = "360_day"
_REFERENCE_DATETIME = cftime.datetime(REFERENCE_YEAR, 1, 1, calendar=REFERENCE_CALENDAR)


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
    for model in model_group:
        lat_dims.append(model.lat.shape[0])
        lon_dims.append(model.lon.shape[0])
    return min(lon_dims), min(lat_dims)


def normalize_calendar(model, freq):
    model_time = model["time"]
    norm_time = normalize_calendar_series(model_time, model_time.units, model_time.calendar)
    new_model = model.assign_coords({"time": norm_time})
    new_model["time"].attrs.update({"units": f"days since {REFERENCE_YEAR}-1-1",
                                    "calendar": REFERENCE_CALENDAR})
    return new_model


def normalize_calendar_series(time, units, calendar):
    this_origin = cftime.num2date(time[0], units=units, calendar=calendar)
    this_y, this_m, this_d, *_ = this_origin.timetuple()
    std_origin = cftime.datetime(this_y, this_m, this_d, calendar="360_day")
    diff = (std_origin - _REFERENCE_DATETIME).days
    return diff + time - time[0]


def align_time_axes(models, init_days, time_dim):
    res = []
    for model in models:
        new_model = model.sel(time=slice(init_days, None))
        new_model = new_model.isel(time=slice(None, time_dim))
        res.append(new_model)
    return res


def infer_common_time_axis(time_axes):
    inits = [time_axis[0] for time_axis in time_axes]
    init_days = np.quantile(inits, 0.3)
    time_dims = []
    for time_axis in time_axes:
        time_dims.append(time_axis[time_axis >= init_days].shape[0])
    time_dim = np.min(time_dims)
    return init_days, time_dim


def regrid_dataset_group(dataset_group, lon, lat):
    res = []
    for dataset in dataset_group:
        cur_lon, cur_lat = dataset.lon.shape[0], dataset.lat.shape[0]
        if (cur_lon == lon) and (cur_lat == lat):
            res.append(dataset)
            continue
        regrided_dataset = cdo_remapcon_from_data(dataset, lon, lat)
        res.append(regrided_dataset)
    return res
