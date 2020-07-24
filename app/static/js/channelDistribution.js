var antennaRange, filterConditions = {};

// Initialize graph
for (var i = 3; i < figure.data.length; i++) {
    figure.data[i].y = figure.data[i].y.map(y => y * figure.data[0].x.length)
}

var layout = {
    title: { text: "Signal Measurement Distribution of Channel " + defaultChannel.split()[0] },
    yaxis: {
        range: [0, figure.data[0].x.length + 5],
        title: { text: "Scan Frequency (counts)" }
    },
    xaxis: {
        range: [-1, 101],
        title: { text: "Signal Measurement" }
    },
    showlegend: true,
    legend: { title: { text: legendTitle + "<br>" } },
    barmode: 'overlay'
};

var config = {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['autoScale2d', 'resetScale2d', 'select2d', 'lasso2d'],
    modeBarButtonsToAdd: [{
        name: 'updatableResetScale2d',
        title: 'Reset Axes',
        icon: Plotly.Icons.home,
        click: function (gd) {
            var update = { 'yaxis.range': [], 'xaxis.range': [-1, 101] };

            if ($('input[type=radio][name=freqradio]:checked').val() == "counts")
                update['yaxis.range'] = [0, figure.data[0].x.length + 5];
            else
                update['yaxis.range'] = [0, 1]

            Plotly.relayout(gd, update)
        }
    }],
    doubleClick: false
};

Plotly.newPlot('graph-container', figure.data, layout, config)
    .then(gd => {
        gd.on('plotly_legenddoubleclick', () => false) // Remove legend doubleclick functionality
        gd.on('plotly_legendclick', (event) => {
            var update = { visible: [] }
            var button = document.getElementById('hide-models');

            // Update legend visibility
            if (figure.data[event.curveNumber].visible == true) {
                update.visible.push("legendonly")
                update.visible.push("legendonly")
            } else if (figure.data[event.curveNumber].visible == 'legendonly') {
                update.visible.push(true)

                if (button.innerHTML == "Show Models")
                    update.visible.push("legendonly")
                else
                    update.visible.push(true)
            }

            Plotly.restyle('graph-container', update, [event.curveNumber, event.curveNumber + 3])
            return false
        })
    });

// Get Modal Datepicker Date Range
var xhttp;
xhttp = new XMLHttpRequest();
xhttp.onreadystatechange = function () {
    if (this.readyState == 4 && this.status == 200) {
        antennaRange = JSON.parse(this.responseText).range
    }
}

xhttp.open(
    "GET",
    "http://www.employees.org:58000/graphs/scansummary/antennaapi?antenna=" + defaultAntenna,
    false
);
xhttp.send();

// Fill Antenna and Channel selectboxes
antennaSelectbox = document.getElementById('select-antenna')

for (instance of Object.keys(antennaMap)) {
    var option = document.createElement("option");
    option.value = instance;
    option.text = antennaMap[instance].name;
    antennaSelectbox.add(option);
}

channelSelectbox = document.getElementById('select-channel')

for (instance of Object.keys(channelMap)) {
    var option = document.createElement("option");
    option.value = instance;
    option.text = channelMap[instance];
    channelSelectbox.add(option);
}

// Fill Modal Selectbox
weatherSelectbox = document.getElementById('select-weather-status')

for (status of weatherMap[defaultAntenna]) {
    var option = document.createElement("option");
    option.value = option.text = status;
    weatherSelectbox.add(option);
}

function setVisible(id, visible) {
    document.getElementById(id).style.display = visible ? 'block' : 'none';
}

