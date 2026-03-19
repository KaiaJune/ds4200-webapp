import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

# Load dataset (from your repo)
df = pd.read_csv("ds4200_global_streaming_cleaned.csv")

# Keep only necessary columns
df = df[['Age', 'Top Genre', 'Most Played Artist']]

# Get top 10 artists
top_artists = df['Most Played Artist'].value_counts().nlargest(10).index.tolist()
df = df[df['Most Played Artist'].isin(top_artists)]

# Pre-aggregate counts
agg = df.groupby(['Most Played Artist', 'Age', 'Top Genre']).size().reset_index(name='Count')

# Start with the first artist
initial_artist = top_artists[0]
artist_data = agg[agg['Most Played Artist'] == initial_artist]

# Min/max ages for slider
age_min = int(df['Age'].min())
age_max = int(df['Age'].max())

# Create figure
fig = go.Figure()

genres = artist_data['Top Genre'].unique()
for genre in genres:
    genre_data = artist_data[artist_data['Top Genre'] == genre]
    fig.add_trace(go.Scatter(
        x=genre_data['Age'],
        y=genre_data['Count'],
        mode='lines+markers',
        name=genre
    ))

# Sliders
steps = []
for age in range(age_min, age_max + 1):
    step_data = []
    filtered = artist_data[artist_data['Age'] <= age]
    for genre in genres:
        genre_filtered = filtered[filtered['Top Genre'] == genre]
        step_data.append(genre_filtered['Count'].tolist())
    steps.append(dict(
        method="restyle",
        args=[{"y": step_data}],
        label=str(age)
    ))

sliders = [dict(
    active=0,
    currentvalue={"prefix": "Max Age: "},
    pad={"t": 50},
    steps=steps
)]

# Dropdown for artists
dropdown_buttons = []
for artist in top_artists:
    artist_filtered = agg[agg['Most Played Artist'] == artist]
    genres_artist = artist_filtered['Top Genre'].unique()
    y_data = [artist_filtered[artist_filtered['Top Genre'] == g]['Count'].tolist() for g in genres_artist]

    dropdown_buttons.append(dict(
        label=artist,
        method="restyle",
        args=[{"y": y_data, "name": list(genres_artist)}]
    ))

# Layout
fig.update_layout(
    title={"text": "Understanding the Age and Genre Profile of an Artist’s Audience", "x":0.5},
    xaxis=dict(title="Age"),
    yaxis=dict(title="Number of Listeners"),
    updatemenus=[dict(
        buttons=dropdown_buttons,
        direction="down",
        x=0.5,
        xanchor="center",
        y=1.15,
        yanchor="top"
    )],
    sliders=sliders,
    margin=dict(t=150, r=150, b=80)
)

# Save **full HTML** for iframe
pio.write_html(
    fig,
    file="genre_by_age_interactive.html",
    full_html=True,       # ✅ critical for iframe
    include_plotlyjs="cdn",
    auto_open=True
)
