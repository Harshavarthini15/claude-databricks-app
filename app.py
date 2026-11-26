"""World Explorer - a Databricks App built with Dash and Plotly.

Uses plotly's built-in gapminder dataset (bundled with plotly, no network needed).
"""

import os

import dash
import pandas as pd
import plotly.express as px
from dash import Input, Output, dcc, html

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
df = px.data.gapminder()
YEARS = sorted(df["year"].unique())
CONTINENTS = sorted(df["continent"].unique())
ALL = "All"

CONTINENT_COLORS = {
    "Africa": "#2a78d6",
    "Americas": "#e07b39",
    "Asia": "#1f9e89",
    "Europe": "#8e5ad6",
    "Oceania": "#d6457a",
}

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
BG = "#f5f7fb"
CARD_BG = "#ffffff"
TEXT = "#1f2937"
MUTED = "#6b7280"
ACCENT = "#2a78d6"

CARD_STYLE = {
    "backgroundColor": CARD_BG,
    "borderRadius": "14px",
    "boxShadow": "0 1px 3px rgba(16,24,40,0.06), 0 1px 2px rgba(16,24,40,0.04)",
    "border": "1px solid #e5e7eb",
    "padding": "20px 24px",
}


def kpi_card(label, value_id):
    return html.Div(
        style={**CARD_STYLE, "flex": "1", "minWidth": "200px"},
        children=[
            html.Div(
                label,
                style={
                    "fontSize": "13px",
                    "fontWeight": 600,
                    "color": MUTED,
                    "textTransform": "uppercase",
                    "letterSpacing": "0.04em",
                },
            ),
            html.Div(
                id=value_id,
                style={
                    "fontSize": "32px",
                    "fontWeight": 700,
                    "color": TEXT,
                    "marginTop": "6px",
                },
            ),
        ],
    )


def style_figure(fig, title):
    fig.update_layout(
        title={"text": title, "x": 0, "xanchor": "left",
               "font": {"size": 16, "color": TEXT}},
        font={"family": FONT, "color": TEXT, "size": 12},
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        margin={"l": 60, "r": 20, "t": 60, "b": 50},
        legend={"title": None, "orientation": "h", "y": -0.22, "x": 0},
        hoverlabel={"font_family": FONT},
    )
    fig.update_xaxes(showgrid=True, gridcolor="#eef0f4", zeroline=False, linecolor="#d1d5db")
    fig.update_yaxes(showgrid=True, gridcolor="#eef0f4", zeroline=False, linecolor="#d1d5db")
    return fig


# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------
app = dash.Dash(__name__, title="World Explorer")
app.index_string = app.index_string.replace("<head>", "<head><style>body{margin:0}</style>", 1)
server = app.server