function keyDown(event) {
    var deltaChannel = 0;
    var selectedChannel = $('#select-channel').val();
    var currentIndex = Object.keys(channelMap).indexOf(selectedChannel);
    // console.log(event.key)
    // console.log(currentIndex)

    switch (event.key) {
        case "ArrowLeft":
            if (currentIndex > 0)
                deltaChannel = -1;
            break;
        case "ArrowRight":
            if (currentIndex != Object.keys(channelMap).length - 1)
                deltaChannel = 1;
            break;
        default:
            return
    }

    // Don't switch if filter modal is open
    if (document.getElementById("filterModal").style.display == "none")
        $('#select-channel').val(Object.keys(channelMap)[currentIndex + deltaChannel]).trigger("change");
}

document.onkeydown = keyDown

$(window).on("resize", function () {
    // Set responsive graph dimensions
    var update = {
        height: window.innerHeight * 0.75,
        width: window.innerWidth * 0.9,
    };
    Plotly.relayout('graph-container', update)
}).resize();

function updateModel() {
    // Request
    var xhttp, filterArgs = "";
    xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            var update = { y: [] };
            var traces = [];
            figure.data = JSON.parse(JSON.parse(this.responseText)).data

            if ($('input[name=freqradio]:checked').val() == "counts")
                for (var i = figure.data.length / 2; i < figure.data.length; i++) {
                    figure.data[i].y = figure.data[i].y.map(y => y * figure.data[0].x.length);
                    update.y.push(figure.data[i].y);
                    traces.push(i);
                }
            else
                for (var i = figure.data.length / 2; i < figure.data.length; i++) {
                    update.y.push(figure.data[i].y);
                    traces.push(i);
                }

            // Replot
            Plotly.restyle('graph-container', update, traces)
        }
    }

    if (Object.keys(filterConditions).length > 0) {
        for (param of Object.values(filterConditions)) {
            if (param != "")
                filterArgs += "&" + param;
        }
    }

    xhttp.open(
        "GET",
        "http://www.employees.org:58000/graphs/channeldistribution/channelapi?channel=" + $('#select-channel').val()
        + "&antenna=" + $('#select-antenna').val() + "&model=" + $('input[name=modelradio]:checked').val() + filterArgs,
        true
    );
    xhttp.send();
}

function updateChannel(range = false) {
    var xhttp, filterArgs = "";
    var selectedChannel = $('#select-channel').val();

    if ($('input[name=freqradio]:checked').val() == "percents")
        histnorm = "probability";

    setVisible('channel-loading', true);

    // Request
    xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            figure.data = JSON.parse(JSON.parse(this.responseText)).data

            if ($('input[name=freqradio]:checked').val() == "counts")
                for (var i = figure.data.length / 2; i < figure.data.length; i++) {
                    figure.data[i].y = figure.data[i].y.map(y => y * figure.data[0].x.length);
                }
            else
                for (var i = 0; i < figure.data.length / 2; i++) {
                    figure.data[i].histnorm = "probability";
                }

            layout.title.text = "Signal Measurement Distribution of Channel " + selectedChannel;
            layout.legend.title.text = channelMap[selectedChannel].replace(": ", "<br>---<br>");
            layout.legend.title.text = layout.legend.title.text.replaceAll(", ", "<br>") + "<br>";

            if (range && $('input[name=freqradio]:checked').val() == "counts")
                layout.yaxis.range = [0, figure.data[0].x.length + 5];

            // Replot
            Plotly.react('graph-container', figure.data, layout, config)
            setVisible('channel-loading', false)
        }
    }

    if (Object.keys(filterConditions).length > 0) {
        for (param of Object.values(filterConditions)) {
            if (param != "")
                filterArgs += "&" + param;
        }
    }

    // console.log(filterArgs)

    xhttp.open(
        "GET",
        "http://www.employees.org:58000/graphs/channeldistribution/channelapi?channel=" + selectedChannel
        + "&antenna=" + $('#select-antenna').val() + "&model=" + $('input[name=modelradio]:checked').val() + filterArgs,
        true
    );
    xhttp.send();
}

