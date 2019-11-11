/* This is the central Dissemin JavaScript library */
/* Every function should be inside this file */


/* ***
 * Miscellaneous
 * *** */

/* On AJAX errors, we like to be informed via Sentry */
$(document).ajaxError( function (event, jqXHR, ajaxSettings, thrownError) {
    try {
        Sentry.captureMessage(thrownError || jqXHR.statusText, {
            extra: {
                type: ajaxSettings.type,
                url: ajaxSettings.url,
                data: ajaxSettings.data,
                status: jqXHR.status,
                error: thrownError || jqXHR.statusText,
                response: jqXHR.responseText.substring(0, 100)
            }
        });
    }
    catch (e)
    {
        console.log(thrownError);
        console.log(ajaxSettings);
    }
});

/* Enable bootstrap tooltip */
$(function () {
    $('[data-toggle="tooltip"]').tooltip();
});

/* Returns the current csrf token from the cookie. This is the recommend method by django: https://docs.djangoproject.com/en/2.2/ref/csrf/#ajax */
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


/* ***
 * Navigation
 * *** */

/* When changing language in dropdown, submit the form */
$(function() {
    $("#select-language").change(function() {
        $("#select-language").submit();
    });
});

/* This is the ORCID Logout. Pass the orcid_base_domain as parameter */
function orcidLogout (orcid_base_domain) {
    $.ajax({ url: 'https://' + orcid_base_domaon + '/userStatus.json?logUserOut=true',
        dataType: 'jsonp',
        success: function(result,status,xhr) {
                    window.location.href = '{% url "account_logout" %}';
                },
        error: function (xhr, status, error) {
                    window.location.href = '{% url "account_logout" %}';
                }
    })
}


/* ***
 * Paper
 * *** */

/* A paper can have many authors. This functions shows or hides all authors using flex and aria-hidden */
$(function() {
    $("#showAllAuthors").click(function() {
        $('#authorListInteresting').addClass("d-none"); // Hide from screen
        $('#authorListInteresting').attr("aria-hidden", "true"); // Hide from screenreader

        $('#authorListFull').removeClass("d-none"); // Show
        $('#authorListFull').attr("aria-hidden", "false"); // Hide no longer from screenreader
    });

    $("#showInterestingAuthors").click(function() {
        $('#authorListFull').addClass("d-none"); // Hide from screen
        $('#authorListFull').attr("aria-hidden", "true"); // Hide from screenreader

        $('#authorListInteresting').removeClass("d-none"); // Show
        $('#authorListInteresting').attr("aria-hidden", "false"); // Hide no longer from screenreader
    });

});

/* Add item to the to-do list and change UI accordingly
 * This function is here, because it is related to the search */
$(function() {
    $('#paperButtonTodoList').click(function() {
        obj = $(this);
        var paper_pk = obj.attr("data-paper-pk");
        var ajax_url = Urls['ajax-todolist-add']();

        $.ajax({
            data: {
                "paper_pk": paper_pk,
                "csrfmiddlewaretoken": getCookie('csrftoken')
            },
            dataType: 'json',
            error: function (data) {
                obj.text(data['error_msg']);
            },
            method : 'post',
            success: function (data) {
                obj.remove();
                $('#paperTodoListAdded').removeClass("d-none"); // Show
                $('#paperTodoListAdded').attr("aria-hidden", "false"); // Hide no longer from screenreader
            },
            timeout : 5000,
            url : ajax_url
        });

    });
});


/* ***
 * Publishers
 * *** */

/* Change the OA status of a publisher */
$(function() {
    $('#changePublisherOAStatus input').change(function() {
        var form = $('#changePublisherOAStatus');

        ajax_url = Urls[form.attr('data-ajax-url')]();
        publisher_pk = form.attr('data-publisher-pk');
        new_status = $('input[name=radioOAStatus]:checked', '#changePublisherOAStatus').val();
        data = {
            'csrfmiddlewaretoken': getCookie('csrftoken'),
            'pk' : publisher_pk,
            'status' : new_status
        };

        $.ajax({
            data : data,
            dataType : 'text',
            error : function( message ) {
                alert('Error: ' + message);
            },
            method : 'POST',
            timeout : 5000,
            url : ajax_url
        });
    });
});


/* ***
 * Search
 * *** */

