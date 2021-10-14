import cftime
from cfunits import Units
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


def normalize_time(model, freq):
    model_time = model["time"]
    norm_time = normalize_calendar(model_time, model_time.units, model_time.calendar)
    coarsened_time = coarsen_time(norm_time, freq)
    new_model = model.assign_coords({"time": coarsened_time})
    new_model["time"].attrs.update({"units": f"days since {REFERENCE_YEAR}-1-1",
                                    "calendar": REFERENCE_CALENDAR})
    return new_model


def normalize_calendar(time, units, calendar):
    this_origin = Units(units, calendar).reftime
    this_y, this_m, this_d, *_ = this_origin.timetuple()
    std_origin = cftime.datetime(this_y, this_m, this_d, calendar="360_day")
    diff = (std_origin - _REFERENCE_DATETIME).days
    return diff + time


def coarsen_time(time, freq):
    # reference calendar is 360_day
    scales = {
        "yr": 360,
        "mon": 30
    }
    scale_factor = scales[freq]
    return (time // scale_factor)*scale_factor


def regrid_model_group(model_group, lon, lat):
    res = []
    for model in model_group:
        regrided_model = cdo_remapcon_from_data(model, lon, lat)
        res.append(regrided_model)
    return res
