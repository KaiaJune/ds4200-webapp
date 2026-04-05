import pandas as pd
import plotly.express as px
import streamlit as st

# page setup
st.set_page_config(page_title="Streaming Scatter Heatmap", layout="wide")

st.markdown("## Streaming Time of Day vs Platform")
st.caption("Scatter-heatmap showing when users listen most across platforms")

# load data
@st.cache_data
def load_data():
    df = pd.read_csv("ds4200_global_streaming_cleaned (1).csv")

    # clean column names
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("/", "_")
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
        .str.replace("%", "percent", regex=False)
    )

    # clean categories
    df["streaming_platform"] = df["streaming_platform"].str.strip().str.title()
    df["country"] = df["country"].str.strip().str.title()
    df["listening_time_morning_afternoon_night"] = (
        df["listening_time_morning_afternoon_night"]
        .str.strip()
        .str.title()
    )

    return df

df = load_data()

# filters
st.sidebar.markdown("### filters")

countries = sorted(df["country"].unique())
selected_countries = st.sidebar.multiselect(
    "country",
    countries,
    default=countries
)

filtered = df[df["country"].isin(selected_countries)].copy()

platforms = sorted(filtered["streaming_platform"].unique())
selected_platforms = st.sidebar.multiselect(
    "platform",
    platforms,
    default=platforms
)

filtered = filtered[filtered["streaming_platform"].isin(selected_platforms)].copy()

if filtered.empty:
    st.warning("no data for this selection")
    st.stop()

# aggregate counts
scatter_data = (
    filtered.groupby([
        "streaming_platform",
        "listening_time_morning_afternoon_night"
    ])
    .size()
    .reset_index(name="count")
)

# fix order
time_order = ["Morning", "Afternoon", "Night"]
scatter_data["listening_time_morning_afternoon_night"] = pd.Categorical(
    scatter_data["listening_time_morning_afternoon_night"],
    categories=time_order,
    ordered=True
)

# sort platforms by usage (makes it cleaner)
platform_order = (
    scatter_data.groupby("streaming_platform")["count"]
    .sum()
    .sort_values(ascending=False)
    .index
)

# plot
fig = px.scatter(
    scatter_data,
    x="streaming_platform",
    y="listening_time_morning_afternoon_night",
    size="count",
    color="count",
    size_max=80,
    color_continuous_scale=[
        [0.0, "#dbeafe"],
        [0.5, "#3b82f6"],
        [1.0, "#1e3a8a"],
    ],
    category_orders={
        "streaming_platform": list(platform_order),
        "listening_time_morning_afternoon_night": time_order
    },
    labels={
        "streaming_platform": "platform",
        "listening_time_morning_afternoon_night": "time of day",
        "count": "users"
    }
)

# cleaner look
fig.update_traces(
    marker=dict(line=dict(width=1, color="white")),
    hovertemplate=(
        "platform: %{x}<br>"
        "time: %{y}<br>"
        "users: %{marker.size}<extra></extra>"
    )
)

fig.update_layout(
    height=550,
    margin=dict(l=20, r=20, t=40, b=20),
    template="plotly_white"
)

fig.update_xaxes(tickangle=-25, showgrid=False)
fig.update_yaxes(showgrid=False)

st.plotly_chart(fig, use_container_width=True)

# takeaway
st.markdown("### takeaway")
st.write(
    "circle size and color both represent user count. this makes it easy to compare "
    "which platforms have stronger listening activity at different times of day."
)