/* Our strategy is: Reload a part of the page and insert any messages that get delivered */

function updateSearch (ajax_url, data) {
    // slighty fade current results that are going to be replaced
    $('#paperSearchResults').css('opacity', '0.5');
    // turn bird on
    $('#paperSearchWaitingArea').toggleClass('d-none d-flex');

    // call with ajax. it's easy
    $.ajax ({
        contentType : 'application/json',
        data : data,
        dataType : 'json',
        method : 'GET',
        success : function (result) {
            $('#paperSearchResults').html(result.listPapers);
            $('#searchNotifications').html(result.messages);
            // update pie
            updateStats(result.stats);
            // update number of search results
            $('#nbPapersFound').text(
                interpolate(
                    ngettext(
                        '%s paper found',
                        '%s papers found',
                        result.nb_results
                    ),
                    [formatNumbersThousands(result.nb_results)]
                )
            );
        },
        timeout : 5000, // 5 seconds
        url : ajax_url
    });

    // turn bird off
    $('#paperSearchWaitingArea').toggleClass('d-none d-flex');
    // remove opacity
    $('#paperSearchResults').css('opacity', '');
}

/* Prevent standard behaviour of form and execute some JS */
$(function () {
    $('#searchPapers').submit(function (e) {
        e.preventDefault();

        var obj = $(this);

        var ajax_url =  obj.attr('data-ajax-url'); // We take the url from data-ajax-url since it depends on the view
        var data = obj.serializeArray();

        updateSearch(ajax_url, data);
    });
});


/* Refreshes to profil of a user from ORCID.
 * This function is here, because it is related to the search */
$(function () {
    $('#refetchPublications').submit( function () {
        var obj = $(this);
        var researcher_pk = obj.attr('data-researcher-pk');
        var ajax_url = Urls['refetch-researcher'](researcher_pk);

        updateSearch(ajax_url);
    });
});

/* When a message on search is closed, move it from inbox toarchive to not display it again
 * This function is here, because it is related to the search */
$(function () {
    $('.messageAlert').on('closed.bs.alert', function () {
        var obj = $(this);
        var message_pk = obj.attr('data-message-pk');
        var url = Urls['inbox-read'](message_pk);

        $.ajax({
            data: {
                "csrfmiddlewaretoken": getCookie('csrftoken')
            },
            method : 'POST',
            url : url
        });
    });
});

/* Claim and unclaim items to or from profile
 * This function is here, because it is related to the search */

$(function () {
    $('.buttonClaimUnclaim').submit( function () {
        var obj = $(this);
        var paper_pk = obj.attr('data-pk');
        var action = obj.attr('data-action');
        var fadeout = obj.attr('data-fadeout');

        if (action == 'claim') {
            obj.text(gettext('Claiming...'));
            ajax_url = Urls['ajax-claimPaper']();
        }
        else if (action == 'unclaim') {
            obj.text(gettext('Unclaiming...'));
            ajax_url = Urls['ajax-unclaimPaper']();
        }
        else {
            // action currently ongoing
            return
        }

        $.ajax({
            method : 'post',
            data : {
                'pk' : paper_pk,
                "csrfmiddlewaretoken": getCookie('csrftoken')
            },
            dataType : 'json',
            error : function (data) {
                if (action == "claim") {
                    obj.text(gettext('Claiming failed!'));
                }
                else {
                    obj.text(gettext('Unclaiming failed!'));
                }
            },
            success : function (data) {
                if (action == 'claim') {
                    obj.text(gettext('Exclude from my profile'));
                    obj.attr('data-action', 'unclaim');
                }
                else {
                    obj.text(gettext('Include in my profile'));
                    obj.attr('data-action', 'claim');
                    if (fadeout == 'true') {
                        $("#paper-" + paper_pk).fadeOut(300, function() { obj.remove(); });
                    }
                }
            },
            url : ajax_url
        });

    });
});

/* Add and remove items to or from the to-do list 
 * This function is here, because it is related to the search */
