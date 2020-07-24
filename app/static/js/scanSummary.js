var antennaRange;
var config = { responsive: true, displaylogo: false }
var layout = {
    title: { x: 0.5, font: { size: 15 } },
    xaxis: {
        title: 'Channel',
        font: { size: 5 },
    },
    yaxis: {
        title: 'Signal Measurement',
        font: { size: 11 },
        range: [0, 100]
    },
    margin: {
        b: 200
    },
    barmode: 'group'
}

function plotNewScan(newScanData) {
    figure = JSON.parse(newScanData.figure);
    layout.title.text = 'Signal Measurements of Scan at ' + moment.utc(newScanData.scantime).local().format("MMM DD, YYYY hh:mm A");

    Plotly.react('graph-container', figure.data, layout, config)
}

// Initial Requests
var xhttp1;
xhttp1 = new XMLHttpRequest();
xhttp1.onreadystatechange = function () {
    if (this.readyState == 4 && this.status == 200) {
        antennaRange = JSON.parse(this.responseText).range
    }
}

xhttp1.open(
    "GET",
    "http://www.employees.org:58000/graphs/scansummary/antennaapi?antenna=" + defaultAntenna,
    false
);
xhttp1.send();

var xhttp2;
xhttp2 = new XMLHttpRequest();
xhttp2.onreadystatechange = function () {
    if (this.readyState == 4 && this.status == 200) {
        plotNewScan(JSON.parse(this.responseText));
    }
}

xhttp2.open(
    "GET",
    "http://www.employees.org:58000/graphs/scansummary/scanapi?scantime=" + Date.now() + "&antenna=" + defaultAntenna,
    false
);
xhttp2.send();

// Fill Antenna instance selectbox
antennaSelectbox = document.getElementById('select-antenna')

for (instance of Object.keys(antennaMap)) {
    var option = document.createElement("option");
    option.value = instance;
    option.text = antennaMap[instance].name;
    antennaSelectbox.add(option);
}

$(window).on("resize", function () {
    // Set graph dimensions
    var update = {
        height: window.innerHeight * 0.9,
        width: window.innerWidth * 0.9,
    };
    Plotly.relayout('graph-container', update)
}).resize();

$(document).ready(function () {
    // Set defualt scan datetime
    $('#datetimepicker').datetimepicker({
        date: moment(new Date(Date.now()))
    });

    $('#datetimepicker').data("DateTimePicker").options({
        minDate: moment(antennaRange.start),
        maxDate: moment(antennaRange.end)
    });

    $('#datetimepicker')
        .datetimepicker()
        .on('dp.change', function (event) {
            var xhttp;
            xhttp = new XMLHttpRequest();
            xhttp.onreadystatechange = function () {
                if (this.readyState == 4 && this.status == 200) {
                    plotNewScan(JSON.parse(this.responseText));
                }
            }

            xhttp.open(
                "GET",
                "http://www.employees.org:58000/graphs/scansummary/scanapi?scantime=" + $('#datetimepicker').data('DateTimePicker').date().unix() + "&antenna=" + $('#select-antenna').val(),
                true
            );
            xhttp.send();
        });

    // Set default antenna instance
    $('#select-antenna')
        .select2()
        .val(defaultAntenna)
        .trigger("change");

    $('#select-antenna').on('select2:select', function (event) {
        var selectedInstance = $('#select-antenna').val();

        var xhttp;
        xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (this.readyState == 4 && this.status == 200) {
                antennaRange = JSON.parse(this.responseText).range
                $('#datetimepicker').data("DateTimePicker").options({
                    minDate: moment(antennaRange.start),
                    maxDate: moment(antennaRange.end)
                });

                $('#datetimepicker').datetimepicker({
                    date: moment(antennaRange.end)
                });
                $('#datetimepicker').datetimepicker().trigger('dp.change');
            }
        }

        xhttp.open(
            "GET",
            "http://www.employees.org:58000/graphs/scansummary/antennaapi?antenna=" + selectedInstance,
            true
        );
        xhttp.send();
    });
});