from cicliminds_lib.plotting.recipes.means_of_hists import MeansOfHistsRecipe
from cicliminds_lib.plotting.recipes.means_of_hists import MeansOfHistsDiffRecipe
from cicliminds_lib.plotting.recipes.hists_of_means import HistsOfMeansRecipe
from cicliminds_lib.plotting.recipes.hists_of_means import HistsOfMeansDiffRecipe
from cicliminds_lib.plotting.recipes.mean_val import MeanValRecipe
from cicliminds_lib.plotting.recipes.mean_val import MeanValDiffRecipe
from cicliminds_lib.plotting.recipes.time_series import TimeSeriesRecipe
from cicliminds_lib.plotting.recipes.time_series import TimeSeriesDiffRecipe

PLOT_TYPES_SPEC = {
    "fldmean first": [HistsOfMeansRecipe, HistsOfMeansDiffRecipe],
    "fldmean last": [MeansOfHistsRecipe, MeansOfHistsDiffRecipe],
    "mean val": [MeanValRecipe, MeanValDiffRecipe],
    "time series": [TimeSeriesRecipe, TimeSeriesDiffRecipe]
}


def get_plot_recipe_by_query(plot_query):
    plot_recipe = PLOT_TYPES_SPEC[plot_query["plot_type"]][int(plot_query["subtract_reference"])]
    return plot_recipe