function updateAntenna() {
    var xhttp;
    var selectedInstance = $('#select-antenna').val();
    setVisible('antenna-loading', true);

    // Request
    xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            var response = JSON.parse(this.responseText);
            channelMap = response.channelMap;
            weatherMap = response.weatherMap;

            $('#select-channel').empty().trigger("change");
            channelSelectbox = document.getElementById('select-channel')
            for (instance of Object.keys(channelMap)) {
                var option = document.createElement("option");
                option.value = instance;
                option.text = channelMap[instance];
                channelSelectbox.add(option);
            }

            // Fill Modal Selectbox
            $('#select-weather-status').empty().trigger("change");
            weatherSelectbox = document.getElementById('select-weather-status')

            for (status of weatherMap[selectedInstance]) {
                var option = document.createElement("option");
                option.value = option.text = status;
                weatherSelectbox.add(option);
            }

            // Update Antenna Range
            var xhttpRange;
            xhttpRange = new XMLHttpRequest();
            xhttpRange.onreadystatechange = function () {
                if (this.readyState == 4 && this.status == 200) {
                    antennaRange = JSON.parse(this.responseText).range

                    $('#datetimepicker-start').data("DateTimePicker").options({
                        minDate: moment(antennaRange.start),
                        maxDate: moment(antennaRange.end)
                    });

                    $('#datetimepicker-end').data("DateTimePicker").options({
                        minDate: moment(antennaRange.start),
                        maxDate: moment(antennaRange.end)
                    });
                }
            }

            xhttpRange.open(
                "GET",
                "http://www.employees.org:58000/graphs/scansummary/antennaapi?antenna=" + selectedInstance,
                false
            );
            xhttpRange.send();


            // Set channel to first in channelMap
            $('#select-channel').val(Object.keys(channelMap)[0]);
            updateChannel(range = true);
            setVisible('antenna-loading', false);
        }
    }

    xhttp.open(
        "GET",
        "http://www.employees.org:58000/graphs/channeldistribution/antennaapi?antenna=" + selectedInstance,
        true
    );
    xhttp.send();
}

function resetFilters() {
    filterConditions = {};

    // Reset all input fields
    // Time Inputs
    $('#timepicker-start').data("DateTimePicker").clear();
    $('#timepicker-end').data("DateTimePicker").clear();
    $('#datetimepicker-start').data("DateTimePicker").clear();
    $('#datetimepicker-end').data("DateTimePicker").clear();

    $('#datetimepicker-start').data("DateTimePicker").options({
        maxDate: moment(antennaRange.end),
        minDate: moment(antennaRange.start)
    });

    $('#datetimepicker-end').data("DateTimePicker").options({
        minDate: moment(antennaRange.start),
        maxDate: moment(antennaRange.end)
    });

    // Weather Inputs
    $('#temp-start').val("");
    $('#temp-end').val("");
    $('#wind-speed-start').val("");
    $('#wind-speed-end').val("");
    $('#wind-direction-start').val("");
    $('#wind-direction-end').val("");
    $('#humidity-start').val("");
    $('#humidity-end').val("");
    $('#select-weather-status').val('').trigger('change');

    document.getElementById("filter").className = "btn";
    document.getElementById('invalid-filter-condition').style.display = "none";
    updateChannel(range = true);
}

function isInt(value) {
    return !isNaN(value) &&
        parseInt(Number(value)) == value &&
        !isNaN(parseInt(value, 10));
}

