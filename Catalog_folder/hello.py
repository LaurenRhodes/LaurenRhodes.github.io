from flask import Flask, redirect, url_for, render_template, request, send_file
import io
import pandas as pd
import plotly.express as px

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/light-curves")
def light_curves():
    df = pd.read_csv("data/all_lightcurve_data_website_with_anderson_12082026.csv")
    
    selected_type = request.args.get("type", "all")
    selected_redshift = request.args.get("redshift", "all")
    selected_year = request.args.get("year", "all")
    selected_inpaper = request.args.get("paper", "all")

    if selected_type != "all":
        df = df[df["Type"] == selected_type]

    if selected_redshift == "known":
        df = df[df["Redshift"] != "Unknown"]

    if selected_redshift == "unknown":
        df = df[df["Redshift"] == "Unknown"]
    
    if selected_year != "all":
        df = df[df["Year"].astype(str) == selected_year]
    
    df["In the paper"] = df["In the paper"].astype(str).str.upper()
    if selected_inpaper != "all":
        df = df[df["In the paper"] == selected_inpaper]
    
    df_detect = df[df["Type"] == "Detection"]
    df_upper  = df[df["Type"] == "Non-Detection"]

    fig = px.scatter(
        df_detect,
        x="Time Since Burst (days)",
        y="Flux (mJy)",
        error_y="Error (mJy)",
        custom_data=["Redshift"],
        color="Source",
        log_x=True,
        log_y=True)
    
    fig.update_traces(
    hovertemplate=
        "<b>%{fullData.name}</b><br>" +
        "Type: Detection<br>" +
        "Time since burst: %{x} days<br>" +
        "Flux: %{y} mJy<br>" +
        "Redshift: %{customdata[0]}<extra></extra>")
    
    for grb in df_upper["Source"].unique():

        df_grb = df_upper[df_upper["Source"] == grb]

        # try to recover same color from detections
        color = None

        for trace in fig.data:
            if trace.name == grb:
                color = trace.marker.color
                break

    # if no detection exists, let plotly choose a new color
        if color is None:
            showlegend = True
        else:
            showlegend = False

        fig.add_scatter(
            x=df_grb["Time Since Burst (days)"],
            y=df_grb["Flux (mJy)"],
            mode="markers",
            customdata=df_grb[["Redshift"]],
            marker=dict(
                symbol="triangle-down",
                size=10,
                color=color
            ),
            name=grb,
            legendgroup=grb,
            showlegend=showlegend,
            hovertemplate=
                "<b>%{fullData.name}</b><br>" +
                "Type: Non-Detection<br>" +
                "Time since burst: %{x} days<br>" +
                "Flux: %{y} mJy<br>" +
                "Redshift: %{customdata[0]}<extra></extra>"
        )

    seen = set()

    for trace in fig.data:

        if trace.name in seen:
            trace.showlegend = False
        else:
            seen.add(trace.name)

    fig.update_xaxes(
        type="log",
        exponentformat="power")

    fig.update_yaxes(
        type="log",
        exponentformat="power")
    
    fig.update_layout(
    legend_title_text="Source")

    plot_html = fig.to_html(full_html=False)

    return render_template(
        "light_curves.html",
        plot_html=plot_html,
        selected_type=selected_type,
        selected_redshift=selected_redshift,
        selected_year=selected_year,
        selected_inpaper=selected_inpaper,
        request=request)

def filter_dataframe(df, request):
    selected_type = request.args.get("type", "all")
    selected_redshift = request.args.get("redshift", "all")
    selected_year = request.args.get("year", "all")
    selected_inpaper = request.args.get("paper", "all")

    if selected_type != "all":
        df = df[df["Type"] == selected_type]

    if selected_redshift == "known":
        print(df["Redshift"])
        df = df[df["Redshift"] != "Unknown"]

    elif selected_redshift == "unknown":
        df = df[df["Redshift"] == "Unknown"]

    if selected_year != "all":
        df = df[df["Year"].astype(str) == selected_year]

    df["In the paper"] = df["In the paper"].astype(str).str.upper()
    if selected_inpaper != "all":
        df = df[df["In the paper"] == selected_inpaper]

    return df

@app.route("/downloads")
def downloads():

    df = pd.read_csv("data/all_lightcurve_data_website_27052026.csv")

    years = sorted(df["Year"].dropna().unique())

    return render_template(
        "downloads.html",
        years=years
    )

@app.route("/downloads-data")
def download_data():

    df = pd.read_csv("data/all_lightcurve_data_website_with_anderson_12082026.csv")

    selected_type = request.args.get("type", "all")
    selected_redshift = request.args.get("redshift", "all")
    selected_year = request.args.get("year", "all")
    selected_inpaper = request.args.get("paper", "all")

    if selected_type != "all":
        df = df[df["Type"] == selected_type]

    if selected_redshift == "known":
        df = df[df["Redshift"] != "Unknown"]

    elif selected_redshift == "unknown":
        df = df[df["Redshift"] == "Unknown"]

    if selected_year != "all":
        df = df[df["Year"].astype(str) == selected_year]

    df["In the paper"] = df["In the paper"].astype(str).str.upper()

    if selected_inpaper != "all":
        df = df[df["In the paper"] == selected_inpaper]

    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="lightcurve_data.csv",
        mimetype="text/csv"
    )

if __name__ == "__main__" :
    app.run(debug=True)
    
    
