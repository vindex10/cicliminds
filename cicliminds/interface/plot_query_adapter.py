from dataclasses import fields
from cicliminds_lib.plotting.config import RecipeConfig


class UnitFactorConverter:
    KEYWORDS = {
        "day": 1
    }

    @classmethod
    def from_json(cls, value):
        return cls.KEYWORDS.get(value, value)

    @classmethod
    def to_json(cls, value):
        for k, v in cls.KEYWORDS.items():
            # compare for precise match. 1 should not match np.timdelta64(1, 'D')
            if type(v) == type(value) and v == value:  # pylint: disable=unidiomatic-typecheck
                return k
        return value


class PlotQueryAdapter:
    INTERNAL_FIELDS = ["init_year"]
    CONVERTERS = {
        "unit_factor": UnitFactorConverter
    }

    @classmethod
    def from_json(cls, plot_query, restrictive=True):
        res = {}
        config_fields = list(f.name for f in fields(RecipeConfig))
        for k, v in plot_query.items():
            if restrictive and k not in config_fields:
                continue
            converter = cls.CONVERTERS.get(k)
            try:
                val = plot_query[k]
            except KeyError:
                continue
            if converter is not None:
                val = converter.from_json(v)
            res[k] = val
        return res

    @classmethod
    def to_json(cls, plot_config_patch, restrictive=True):
        res = {}
        config_fields = list(f.name for f in fields(RecipeConfig))
        for k, v in plot_config_patch.items():
            if restrictive and k not in config_fields:
                continue
            if k in cls.INTERNAL_FIELDS:
                continue
            converter = cls.CONVERTERS.get(k)
            val = v
            if converter is not None:
                val = converter.to_json(v)
            res[k] = val
        return res