function validateModalInputs() {
    checkTemp: if (
        !isInt($('#temp-start').val()) ||
        !isInt($('#temp-end').val()) ||
        parseInt($('#temp-start').val(), 10) >= parseInt($('#temp-end').val(), 10)
    ) {
        if ($('#temp-start').val() == "" || $('#temp-end').val() == "")
            break checkTemp;
        return false
    }

    checkWindSpeed: if (
        !isInt($('#wind-speed-start').val()) ||
        !isInt($('#wind-speed-end').val()) ||
        parseInt($('#wind-speed-start').val(), 10) < 0 ||
        parseInt($('#wind-speed-start').val(), 10) >= parseInt($('#wind-speed-end').val(), 10)
    ) {
        if ($('#wind-speed-start').val() == "" || $('#wind-speed-end').val() == "")
            break checkWindSpeed;
        return false
    }

    checkWindDirection: if (
        !isInt($('#wind-direction-start').val()) ||
        !isInt($('#wind-direction-end').val()) ||
        parseInt($('#wind-direction-start').val(), 10) < 0 ||
        parseInt($('#wind-direction-end').val(), 10) > 360 ||
        parseInt($('#wind-direction-start').val(), 10) >= parseInt($('#wind-direction-end').val(), 10)
    ) {
        if ($('#wind-direction-start').val() == "" || $('#wind-direction-end').val() == "")
            break checkWindDirection;
        return false
    }

    checkHumidity: if (
        !isInt($('#humidity-start').val()) ||
        !isInt($('#humidity-end').val()) ||
        parseInt($('#humidity-start').val(), 10) < 0 ||
        parseInt($('#humidity-end').val(), 10) > 100 ||
        parseInt($('#humidity-start').val(), 10) >= parseInt($('#humidity-end').val(), 10)
    ) {
        if ($('#humidity-start').val() == "" || $('#humidity-end').val() == "")
            break checkHumidity;
        return false
    }

    return true
}