$(function () {
    $('.buttonTodoList').submit(function () {
        var obj = $(this)
        var action = $(this).attr('data-action');
        var paper_pk = $(this).attr('data-pk');
        var fadeout = $(this).attr('data-fadeout');

        if (action == 'mark') {
            obj.text(gettext('Adding to todolist'));
            var ajax_url = Urls['ajax-todolist-add']();
        }
        else if (action == 'unmark') {
            obj.text(gettext('Removing from todolist'));
            var ajax_url = Urls['ajax-todolist-remove']();
        }
        else {
            // action currently ongoing
            return
        }

        $.ajax({
            method: 'post',
            url: ajax_url,
            data: {
                "paper_pk": paper_pk,
                "csrfmiddlewaretoken": getCookie('csrftoken')
            },
            dataType: 'json',
            success: function (data) {
                obj.text(data['success_msg']);
                action = data['data-action'];
                /* If object was removed, i.e. server returned 'mark' and fadeout is true, do fadeout */
                if (action == 'mark' && fadeout == 'true') {
                    $("#paper-" + paper_pk).fadeOut(300, function() { obj.remove(); });
                }
                obj.attr('data-action', action);
            },
            error: function (data) {
                obj.text(data['error_msg']);
            }
        });
    });
});


/* ***
 * Statistic
 * *** */

/* Setting colors for the pie */
var stats_colors = ["#FCD206", "#B9C909", "#419BE8", "#dddddd", "#122B52"];
var stats_colors_aggregated = ["#43A000", "#DB1456"];

/* Instead of the full number, which has a lot of digits, we use abbreviations */
function readablizeNumber (number) {
    var units = ['', 'K', 'M', 'G', 'T', 'P'];
    var e = Math.floor(Math.log(number) / Math.log(1000));
    return Math.round((number / Math.pow(1000, e))) + " " + units[e];
}

/* Preprocessing Data */
function preProcessData(data) {
    // The pie only shows active OA categories, which have graph_value = value, while inactive ones have graph_value = 0.
    data.aggregated[0].graph_value = data.aggregated[1].graph_value = 0
    for (var i = 0; i < 5; i++) {
        detail = data.detailed[i]
        detail.graph_value = 0
        if (data.on_statuses.length === 0 || -1 !== $.inArray(detail.id, data.on_statuses)) {
            var j = i < 2 ? 0 : 1
            data.aggregated[j].graph_value += detail.value
            detail.graph_value = detail.value
        }
    }
    // Avoid division by zero when there are no results.
    data.num_tot = data.aggregated[0].graph_value + data.aggregated[1].graph_value
    if (data.num_tot === 0) {
        data.detailed[3].dummy = 1
        data.aggregated[1].dummy = 1
    }
}

