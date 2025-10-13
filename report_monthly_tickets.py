from dash import Dash, dcc, html, Input, Output
import datetime as dt
import glob
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys

# Attempt to find the CSV file in the root of the repository
try:
    files_globbed = glob.glob(r"Ticket_List*")
    csv_input = files_globbed[0]
except Exception as err:
    sys.exit(
        f"There are no files in the directory with the correct name -- {err}"
    )

# Define the Dash app
app = Dash()

# Set the current date
date_today = dt.datetime.today()

# Get the first day of the previous month
date_month_start = ((date_today - dt.timedelta(days=25))
                    .replace(day=1)
                    .strftime("%Y-%m-%d")
                    )

# Get the last day of the previous month
date_month_end = ((date_today.replace(day=1) - dt.timedelta(days=1))
                  .strftime("%Y-%m-%d"))

# Format the layout of the Dash app
app.layout = html.Div([
    html.H1(
        "Ticket Visualizations"
    ),
    dcc.DatePickerRange(
        id="date-picker-range",
        display_format="YYYY-MM-DD",
        start_date=date_month_start,
        end_date=date_month_end,
        number_of_months_shown=1
    ),
    dcc.Graph(
        id="bar-chart"
    ),
    dcc.Graph(
        id="pie-main-queues",
        style={
            "width": "80%",
            "height": "1000px"
        }
    ),
    dcc.Graph(
        id="pie-chart",
        style={
            "width": "80%",
            "height": "1000px"
        }
    ),
])


def csv_to_dataframe(file):
    try:
        df = pd.read_csv(
            file,
            parse_dates=["Created"],
            low_memory=False
        )
    except Exception as err:
        sys.exit(f"[ERROR]: Failed to process {file} into dataframe -- {err}")

    return df


def generate_charts(df):
    # Total the accounted time for tickets, and number of tickets
    sub_queues = df.groupby("Sub Queue").agg({
        "Accounted time": "sum",
        "Queue": "count"
    }).reset_index()

    # Give the new columns some names
    sub_queues.rename(
        columns={
            "Queue":
            "Total tickets"
        },
        inplace=True
    )

    # Total the number of closed tickets
    total_closed = df["IsClosed"].sum()

    # Get the total number of tickets in the subqueues
    total_tickets = sub_queues["Total tickets"].sum()

    # Get the percent of tickets closed
    if total_tickets > 0:
        percent_closed = round(100 * total_closed / total_tickets)
    else:
        0

    # Generate the bar chart for the subqueues
    bar_sub_queues = px.bar(
        sub_queues,
        x="Sub Queue",
        y="Accounted time",
        text="Total tickets",
        title="Accounted time by subqueue",
        labels={
            "Subqueue":
            "Subqueue"
        }
    )

    # Set the colors for the bar chart
    bar_sub_queues.update_traces(
        marker_color="lightcoral"
    )

    # Annotate the subqueue bar chart re: total tickets
    bar_sub_queues.add_annotation(
        x=1,
        y=(total_tickets + 800),
        text=f"Total tickets: {total_tickets}",
        showarrow=False,
        font=dict(size=14)
    )

    # Annotate the subqueue bar chart re: closed tickets
    bar_sub_queues.add_annotation(
        x=1,
        y=(total_closed + 1000),
        text=f"Closed tickets: {total_closed}",
        showarrow=False,
        font=dict(size=14)
    )

    # Annotate the subqueue bar chart re: percent closed
    bar_sub_queues.add_annotation(
        x=1,
        y=(total_closed + 600),
        text=f"{percent_closed}% closed",
        showarrow=False,
        font=dict(size=14)
    )

    # Total the accounted time for tickets, and number of tickets
    main_queues = df.groupby("Main Queue").agg({
        "Accounted time": "sum",
        "Queue": "count"
    }).reset_index()

    # Give the new columns some names
    main_queues.rename(
        columns={
            "Queue":
            "Total tickets"
        },
        inplace=True
    )

    # Set "overall accounted time"
    accounted_time = df["Accounted time"].sum()

    # Generate the pie chart for the main queues
    pie_main_queues = go.Figure(
        data=[(
            go.Pie(
                labels=main_queues["Main Queue"],
                values=main_queues["Accounted time"],
                textinfo="label+percent",
                hole=0.3
            )
        )]
    )

    # Set the colors for the pie chart
    pie_main_queues.update_traces(
        marker=dict(
            colors=["lightgreen"]
        )
    )

    # Set the title for the pie chart
    pie_main_queues.update_layout(
        title="% time by main queues"
    )

    # Generate the pie chart for the sub queues
    pie_sub_queues = go.Figure(
        data=[(
            go.Pie(
                labels=sub_queues["Sub Queue"],
                values=sub_queues["Accounted time"],
                textinfo="label+percent",
                hole=0.3
            )
        )]
    )

    # Set the colors for the pie chart
    pie_sub_queues.update_traces(
        marker=dict(
            colors=["skyblue"]
        )
    )

    # Set the title for the pie chart
    pie_sub_queues.update_layout(
        title="% time by subqueue"
    )

    # Annotate the main queue pie chart re: accounted time
    pie_sub_queues.add_annotation(
        x=0.5,
        y=1000,
        text=f"Total time: {accounted_time}",
        showarrow=False,
        font=dict(size=14)
    )

    return bar_sub_queues, pie_main_queues, pie_sub_queues


df = csv_to_dataframe(csv_input)


# The callback defines what gets updated when a change is detected
@app.callback(
    [
        Output("bar-chart", "figure"),
        Output("pie-main-queues", "figure"),
        Output("pie-chart", "figure")
    ],
    [
        Input("date-picker-range", "start_date"),
        Input("date-picker-range", "end_date")
    ]
)
def display_charts(date_month_start, date_month_end):
    if df.empty:
        return go.Figure(), go.Figure(), go.Figure()

    # The dataframe should only show data from the date range
    temp_df = df[
        (
            df["Created"] >= date_month_start
        ) & (
            df["Created"] <= date_month_end
        )
    ].copy()

    # Show only the relevant information
    temp_df[[
        "Main Queue",
        "Sub Queue"
    ]] = temp_df["Queue"].str.split(
        "::",
        expand=True
    )

    # Format the empty cells
    temp_df["Sub Queue"].fillna("")

    # Remove rows with no subqueue
    temp_df = temp_df[temp_df["Sub Queue"] != ""]

    # Remove columns that are not applicable
    temp_df = temp_df[(
        ~temp_df["Main Queue"].isin([
            "AIM",
            "Cloud"
        ])
    )]

    # Create the `IsClosed` column for tickets that are closed
    temp_df["IsClosed"] = ~temp_df["State"].str.contains(
        "open",
        case=False,
        na=False,
        regex=True
    )

    bar_sub_queues, pie_sub_queues, pie_main_queues = generate_charts(temp_df)

    return bar_sub_queues, pie_sub_queues, pie_main_queues


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
