import matplotlib.pyplot as plt


def set_plt_reasonable_defaults():
    plt.rcParams["figure.figsize"] = (12, 8)
    plt.rcParams['figure.constrained_layout.use'] = True
    plt.rcParams["xtick.direction"] = "in"
    plt.rcParams["xtick.major.size"] = 8
    plt.rcParams["xtick.major.width"] = 1.6
    plt.rcParams["xtick.minor.width"] = 0.8
    plt.rcParams["xtick.minor.size"] = 4
    plt.rcParams["ytick.direction"] = "in"
    plt.rcParams["ytick.major.width"] = 1.6
    plt.rcParams["ytick.minor.width"] = 0.8
    plt.rcParams["ytick.major.size"] = 8
    plt.rcParams["ytick.minor.size"] = 4
    plt.rcParams["font.size"] = 16
    plt.rcParams["lines.linewidth"] = 3
    plt.rcParams["lines.markersize"] = 5
    plt.rcParams["savefig.dpi"] = 300/2.4
    plt.rcParams["savefig.transparent"] = False
    plt.rcParams["savefig.facecolor"] = "white"
