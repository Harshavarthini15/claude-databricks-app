"""World Explorer - a Databricks App built with Dash and Plotly.

Tab 1 "Gapminder": plotly's built-in gapminder dataset (bundled, no network needed).
Tab 2 "Databricks Data": live aggregates from samples.nyctaxi.trips, queried through
the SQL warehouse attached to the app under the resource key "sql-warehouse".
"""

import logging
import os
import threading
import time

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


def kpi_card(label, value_id=None, value=None):
    value_props = {"id": value_id} if value_id else {}
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
                value,
                **value_props,
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


def gapminder_tab():
    return html.Div(
        style={"paddingTop": "20px"},
        children=[
            html.P(
                "Life expectancy, wealth and population across the world "
                "(Gapminder, 1952–2007).",
                style={"margin": "0 0 16px", "color": MUTED},
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


def databricks_tab():
    return html.Div(
        style={"paddingTop": "20px"},
        children=[
            html.P(
                "NYC yellow taxi trips from the Databricks sample table "
                "samples.nyctaxi.trips, queried live through a SQL warehouse.",
                style={"margin": "0 0 16px", "color": MUTED},
            ),
            dcc.Loading(
                type="circle",
                color=ACCENT,
                children=html.Div(id="dbx-content", style={"minHeight": "200px"}),
            ),
        ],
    )


TAB_STYLE = {"padding": "10px 20px", "fontWeight": 600, "color": MUTED,
             "border": "none", "borderBottom": "2px solid transparent",
             "backgroundColor": "transparent"}
TAB_SELECTED_STYLE = {**TAB_STYLE, "color": ACCENT, "borderBottom": f"2px solid {ACCENT}"}

app.layout = html.Div(
    style={"backgroundColor": BG, "minHeight": "100vh", "fontFamily": FONT,
           "color": TEXT, "padding": "32px 40px"},
    children=[
        html.Div(
            style={"maxWidth": "1280px", "margin": "0 auto"},
            children=[
                html.H1("World Explorer",
                        style={"margin": "0 0 16px", "fontSize": "28px", "fontWeight": 700}),
                dcc.Tabs(
                    id="tabs",
                    value="gapminder",
                    style={"borderBottom": "1px solid #e5e7eb"},
                    children=[
                        dcc.Tab(label="Gapminder", value="gapminder",
                                style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE,
                                children=gapminder_tab()),
                        dcc.Tab(label="Databricks Data", value="databricks",
                                style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE,
                                children=databricks_tab()),
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


# ---------------------------------------------------------------------------
# Databricks Data tab (samples.nyctaxi.trips via the app's SQL warehouse)
# ---------------------------------------------------------------------------
log = logging.getLogger("world_explorer")

TAXI_TABLE = "samples.nyctaxi.trips"

KPI_QUERY = f"""
SELECT
  COUNT(*)           AS total_trips,
  AVG(fare_amount)   AS avg_fare,
  AVG(trip_distance) AS avg_distance
FROM {TAXI_TABLE}
"""

HOURLY_QUERY = f"""
SELECT HOUR(tpep_pickup_datetime) AS pickup_hour, COUNT(*) AS trips
FROM {TAXI_TABLE}
GROUP BY 1
ORDER BY 1
"""

DAILY_QUERY = f"""
SELECT CAST(tpep_pickup_datetime AS DATE) AS pickup_date, AVG(fare_amount) AS avg_fare
FROM {TAXI_TABLE}
GROUP BY 1
ORDER BY 1
"""

CACHE_TTL_SECONDS = 600
_cache = {"at": 0.0, "data": None}
_cache_lock = threading.Lock()
_cfg = None


def _config():
    """Lazily build the SDK config (app service principal credentials)."""
    global _cfg
    if _cfg is None:
        from databricks.sdk.core import Config
        _cfg = Config()
    return _cfg


def run_query(query: str) -> pd.DataFrame:
    from databricks import sql

    warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID")
    if not warehouse_id:
        raise RuntimeError(
            "DATABRICKS_WAREHOUSE_ID is not set. Attach a SQL warehouse to the app "
            "with the resource key 'sql-warehouse'."
        )
    cfg = _config()
    with sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        credentials_provider=lambda: cfg.authenticate,
    ) as conn, conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall_arrow().to_pandas()


def load_taxi_data():
    """Run the three aggregate queries, cached for CACHE_TTL_SECONDS."""
    with _cache_lock:
        if _cache["data"] is not None and time.time() - _cache["at"] < CACHE_TTL_SECONDS:
            return _cache["data"]
        data = {
            "kpi": run_query(KPI_QUERY),
            "hourly": run_query(HOURLY_QUERY),
            "daily": run_query(DAILY_QUERY),
        }
        _cache.update(at=time.time(), data=data)
        return data


def error_card(detail):
    return html.Div(
        style={**CARD_STYLE, "borderLeft": "4px solid #e07b39"},
        children=[
            html.Div("Couldn't load data from Databricks",
                     style={"fontSize": "16px", "fontWeight": 700, "marginBottom": "6px"}),
            html.P(
                "The NYC taxi data isn't available right now. Check that a SQL warehouse "
                "is attached to this app under the resource key \"sql-warehouse\", that "
                "the warehouse is running, and that the app's service principal can read "
                f"{TAXI_TABLE}. Switch tabs and come back to retry.",
                style={"margin": "0 0 8px", "color": MUTED},
            ),
            html.Details([
                html.Summary("Technical details", style={"cursor": "pointer", "color": MUTED,
                                                         "fontSize": "13px"}),
                html.Pre(detail, style={"whiteSpace": "pre-wrap", "fontSize": "12px",
                                        "color": MUTED, "margin": "8px 0 0"}),
            ]),
        ],
    )


@app.callback(Output("dbx-content", "children"), Input("tabs", "value"))
def render_databricks_tab(tab):
    if tab != "databricks":
        return dash.no_update
    try:
        data = load_taxi_data()
    except Exception as exc:  # show a friendly message instead of crashing
        log.exception("Databricks query failed")
        return error_card(f"{type(exc).__name__}: {exc}")

    kpi = data["kpi"].iloc[0]
    hourly = data["hourly"].astype({"pickup_hour": int, "trips": int})
    daily = data["daily"].copy()
    daily["pickup_date"] = pd.to_datetime(daily["pickup_date"])
    daily["avg_fare"] = daily["avg_fare"].astype(float)

    by_hour = px.bar(hourly, x="pickup_hour", y="trips",
                     labels={"pickup_hour": "Pickup hour (0–23)", "trips": "Trips"})
    by_hour.update_traces(marker_color=ACCENT,
                          hovertemplate="Hour %{x}:00<br>%{y:,} trips<extra></extra>")
    by_hour.update_xaxes(dtick=1)
    style_figure(by_hour, "Trips by pickup hour")

    by_day = px.line(daily, x="pickup_date", y="avg_fare", markers=True,
                     labels={"pickup_date": "Pickup date", "avg_fare": "Avg. fare (USD)"})
    by_day.update_traces(line={"width": 2.5, "color": ACCENT},
                         hovertemplate="%{x|%b %d, %Y}<br>$%{y:.2f}<extra></extra>")
    style_figure(by_day, "Average fare by day")

    return html.Div(children=[
        html.Div(
            style={"display": "flex", "gap": "20px", "flexWrap": "wrap",
                   "marginBottom": "20px"},
            children=[
                kpi_card("Total trips", value=f"{int(kpi['total_trips']):,}"),
                kpi_card("Avg. fare", value=f"${float(kpi['avg_fare']):.2f}"),
                kpi_card("Avg. trip distance", value=f"{float(kpi['avg_distance']):.2f} mi"),
            ],
        ),
        html.Div(
            style={"display": "grid",
                   "gridTemplateColumns": "repeat(auto-fit, minmax(480px, 1fr))",
                   "gap": "20px"},
            children=[
                html.Div(style={**CARD_STYLE, "padding": "8px"},
                         children=dcc.Graph(figure=by_hour, config={"displaylogo": False},
                                            style={"height": "420px"})),
                html.Div(style={**CARD_STYLE, "padding": "8px"},
                         children=dcc.Graph(figure=by_day, config={"displaylogo": False},
                                            style={"height": "420px"})),
            ],
        ),
    ])


if __name__ == "__main__":
    port = int(os.getenv("DATABRICKS_APP_PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)