app.layout = html.Div(
    style={"backgroundColor": BG, "minHeight": "100vh", "fontFamily": FONT,
           "color": TEXT, "padding": "32px 40px"},
    children=[
        html.Div(
            style={"maxWidth": "1280px", "margin": "0 auto"},
            children=[
                # Header
                html.Div(
                    style={"marginBottom": "24px"},
                    children=[
                        html.H1("World Explorer",
                                style={"margin": 0, "fontSize": "28px", "fontWeight": 700}),
                        html.P(
                            "Life expectancy, wealth and population across the world "
                            "(Gapminder, 1952–2007).",
                            style={"margin": "6px 0 0", "color": MUTED},
                        ),
                    ],
                ),
                # Controls
                html.Div(
                    style={**CARD_STYLE, "display": "flex", "gap": "32px",
                           "alignItems": "center", "flexWrap": "wrap",
                           "marginBottom": "20px"},
                    children=[
                        html.Div(
                            style={"width": "240px"},
                            children=[
                                html.Label("Continent", style={"fontWeight": 600,
                                                               "fontSize": "13px",
                                                               "color": MUTED}),
                                dcc.Dropdown(
                                    id="continent",
                                    options=[{"label": ALL, "value": ALL}]
                                    + [{"label": c, "value": c} for c in CONTINENTS],
                                    value=ALL,
                                    clearable=False,
                                    style={"marginTop": "6px"},
                                ),
                            ],
                        ),
                        html.Div(
                            style={"flex": "1", "minWidth": "320px"},
                            children=[
                                html.Label("Year", style={"fontWeight": 600,
                                                          "fontSize": "13px",
                                                          "color": MUTED}),
                                dcc.Slider(
                                    id="year",
                                    min=min(YEARS),
                                    max=max(YEARS),
                                    step=None,
                                    value=max(YEARS),
                                    marks={int(y): str(y) for y in YEARS},
                                ),
                            ],
                        ),
                    ],
                ),
                # KPI cards
                html.Div(
                    style={"display": "flex", "gap": "20px", "flexWrap": "wrap",
                           "marginBottom": "20px"},
                    children=[
                        kpi_card("Countries", "kpi-countries"),
                        kpi_card("Avg. life expectancy", "kpi-life"),
                        kpi_card("Total population", "kpi-pop"),
                    ],
                ),
                # Charts
                html.Div(
                    style={"display": "grid",
                           "gridTemplateColumns": "repeat(auto-fit, minmax(480px, 1fr))",
                           "gap": "20px"},
                    children=[
                        html.Div(style={**CARD_STYLE, "padding": "8px"},
                                 children=dcc.Graph(id="bubble", config={"displaylogo": False},
                                                    style={"height": "460px"})),
                        html.Div(style={**CARD_STYLE, "padding": "8px"},
                                 children=dcc.Graph(id="trend", config={"displaylogo": False},
                                                    style={"height": "460px"})),
                    ],
                ),
            ],
        )
    ],
)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
def format_population(n):
    for threshold, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= threshold:
            return f"{n / threshold:.2f}{suffix}"
    return f"{n:,.0f}"


def filter_continent(continent):
    return df if continent == ALL else df[df["continent"] == continent]


@app.callback(
    Output("kpi-countries", "children"),
    Output("kpi-life", "children"),
    Output("kpi-pop", "children"),
    Output("bubble", "figure"),
    Output("trend", "figure"),
    Input("continent", "value"),
    Input("year", "value"),
)
def update(continent, year):
    scoped = filter_continent(continent)
    snapshot = scoped[scoped["year"] == year]

    countries = snapshot["country"].nunique()
    avg_life = snapshot["lifeExp"].mean()
    total_pop = snapshot["pop"].sum()

    bubble = px.scatter(
        snapshot,
        x="gdpPercap",
        y="lifeExp",
        size="pop",
        color="continent",
        hover_name="country",
        log_x=True,
        size_max=55,
        color_discrete_map=CONTINENT_COLORS,
        category_orders={"continent": CONTINENTS},
        labels={"gdpPercap": "GDP per capita (USD, log scale)",
                "lifeExp": "Life expectancy (years)",
                "pop": "Population", "continent": "Continent"},
    )
    bubble.update_traces(marker={"line": {"width": 0.5, "color": "white"}, "opacity": 0.85})
    style_figure(bubble, f"Wealth vs. health, {year}")

    if continent == ALL:
        trend_df = scoped.groupby(["year", "continent"], as_index=False)["lifeExp"].mean()
        world = scoped.groupby("year", as_index=False)["lifeExp"].mean()
        world["continent"] = "World"
        trend_df = pd.concat([trend_df, world], ignore_index=True)
    else:
        trend_df = scoped.groupby(["year", "continent"], as_index=False)["lifeExp"].mean()

    trend = px.line(
        trend_df,
        x="year",
        y="lifeExp",
        color="continent",
        markers=True,
        color_discrete_map={**CONTINENT_COLORS, "World": "#111827"},
        labels={"year": "Year", "lifeExp": "Avg. life expectancy (years)",
                "continent": "Continent"},
    )
    trend.update_traces(line={"width": 2.5})
    trend.update_traces(selector={"name": "World"}, line={"width": 3.5, "dash": "dot"})
    trend.add_vline(x=year, line_width=1, line_dash="dash", line_color=MUTED)
    style_figure(trend, "Average life expectancy over time")

    return (
        f"{countries:,}",
        f"{avg_life:.1f} yrs",
        format_population(total_pop),
        bubble,
        trend,
    )


if __name__ == "__main__":
    port = int(os.environ.get("DATABRICKS_APP_PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
