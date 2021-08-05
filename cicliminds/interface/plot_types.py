from cicliminds_lib.plotting.recipes.means_of_hists import MeansOfHistsRecipe
from cicliminds_lib.plotting.recipes.means_of_hists import MeansOfHistsDiffRecipe
from cicliminds_lib.plotting.recipes.hists_of_means import HistsOfMeansRecipe
from cicliminds_lib.plotting.recipes.hists_of_means import HistsOfMeansDiffRecipe
from cicliminds_lib.plotting.recipes.timeavgs import HistOfTimeavgsRecipe
from cicliminds_lib.plotting.recipes.timeavgs import HistOfTimeavgsDiffRecipe

PLOT_TYPES_SPEC = {
    "fldmean first": [HistsOfMeansRecipe, HistsOfMeansDiffRecipe],
    "fldmean last": [MeansOfHistsRecipe, MeansOfHistsDiffRecipe],
    "avg time": [HistOfTimeavgsRecipe, HistOfTimeavgsDiffRecipe]
}


def get_plot_recipe_by_query(plot_query):
    plot_recipe = PLOT_TYPES_SPEC[plot_query["plot_type"]][int(plot_query["subtract_reference"])]
    return plot_recipe
