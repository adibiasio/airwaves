import datetime
import json

from flask import Flask, jsonify, render_template, request
from flask_caching import Cache

from channel_distribution import ChannelDistribution
from scan_summary import ScanSummary
from track_channel import TrackChannels

config = {
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 300
}

app = Flask("flask_app")
app.config.from_mapping(config)
cache = Cache(app)

@app.route("/")
@app.route("/home")
@app.route("/home/")
def home():
    return render_template("home.html")

@app.route("/help")
@app.route("/help/")
def help_page():
    return render_template("help.html", title="Help")

@app.route("/api")
@app.route("/api/")
def apis():
    return render_template("api.html", title="API")

# ---- Graphing Programs ----

# Track Channel
@app.route("/graphs/trackchannel")
@app.route("/graphs/trackchannel/")
@cache.cached(timeout=3600)
def track_channel():
    graph = TrackChannels()
    return render_template(
        "trackChannel.html",
        title="Track Channel",
        antennaMap=json.dumps(graph.antenna_map),
        defaultAntenna=graph.default_antenna
        )

@app.route("/graphs/trackchannel/api")
@cache.cached(timeout=3600, query_string=True)
def track_channel_api():
    graph = TrackChannels()
    antenna = request.args.get("antenna", graph.default_antenna, type=int)
    return jsonify(figure=graph.get_json(antenna=antenna), labels=json.dumps(graph.labels), annotations=graph.mdf["annotations"].tolist())


# Scan Summary
@app.route("/graphs/scansummary")
@app.route("/graphs/scansummary/")
@cache.cached(timeout=3600)
def scan_summary():
    graph = ScanSummary()
    return render_template(
        "scanSummary.html",
        title="Scan Summary",
        figure=graph.get_json(antenna=graph.default_antenna),
        antennaMap=json.dumps(graph.antenna_map),
        defaultAntenna=graph.default_antenna
        )

@app.route("/graphs/scansummary/scanapi")
@cache.cached(timeout=3600, query_string=True)
def scan_summary_scan_api():
    graph = ScanSummary()
    scan = request.args.get("scantime", datetime.datetime.now(), type=int)
    antenna = request.args.get("antenna", None, type=int)
    return jsonify(figure=graph.get_json(scantime=scan, antenna=antenna), scantime=graph.start_time)

@app.route("/graphs/scansummary/antennaapi")
@cache.cached(timeout=3600, query_string=True)
def scan_summary_antenna_api():
    graph = ScanSummary()
    antenna = request.args.get("antenna", graph.default_antenna, type=int)
    return jsonify(range=graph.get_antenna_range(antenna=antenna))

# Channel Distribution
@app.route("/graphs/channeldistribution")
@app.route("/graphs/channeldistribution/")
@cache.cached(timeout=3600)
def channel_distribution():
    graph = ChannelDistribution()
    return render_template(
        "channelDistribution.html",
        title="Channel Distribution",
        figure=graph.get_json(channel=graph.default_channel, antenna=graph.default_antenna),
        defaultChannel=graph.default_channel,
        defaultAntenna=graph.default_antenna,
        legendTitle=graph.channel_label,
        channelMap=json.dumps(graph.labels),
        antennaMap=json.dumps(graph.antenna_map),
        weatherMap=json.dumps(graph.weather_map)
        )

@app.route("/graphs/channeldistribution/channelapi")
@cache.cached(timeout=3600, query_string=True)
def channel_distribution_channel_api():
    graph = ChannelDistribution()
    
    # Request Args
    channel = request.args.get("channel", graph.default_channel, type=int)
    antenna = request.args.get("antenna", graph.default_antenna, type=int)
    model = request.args.get("model", "kde", type=str)
    histnorm = request.args.get("histnorm", "", type=str)

    # Filter Conditions
    filter_conditions = {}
    inversetod = request.args.get("inversetod", type=bool)

    tod = request.args.getlist("tod", type=int) # Time of Day
    daterange = request.args.getlist("daterange", type=int)
    temp = request.args.getlist("temp", type=int)
    windspeed = request.args.getlist("windspeed", type=int)
    winddirection = request.args.getlist("winddirection", type=int)
    humidity = request.args.getlist("humidity", type=int)
    weatherstatus = request.args.get("weatherstatus", type=str)

    for condition, label in zip([tod, daterange, temp, windspeed, winddirection, humidity, weatherstatus], graph.filter_col_labels):
        filter_conditions[label] = condition 

    # Convert Hours to Seconds
    filter_conditions["hour_of_day"] = [hour * 3600 for hour in tod] if len(filter_conditions["hour_of_day"]) > 0 else filter_conditions["hour_of_day"]

    return jsonify(
        graph.get_json(
            channel=channel, 
            antenna=antenna, 
            model=model, 
            histnorm=histnorm,
            filter_conditions = filter_conditions,
            inversetod=inversetod
        )
    )

@app.route("/graphs/channeldistribution/antennaapi")
@cache.cached(timeout=3600, query_string=True)
def channel_distribution_antenna_api():
    graph = ChannelDistribution()
    
    # Request Args
    antenna = request.args.get("antenna", graph.default_antenna, type=int)

    return jsonify(
        channelMap=graph.get_channel_map(antenna=antenna), 
        weatherMap=graph.get_weather_map(antenna=antenna)
    )

if __name__ == "__main__":
    app.run(host="198.137.202.74", port="58000", debug=False)
    # app.run(host="127.0.0.1", port="8000", debug=True)
