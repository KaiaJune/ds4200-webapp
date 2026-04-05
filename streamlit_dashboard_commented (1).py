# =========================================================
# DS4200 PROJECT
# Advanced Streaming Behavior Dashboard
#
# This Streamlit app compares Free vs Premium listeners by:
# 1. Minutes Streamed Per Day
# 2. Repeat Song Rate (%)
#
# Filters:
# - Age Group
# - Top Genre
#
# Why streamlit?
# - It avoids overly broad trends
# - It lets the user focus on a subgroup
# - It combines distribution + relationship analysis
# =========================================================

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ---------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------
st.set_page_config(
    page_title="Streaming Behavior Dashboard",
    page_icon="🎧",
    layout="wide"
)

# Small CSS block to make the page look more polished
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .subtext {
        font-size: 1rem;
        color: #555555;
        margin-bottom: 1rem;
    }
    .insight-box {
        padding: 1rem;
        border-radius: 0.75rem;
        background-color: #f7f9fc;
        border: 1px solid #e6eaf0;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🎧 Advanced Streaming Behavior Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtext">Compare Free and Premium listeners across daily listening time and repeat behavior. '
    'Use the filters to focus on a specific age group and genre.</div>',
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# LOAD AND CLEAN DATA
# ---------------------------------------------------------
@st.cache_data
def load_data():
    """
    Load the CSV and clean column names so they are easier to use in code.
    Also creates age groups for filtering.
    """
    df = pd.read_csv("ds4200_global_streaming_cleaned (1).csv")

    # Standardize column names
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("/", "_")
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
        .str.replace("%", "percent", regex=False)
    )

    # Create grouped age categories
    bins = [10, 18, 25, 35, 45, 60, 101]
    labels = ["Teen", "18-25", "26-35", "36-45", "46-60", "60+"]
    df["age_group"] = pd.cut(df["age"], bins=bins, labels=labels, right=False)

    # Keep only the columns needed for this dashboard
    df = df[
        [
            "subscription_type",
            "minutes_streamed_per_day",
            "repeat_song_rate_percent",
            "top_genre",
            "age_group",
        ]
    ].dropna()

    # Standardize string formatting
    df["subscription_type"] = df["subscription_type"].astype(str).str.title()
    df["top_genre"] = df["top_genre"].astype(str).str.title()
    df["age_group"] = df["age_group"].astype(str)

    return df


df = load_data()

# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------
st.sidebar.header("Filters")

age_order = ["Teen", "18-25", "26-35", "36-45", "46-60", "60+"]
age_groups = [a for a in age_order if a in df["age_group"].unique()]
genres = sorted(df["top_genre"].unique())

selected_age = st.sidebar.selectbox(
    "Select Age Group",
    age_groups,
    index=0
)

default_genre_index = genres.index("Metal") if "Metal" in genres else 0
selected_genre = st.sidebar.selectbox(
    "Select Genre",
    genres,
    index=default_genre_index
)

# ---------------------------------------------------------
# FILTER DATA
# ---------------------------------------------------------
filtered = df[
    (df["age_group"] == selected_age) &
    (df["top_genre"] == selected_genre)
].copy()

if filtered.empty:
    st.warning("No data is available for this age group and genre combination.")
    st.stop()

# ---------------------------------------------------------
# SUMMARY METRICS
# ---------------------------------------------------------
free_count = (filtered["subscription_type"] == "Free").sum()
premium_count = (filtered["subscription_type"] == "Premium").sum()
avg_minutes = filtered["minutes_streamed_per_day"].mean()
avg_repeat = filtered["repeat_song_rate_percent"].mean()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Filtered Users", len(filtered))
m2.metric("Free Users", int(free_count))
m3.metric("Avg Minutes", f"{avg_minutes:.1f}")
m4.metric("Avg Repeat Rate", f"{avg_repeat:.1f}%")

# ---------------------------------------------------------
# BUILD FIGURE
# ---------------------------------------------------------
fig = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=(
        "Minutes Streamed per Day by Subscription",
        "Minutes Streamed vs Repeat Song Rate"
    ),
    horizontal_spacing=0.12
)

# Fixed seed keeps jitter stable every time the app reruns
rng = np.random.default_rng(42)

# Colors chosen to keep the two subscription types visually distinct
subscription_styles = {
    "Free": "#3b82f6",
    "Premium": "#84cc16"
}