$(document).ready(function () {
    // Reset radio buttons on page refresh
    $('#freqRadio').prop('checked', true);
    $('#kdeRadio').prop('checked', true);

    // Set default select values (main controls)
    $('#select-antenna')
        .select2()
        .val(defaultAntenna)
        .trigger("change");

    $('#select-channel')
        .select2()
        .val(defaultChannel)
        .trigger("change");

    // Modal Controls
    $('#datetimepicker-start').datetimepicker();
    $('#datetimepicker-end').datetimepicker({ useCurrent: false });
    $('#timepicker-start').datetimepicker({ format: "h:00 A" });
    $('#timepicker-end').datetimepicker({ format: "h:00 A" });

    $('#datetimepicker-start').data("DateTimePicker").options({
        minDate: moment(antennaRange.start),
        maxDate: moment(antennaRange.end)
    });

    $('#datetimepicker-end').data("DateTimePicker").options({
        minDate: moment(antennaRange.start),
        maxDate: moment(antennaRange.end)
    });

    $('#select-weather-status')
        .select2({ placeholder: 'Select a Weather Status' })
        .val('')
        .trigger('change');

    updateModel();
    resetFilters();

    $('#select-antenna').on('select2:select', function (event) {
        // console.log($('#select-antenna').val());
        updateAntenna();
    });

    $('#select-channel').on('select2:select', function (event) {
        // console.log($('#select-channel').val());
        updateChannel();
    });

    $('#select-channel').on('change', function (event) {
        // console.log($('#select-channel').val());
        updateChannel();
    });

    $('input[type=radio][name=freqradio]').change(function () {
        var traceBuffer = figure.data.length / 2;
        // console.log(this.value)
        // Update Signal Measurement
        if (this.value == "counts") {
            for (var i = 0; i < figure.data.length / 2; i++) {
                figure.data[i].histnorm = "";
                figure.data[i + traceBuffer].y = figure.data[i + traceBuffer].y.map(y => y * figure.data[0].x.length);
            }
            layout.yaxis.title.text = "Scan Frequency (counts)";
            layout.yaxis.range = [0, figure.data[0].x.length + 5];
        } else {
            for (var i = 0; i < figure.data.length / 2; i++) {
                figure.data[i].histnorm = "probability";
                figure.data[i + traceBuffer].y = figure.data[i + traceBuffer].y.map(y => y / figure.data[0].x.length);
            }
            layout.yaxis.title.text = "Relative Scan Frequency (%)";
            layout.yaxis.range = [0, 1];
        }

        // Replot
        Plotly.react('graph-container', figure.data, layout, config)
    });

    $('input[type=radio][name=modelradio]').change(function () {
        // console.log(this.value)
        updateModel()
    });

    $('#hide-models').click(function () {
        var traces = [];
        var update = { visible: [] };

        for (var i = figure.data.length / 2; i < figure.data.length; i++) {
            if (figure.data[i - 3].visible == true)
                traces.push(i);
        }

        if (this.innerHTML == "Hide Models") {
            update.visible = 'legendonly'
            this.innerHTML = 'Show Models'
        } else {
            update.visible = true
            this.innerHTML = 'Hide Models'
        }

        // console.log(traces)
        Plotly.restyle('graph-container', update, traces)
    });


    // Modal Events
    $("#datetimepicker-start").on("dp.change", function (e) {
        $('#datetimepicker-end').data("DateTimePicker").minDate(e.date);
    });
    $("#datetimepicker-end").on("dp.change", function (e) {
        $('#datetimepicker-start').data("DateTimePicker").maxDate(e.date);
    });

    $('#filter').click(function () {
        $('#filterModal').modal({ backdrop: 'static', keyboard: false })
    });

    $('#clear-filter').click(function () {
        resetFilters();
    });

    $('#apply-filter').click(function () {
        console.log(!validateModalInputs());
        if (!validateModalInputs()) {
            document.getElementById('invalid-filter-condition').style.display = "block";
            return
        }

        document.getElementById('invalid-filter-condition').style.display = "none";
        $('#filterModal').modal('hide');

        if ($('#timepicker-start').data("date") == "" || $('#timepicker-end').data("date") == "")
            filterConditions["tod"] = ""
        else {
            filterConditions["tod"] = "tod=" + $('#timepicker-start').data('DateTimePicker').viewDate().hour() + "&tod=" + $('#timepicker-end').data('DateTimePicker').viewDate().hour();
            if ($('#timepicker-start').data('DateTimePicker').viewDate().hour() > $('#timepicker-end').data('DateTimePicker').viewDate().hour())
                filterConditions["tod"] += "&inversetod=true"
        }

        try {
            filterConditions["daterange"] = "daterange=" + $('#datetimepicker-start').data('DateTimePicker').date().unix() + "&daterange=" + $('#datetimepicker-end').data('DateTimePicker').date().unix()
        } catch (TypeError) {
        }

        if ($('#temp-start').val() == "" || $('#temp-end').val() == "")
            filterConditions["temp"] = ""
        else
            filterConditions["temp"] = "temp=" + $('#temp-start').val() + "&temp=" + $('#temp-end').val()

        if ($('#wind-speed-start').val() == "" || $('#wind-speed-end').val() == "")
            filterConditions["windspeed"] = ""
        else
            filterConditions["windspeed"] = "windspeed=" + $('#wind-speed-start').val() + "&windspeed=" + $('#wind-speed-end').val()

        if ($('#wind-direction-start').val() == "" || $('#wind-direction-end').val() == "")
            filterConditions["winddirection"] = ""
        else
            filterConditions["winddirection"] = "winddirection=" + $('#wind-direction-start').val() + "&winddirection=" + $('#wind-direction-end').val()

        if ($('#humidity-start').val() == "" || $('#humidity-end').val() == "")
            filterConditions["humidity"] = ""
        else
            filterConditions["humidity"] = "humidity=" + $('#humidity-start').val() + "&humidity=" + $('#humidity-end').val()

        if ($("#select-weather-status").val() == null)
            filterConditions["weatherstatus"] = ""
        else
            filterConditions["weatherstatus"] = "weatherstatus=" + $("#select-weather-status").val().replaceAll(" ", "+");


        function checkConditionStr(conditionStr) {
            return conditionStr == ""
        }

        if (!Object.values(filterConditions).every(checkConditionStr))
            document.getElementById("filter").className = "btn btn-success"

        updateChannel(range = true);
    });
});