var stats_colors = ["#FCD206", "#B9C909", "#419BE8", "#dddddd", "#122B52"];
var stats_colors_aggregated = ["#43A000", "#DB1456"];

function readablizeNumber (number) {
  var units = ['', 'K', 'M', 'G', 'T', 'P'];
  var e = Math.floor(Math.log(number) / Math.log(1000));
  return Math.round((number / Math.pow(1000, e))) + " " + units[e];
}

function preProcessData(data) {
    // The pie only shows active OA categories, which have graph_value = value,
    // while inactive ones have graph_value = 0.
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

function showStatsPie (data, target_id) {
    preProcessData(data)

    var detailed_data = data.detailed
    var aggregated_data = data.aggregated
    var w = 201, h = 145;
	var r = 100, mr = 50, imr = 45, ir = 40; // radii
    var color = d3.scale.ordinal().range(stats_colors);
    var color_agg = d3.scale.ordinal().range(stats_colors_aggregated);
	
	// Create the svg element
	
    var vis = d3.select("#"+target_id).select(".statspie_graph")
        .append("svg:svg")
            .attr("width", w)
            .attr("height", h)
        .append("svg:g")
            .attr("transform", "translate(" + r + "," + r + ")");    //move the center of the pie chart from 0, 0 to radius, radius

	var parts = vis.selectAll("g.chart")
		.data([detailed_data, aggregated_data])  
		.enter()
			.append("svg:g")
				.attr("class", "chart");

	// Outer detailed statistics
				
    var arc = d3.svg.arc()              //this will create <path> elements for us using arc data
        .outerRadius(r)
		.innerRadius(mr);

    var pie = d3.layout.pie()           //this will create arc data for us given a list of values
        .value(function(d) { return d.dummy || d.graph_value; }) //we must tell it out to access the value of each element in our data array
		.sort(null)
		.startAngle(-Math.PI/2)
		.endAngle(Math.PI/2);

    var arcs = d3.select(parts[0][0]).selectAll("g.slice")     //this selects all <g> elements with class slice (there aren't any yet)
        .data(pie)                          //associate the generated pie data (an array of arcs, each having startAngle, endAngle and value properties) 
        .enter()                            //this will create <g> elements for every "extra" data element that should be associated with a selection. The result is creating a <g> for every object in the data array
            .append("svg:g")                //create a group to hold each slice (we will have a <path> and a <text> element associated with each slice)
                .attr("class", "slice")    //allow us to style things in the slices (like text)
            .each(function(d) { this._current = d.value; });

    var paths = arcs.append("svg:path")
                .attr("fill", function(d, i) { return color(i); } ) //set the color for each slice to be chosen from the color function defined above
                .attr("d", arc);                                    //this creates the actual SVG path using the associated data (pie) with the arc drawing function

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
	var arcs_text = d3.select(parts[0][0]).selectAll("g.slicetext")
        .data(pie)
        .enter()
            .append("svg:g")
                .attr("class", "slicetext");
		
    arcs_text.append("svg:text")                                     //add a label to each slice
            .attr("transform", function(d) { return translateText(arc,d); })
            .attr("text-anchor", "middle")                          //center the text on it's origin
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

	
	var arcs2_text = d3.select(parts[0][1]).selectAll("g.slicetext")
        .data(pie)
        .enter()
        .append("svg:g")
        .attr("class", "slicetext");
		
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

	var captions = d3.select("#"+target_id).select(".statspie_caption");

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
        selectArcs2("g.slicetext").style("display", hideZero)
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
		    .text(function(d) { return d.data.value; });
    }

    return updatePie;
}