/* Showing the Pie itself, which is rendered with d3js */
function showStatsPie (data, chart_id, legend_id) {
    preProcessData(data)

    var detailed_data = data.detailed
    var aggregated_data = data.aggregated
    var w = 201, h = 145;
	var r = 100, mr = 50, imr = 45, ir = 40; // radii
    var color = d3.scale.ordinal().range(stats_colors);
    var color_agg = d3.scale.ordinal().range(stats_colors_aggregated);

	// Create the svg element

    var vis = d3.select("#"+chart_id)
        .append("svg:svg")
            .attr("width", w)
            .attr("height", h)
        .append("svg:g")
            .attr("transform", "translate(" + r + "," + r + ")"); //move the center of the pie chart from 0, 0 to radius, radius

	var parts = vis.selectAll("g.chart")
		.data([detailed_data, aggregated_data])
		.enter()
			.append("svg:g")
				.attr("class", "chart");

	// Outer detailed statistics

    var arc = d3.svg.arc() //this will create <path> elements for us using arc data
        .outerRadius(r)
		.innerRadius(mr);

    var pie = d3.layout.pie() //this will create arc data for us given a list of values
        .value(function(d) { return d.dummy || d.graph_value; }) //we must tell it out to access the value of each element in our data array
		.sort(null)
		.startAngle(-Math.PI/2)
		.endAngle(Math.PI/2);

    var arcs = d3.select(parts[0][0]).selectAll("g.slice") //this selects all <g> elements with class slice (there aren't any yet)
        .data(pie) //associate the generated pie data (an array of arcs, each having startAngle, endAngle and value properties)
        .enter() //this will create <g> elements for every "extra" data element that should be associated with a selection. The result is creating a <g> for every object in the data array
            .append("svg:g") //create a group to hold each slice (we will have a <path> and a <text> element associated with each slice)
                .attr("class", "slice") //allow us to style things in the slices (like text)
            .each(function(d) { this._current = d.value; });

    var paths = arcs.append("svg:path")
                .attr("fill", function(d, i) { return color(i); } ) //set the color for each slice to be chosen from the color function defined above
                .attr("d", arc); //this creates the actual SVG path using the associated data (pie) with the arc drawing function

	// Outer labels
    function translateText(thisArc, d) {
        //set the label's origin to the center of the arc
        //we have to make sure to set these before calling arc.centroid
        d.innerRadius = mr;
        d.outerRadius = r;
        return "translate(" + thisArc.centroid(d) + ")";//this gives us a pair of coordinates like [50, 50]
    }
    function textForLabel(d, i) {
         return (d.data.graph_value === 0 ? "" : readablizeNumber(d.data.graph_value));
    }
	var arcs_text = d3.select(parts[0][0]).selectAll()
        .data(pie)
        .enter()
        .append("svg:g")
        .attr("class", "statsSliceNumber");

    arcs_text.append("svg:text") //add a label to each slice
            .attr("transform", function(d) { return translateText(arc,d); })
            .attr("text-anchor", "middle") //center the text on it's origin
            .text(textForLabel);

	// Inner aggregated statistics

	var arc2 = d3.svg.arc()
        .outerRadius(imr)
		.innerRadius(ir);

	var arcs2 = d3.select(parts[0][1]).selectAll("g.slice")
        .data(pie)
        .enter()
        .append("svg:g")
        .attr("class", "slice");

    arcs2.append("svg:path")
        .attr("fill", function(d, i) { return color_agg(i); } )
        .attr("d", arc2);


	var arcs2_text = d3.select(parts[0][1]).selectAll()
        .data(pie)
        .enter()
        .append("svg:g")
        .attr("class", "statsSliceLegend");

    function lineX(d,i) {
        return arc2.centroid(d)[0];
    }
    function lineY1(d,i) {
        return arc2.centroid(d)[1]+5;
    }
    function lineY2(d,i) {
        return 2 + i*20;
    }
    function hideZero(d) {
        return d.data.graph_value ? null : "none"
    }
    arcs2_text.append("svg:line")
        .attr("x1", lineX)
        .attr("x2", lineX)
        .attr("y1", lineY1)
        .attr("y2", lineY2)
        .attr("style", "stroke:rgb(0,0,0);stroke-width:1");

    arcs2_text.style("display", hideZero)

    function transformAggregatedText(d, i) {
        d.innerRadius = 0;
        d.outerRadius = r/2;
        return "translate(" + arc2.centroid(d)[0] + ", "+ (15 + i*20) +")";
    }
    arcs2_text.append("svg:text")
        .attr("transform", transformAggregatedText)
        .attr("text-anchor", "middle")
        .text(function(d, i) { return aggregated_data[i].label });

	var captions = d3.select("#"+legend_id)

    function updatePie(data) {
        preProcessData(data)

        var arcs = d3.select(parts[0][0]).datum(data.detailed)
        var arcs2 = d3.select(parts[0][1]).datum(data.aggregated)
        var selectArcs = function(elt) { return arcs.selectAll(elt).data(pie).transition() }
        var selectArcs2 = function(elt) { return arcs2.selectAll(elt).data(pie).transition() }

        selectArcs("path")
            .attr("d", arc);
        selectArcs("text")
            .attr("transform",function(d) { return translateText(arc,d) })
            .text(textForLabel);
        selectArcs2("g.statsSliceLegend").style("display", hideZero)
        selectArcs2("path")
            .attr("d", arc2)
        selectArcs2("line")
            .attr("x1", lineX)
            .attr("x2", lineX)
            .attr("y1", lineY1)
            .attr("y2", lineY2);
        selectArcs2("text")
            .attr("transform", transformAggregatedText);
        captions.datum(data.detailed).selectAll("span.detail")
            .data(pie)
            .transition()
		    .text(function(d) { return formatNumbersThousands(d.data.value); });
    }

    return updatePie;
}

/* Insert thousand separator for better readability */
function formatNumbersThousands(value) {
    var thousandSeparator = get_format('THOUSAND_SEPARATOR');
    // Formatting with thousand separator is coming from
    // https://stackoverflow.com/a/2901298
    return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, thousandSeparator);
}
