from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

# from codegreen_core.tools.carbon_intensity import calculate_from_energy_data
# from codegreen_core.tools.carbon_emission import calculate_carbon_footprint_job
from codegreen_core.data import energy
from codegreen_core.tools.loadshift_time import predict_optimal_time
import matplotlib.dates as mdates

Color = {
    "red": "#D6A99A",
    "green": "#99D19C",
    "blue": "#3DA5D9",
    "yellow": "#E2C044",
    "black": "#0F1A20",
}


def plot_percentage_clean(df, country, save_fig_path=None):
    df["startTimeUTC"] = pd.to_datetime(df["startTimeUTC"])
    df["percentNonRenewable"] = round(
        ((df["total"] - df["renewableTotal"]) / df["total"]) * 100
    )

    df["hour"] = df["startTimeUTC"].dt.strftime("%H:%M")

    date_start = df["startTimeUTC"].min().strftime("%Y-%m-%d")
    date_end = df["startTimeUTC"].max().strftime("%Y-%m-%d")
    time_range_label = f"Time ({date_start} - {date_end})"

    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 4))

    # Bar width
    bar_width = 0.85
    bar_positions = range(len(df))

    # Plot each bar
    for i, (index, row) in enumerate(df.iterrows()):
        hour = row["hour"]
        renewable = row["percentRenewable"]
        non_renewable = row["percentNonRenewable"]

        # Plotting bars for renewable and non-renewable
        ax.bar(i, renewable, bar_width, color=Color["green"], edgecolor=Color["green"])
        ax.bar(
            i,
            non_renewable,
            bar_width,
            bottom=renewable,
            color=Color["red"],
            edgecolor=Color["red"],
        )

    # Set x-ticks to be the hours

    if len(df) > 74:
        ax.set_xticks([])  # Hide x-ticks if too many entries
        ax.set_xlabel("")  # Remove x-label if too many entries
    else:
        ax.set_xticks(bar_positions)
        ax.set_xticklabels(df["hour"], rotation=90, fontsize=7)
    ax.set_xlabel(time_range_label)

    ax.set_ylabel("Percentage")
    ax.set_title(
        "Energy Generation Breakdown: Renewable and Non-Renewable by Hour ("
        + country
        + ")"
    )
    # ax.legend()

    if save_fig_path:
        plt.savefig(save_fig_path, dpi=300, bbox_inches="tight")

    plt.tight_layout()
    plt.show()


def plot_multiple_percentage_clean(dfs, labels, save_fig_path=None):
    num_dfs = len(dfs)
    num_cols = 2  # Number of columns in the subplot grid
    num_rows = (num_dfs + num_cols - 1) // num_cols  # Compute number of rows needed

    fig, axes = plt.subplots(
        num_rows, num_cols, figsize=(15 * num_rows, 5 * num_rows), squeeze=False
    )
    fig.suptitle(
        "Energy Generation Breakdown: Renewable and Non-Renewable by Hour",
        fontsize=17,
        y=1,
    )  # Adjust y for positioning
    # Flatten the axes array for easy iteration
    axes = axes.flatten()

    for i, (df, label) in enumerate(zip(dfs, labels)):
        ax = axes[i]

        # Ensure 'startTimeUTC' is in datetime format
        df["startTimeUTC"] = pd.to_datetime(df["startTimeUTC"])
        df["percentNonRenewable"] = round(
            ((df["total"] - df["renewableTotal"]) / df["total"]) * 100
        )
        df["hour"] = df["startTimeUTC"].dt.strftime("%H:%M")

        date_start = df["startTimeUTC"].min().strftime("%Y-%m-%d")
        date_end = df["startTimeUTC"].max().strftime("%Y-%m-%d")
        time_range_label = f"Time ({date_start} - {date_end})"

        # Bar width
        bar_width = 0.85
        bar_positions = range(len(df))

        # Plot each bar
        for index, row in df.iterrows():
            hour = row["hour"]
            renewable = row["percentRenewable"]
            non_renewable = row["percentNonRenewable"]

            # Plotting bars for renewable and non-renewable
            ax.bar(
                index,
                renewable,
                bar_width,
                color=Color["green"],
                edgecolor=Color["green"],
            )
            ax.bar(
                index,
                non_renewable,
                bar_width,
                bottom=renewable,
                color=Color["red"],
                edgecolor=Color["red"],
            )

        # Set x-ticks to be the hours

        if len(df) > 74:
            ax.set_xticks([])  # Hide x-ticks if too many entries
            ax.set_xlabel("")  # Remove x-label if too many entries
        else:
            ax.set_xticks(bar_positions)
            ax.set_xticklabels(df["hour"], rotation=90, fontsize=7)

        ax.set_xlabel(time_range_label)
        ax.set_ylabel("Percentage")
        ax.set_title(label)

    # Hide any unused subplots
    for j in range(i + 1, len(axes)):
        axes[j].axis("off")

    if save_fig_path:
        plt.savefig(save_fig_path, dpi=300, bbox_inches="tight")
    plt.tight_layout()
    plt.show()


def show_clean_energy(country, start, end, save_fig_path=None):
    """note that these plots are based on actual energy production and not the forecasts"""
    d = energy(country, start, end)
    actual1 = d["data"]
    plot_percentage_clean(actual1, country, save_fig_path)


def show_clean_energy_multiple(countries, start, end, save_fig_path=None):
    data = []
    for c in countries:
        data.append(energy(c, start, end)["data"])
    plot_multiple_percentage_clean(data, countries, save_fig_path)