for subscription, color in subscription_styles.items():
    sub_df = filtered[filtered["subscription_type"] == subscription].copy()

    # ---------------- LEFT PANEL ----------------
    # Boxplot showing spread of minutes streamed
    fig.add_trace(
        go.Box(
            y=sub_df["minutes_streamed_per_day"],
            x=[subscription] * len(sub_df),
            name=subscription,
            marker_color="#76c7c0",
            boxpoints=False,
            showlegend=False,
            hovertemplate=(
                f"Subscription={subscription}<br>"
                "Minutes=%{y:.0f}<extra></extra>"
            )
        ),
        row=1,
        col=1
    )

    # Jittered points on top of the boxplot
    # This helps show individual data points without complete overlap
    x_center = 0 if subscription == "Free" else 1
    jitter = rng.normal(0, 0.08, len(sub_df))
    fig.add_trace(
        go.Scatter(
            x=np.full(len(sub_df), x_center) + jitter,
            y=sub_df["minutes_streamed_per_day"],
            mode="markers",
            marker=dict(size=7, color=color, opacity=0.45),
            name=subscription,
            legendgroup=subscription,
            showlegend=True,
            hovertemplate=(
                f"Subscription={subscription}<br>"
                "Minutes=%{y:.0f}<br>"
                f"Genre={selected_genre}<br>"
                f"Age Group={selected_age}<extra></extra>"
            )
        ),
        row=1,
        col=1
    )

    # ---------------- RIGHT PANEL ----------------
    # Scatterplot showing relationship between minutes streamed and repeat rate
    fig.add_trace(
        go.Scatter(
            x=sub_df["minutes_streamed_per_day"],
            y=sub_df["repeat_song_rate_percent"],
            mode="markers",
            marker=dict(size=8, color=color, opacity=0.6),
            name=f"{subscription} points",
            legendgroup=subscription,
            showlegend=False,
            hovertemplate=(
                f"Subscription={subscription}<br>"
                "Minutes=%{x:.0f}<br>"
                "Repeat Rate=%{y:.1f}%<br>"
                f"Genre={selected_genre}<br>"
                f"Age Group={selected_age}<extra></extra>"
            )
        ),
        row=1,
        col=2
    )

    # Add a linear regression trend line when possible
    if len(sub_df) >= 2:
        x = sub_df["minutes_streamed_per_day"].to_numpy()
        y = sub_df["repeat_song_rate_percent"].to_numpy()

        slope, intercept = np.polyfit(x, y, 1)
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = slope * x_line + intercept

        fig.add_trace(
            go.Scatter(
                x=x_line,
                y=y_line,
                mode="lines",
                line=dict(color=color, width=3),
                name=f"{subscription} trend",
                legendgroup=subscription,
                showlegend=False,
                hoverinfo="skip"
            ),
            row=1,
            col=2
        )

# ---------------------------------------------------------
# FINAL FIGURE FORMATTING
# ---------------------------------------------------------
fig.update_layout(
    height=560,
    template="plotly_white",
    title=dict(
        text=(
            "Streaming Behavior by Subscription Type"
            f"<br><sup>Age Group: {selected_age} | Genre: {selected_genre}</sup>"
        ),
        x=0.5
    ),
    legend=dict(
        orientation="h",
        x=0.4,
        y=1.08
    ),
    margin=dict(t=100, l=40, r=40, b=40)
)

# Left chart axes
fig.update_xaxes(
    row=1,
    col=1,
    tickmode="array",
    tickvals=[0, 1],
    ticktext=["Free", "Premium"],
    title_text="Subscription Type"
)
fig.update_yaxes(
    row=1,
    col=1,
    title_text="Minutes Streamed Per Day"
)

# Right chart axes
fig.update_xaxes(
    row=1,
    col=2,
    title_text="Minutes Streamed Per Day"
)
fig.update_yaxes(
    row=1,
    col=2,
    title_text="Repeat Song Rate (%)"
)

# ---------------------------------------------------------
# SHOW CHART
# ---------------------------------------------------------
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# INTERPRETATION / WRITE-UP SECTION
# ---------------------------------------------------------
st.subheader("Interpretation")

st.markdown(f"""
<div class="insight-box">
This dashboard focuses on <b>{selected_age}</b> listeners whose top genre is <b>{selected_genre}</b>.

The left chart compares the distribution of <b>minutes streamed per day</b> between Free and Premium users.
The right chart shows whether users who stream more also tend to have a higher <b>repeat song rate</b>.

Filtering by age group and genre makes the visualization more specific and easier to interpret than a broad, unfiltered comparison.
</div>
""", unsafe_allow_html=True)

st.subheader("Suggested report language")
st.write(
    "After filtering by age group and genre, the visualization provides a more targeted comparison of streaming behavior "
    "between Free and Premium users. The boxplot highlights differences in daily listening time, while the scatterplot "
    "shows how minutes streamed per day relate to repeat song rate within the selected subgroup. This focused view makes "
    "behavioral patterns easier to interpret than an aggregate plot across all users."
)
