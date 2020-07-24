var figure, labels, graphLoaded;
var realChannels, realChannelCount, virtualChannelCount;
var config, antennaSelectbox;
var selectedSignal = "snq";

function diffTime(dt2, dt1) {
    dt1 = new Date(dt1);
    dt2 = new Date(dt2);

    var diff = (dt2.getTime() - dt1.getTime()) / 1000;
    return Math.abs(diff);
}

function shiftDays(date, days) {
    date = new Date(date);
    return date.setDate(date.getDate() + days);
}

config = { responsive: true, displaylogo: false, modeBarButtonsToRemove: ['autoScale2d'] }
var layout = {
    title: { x: 0.5, font: { size: 15 } },
    xaxis: {
        title: 'Time',
        rangeselector: {
            buttons: [{
                count: 1,
                label: '1d',
                step: 'day',
                stepmode: 'backward'
            },
            {
                count: 7,
                label: '1w',
                step: 'day',
                stepmode: 'backward'
            },
            {
                count: 1,
                label: '1m',
                step: 'month',
                stepmode: 'backward'
            },
            {
                count: 6,
                label: '6m',
                step: 'month',
                stepmode: 'backward'
            },
            {
                // Use count of diffTime to avoid autoscaling when no traces are selected
                label: 'Max',
                step: 'second',
                stepmode: 'backward'
            }]
        },
    },
    yaxis: {
        title: 'snq',
        font: { size: 15 },
        range: [0, 100]
    },
    showlegend: true,
    legend: {
        orientation: 'v',
        font: { size: 10 },
        title: { text: '' }
    },
    hovermode: 'closest',
    hoverinfo: "y",
    hoverlabel: { namelength: -1 },
    font_size: 11
}

// Loading Screen
function onReady(callback) {
    var intervalId = window.setInterval(function () {
        if (graphLoaded) {
            window.clearInterval(intervalId);
            callback.call(this);
            graphLoaded = false;
        }
    }, 1000);
}

function setVisible(selector, visible) {
    document.querySelector(selector).style.display = visible ? 'block' : 'none';
}

function setPlotAntenna(antennaData, antenna = defaultAntenna) {
    // Update global variables

    figure = JSON.parse(antennaData.figure);
    labels = JSON.parse(antennaData.labels);
    annotations = antennaData.annotations;
    // console.log(annotations);

    // Set Channel Counts
    realChannels = Object.keys(labels).reverse();
    realChannelCount = realChannels.length;
    virtualChannelCount = 0;

    for (channelLabel of Object.values(labels)) {
        // subtract 3 to account for formatting real channel line breaks
        virtualChannelCount += channelLabel['vertical'].split('<br>').length - 3;
    }

    // Set layout properties dependent on Antenna Instance
    layout.title.text = selectedSignal + ' of Antenna Instance ' + antenna + ' Over Time';
    layout.xaxis.range = [shiftDays(figure.data[0].x[figure.data[0].x.length - 1], -1), figure.data[0].x[figure.data[0].x.length - 1]];
    layout.xaxis.rangeselector.buttons[layout.xaxis.rangeselector.buttons.length - 1].count = diffTime(figure.data[0].x[figure.data[0].x.length - 1], figure.data[0].x[0]);
    layout.legend.title.text = realChannelCount + ' Real Channels<br>' + virtualChannelCount + ' Virtual Channels';

    // Set time & annotation data points of all traces
    for (i = 1; i < figure.data.length; i++) {
        figure.data[i].x = figure.data[0].x;
        figure.data[i].text = annotations
    }

    // Set Default Legend Labels
    for (i = 0; i < realChannelCount; i++) {
        figure.data[i].name = labels[realChannels[i]]['vertical']
    }

    // Create Graph
    Plotly.react('graph-container', figure.data, layout, config)
    graphLoaded = true;
}
var xhttp;
xhttp = new XMLHttpRequest();
xhttp.onreadystatechange = function () {
    if (this.readyState == 4 && this.status == 200) {
        setPlotAntenna(JSON.parse(this.responseText), antenna = defaultAntenna)

        Plotly.react('graph-container', figure.data, layout, config)
            .then(gd => {
                gd.on('plotly_legenddoubleclick', () => false) // Remove doubleclick functionality
                gd.on('plotly_legendclick', (event) => {
                    var update = { visible: true }
                    var button = document.getElementById('hide-all-traces');

                    // Update legend visibility
                    if (figure.data[event.curveNumber].visible == true)
                        update.visible = 'legendonly'
                    else if (figure.data[event.curveNumber].visible == 'legendonly')
                        update.visible = true

                    Plotly.restyle('graph-container', update, event.curveNumber)

                    // Update 'Hide All' button text
                    for (trace of figure.data) {
                        if (trace.visible == true && button.innerHTML == "Show All") {
                            button.innerHTML = "Hide All"
                            return false
                        } else if (trace.visible == true)
                            return false
                    };

                    button.innerHTML = "Show All"
                    return false
                })
            })
    }
}

xhttp.open(
    "GET",
    "http://www.employees.org:58000/graphs/trackchannel/api?antenna=" + defaultAntenna,
    false
);
xhttp.send();

onReady(function () {
    setVisible('.page', true);
    setVisible('#loading', false);
});

// Fill Antenna instance selectbox
antennaSelectbox = document.getElementById('select-antenna')

for (instance of Object.keys(antennaMap)) {
    var option = document.createElement("option");
    option.value = instance;
    option.text = antennaMap[instance].name;
    antennaSelectbox.add(option);
}

function setLegendView(resetCurrentView = false) {
    var label_index, update;

    if (resetCurrentView) {
        if (this.innerHTML == 'Legend Fullview')
            label_index = 'horizontal'
        else
            label_index = 'vertical'
    } else {
        if (figure.data[0].name.includes('<br>'))
            label_index = 'horizontal'
        else
            label_index = 'vertical'
    }

    // Set Legend Labels
    update = { name: [] };
    for (i = 0; i < realChannelCount; i++) {
        update['name'].push(labels[realChannels[i]][label_index])
    }
    Plotly.restyle('graph-container', update);

    if (resetCurrentView)
        return

    // Update Button Text
    if (this.innerHTML == 'Legend Fullview')
        this.innerHTML = 'Legend Scrollview'
    else
        this.innerHTML = 'Legend Fullview'
}

// Set default antenna instance
$('#select-antenna')
    .select2()
    .val(defaultAntenna)
    .trigger("change");

$(window).on("resize", function () {
    // Set graph dimensions
    var update = {
        height: window.innerHeight * 0.9,
        width: window.innerWidth * 0.9,
    };
    Plotly.relayout('graph-container', update)
}).resize();


$(document).ready(function () {
    // Reset radio on page refresh
    $('#snqRadio').prop('checked', true);

    $('#change-legend-view').click(function () {
        setLegendView();
    });

    $('#hide-all-traces').click(function () {
        var traceStart, traceEnd, signalMeasurementFactor;
        var traces = [];
        var update = { visible: [] };

        switch (selectedSignal) {
            case "ss":
                signalMeasurementFactor = 2
                break;
            case "seq":
                signalMeasurementFactor = 3
                break;
            default:
                // case "snq"
                signalMeasurementFactor = 1
                break;
        }

        traceStart = (signalMeasurementFactor * realChannelCount) - realChannelCount;
        traceEnd = signalMeasurementFactor * realChannelCount;

        for (i = traceStart; i < traceEnd; i++) {
            update.visible.push(figure.data[i].visible);
            traces.push(i);
        }

        if (update.visible.includes(true)) {
            // Current Text: Hide All
            update.visible = 'legendonly'
            this.innerHTML = 'Show All'
        } else {
            // Current Text: Show All
            update.visible = true
            this.innerHTML = 'Hide All'
        }

        Plotly.restyle('graph-container', update, traces);
    });

    $('input[type=radio][name=smradio]').change(function () {
        // Update Signal Measurement
        var update = { visible: [] };
        var visibilityMap = { snq: [], ss: [], seq: [] };

        for (i = 0; i < realChannelCount; i++) {
            if (selectedSignal == "snq")
                visibilityMap.snq.push(figure.data[i].visible)
            else
                visibilityMap.snq.push(false)
        }

        for (i = realChannelCount; i < 2 * realChannelCount; i++) {
            if (selectedSignal == "ss")
                visibilityMap.ss.push(figure.data[i].visible)
            else
                visibilityMap.ss.push(false)
        }

        for (i = 2 * realChannelCount; i < 3 * realChannelCount; i++) {
            if (selectedSignal == "seq")
                visibilityMap.seq.push(figure.data[i].visible)
            else
                visibilityMap.seq.push(false)
        }

        [visibilityMap[this.value], visibilityMap[selectedSignal]] = [visibilityMap[selectedSignal], visibilityMap[this.value]];
        update = { visible: visibilityMap.snq.concat(visibilityMap.ss, visibilityMap.seq) }
        setLegendView(resetCurrentView = true)

        layout.title.text = layout.title.text.replace(layout.title.text.split(" ")[0], this.value)
        selectedSignal = layout.yaxis.title.text = this.value

        // Replot
        Plotly.restyle('graph-container', update);
    });

    $('#select-antenna').on('select2:select', function (event) {
        var selectedInstance = $('#select-antenna').val();

        setVisible('.page', false);
        setVisible('#loading', true);

        var xhttp;
        xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (this.readyState == 4 && this.status == 200) {
                setPlotAntenna(JSON.parse(this.responseText), antenna = selectedInstance)
            }
        }

        xhttp.open(
            "GET",
            "http://www.employees.org:58000/graphs/trackchannel/api?antenna=" + selectedInstance,
            true
        );
        xhttp.send();

        // Loading Screen
        onReady(function () {
            setVisible('.page', true);
            setVisible('#loading', false);
        });
    });

});
