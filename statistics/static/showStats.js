var stats_colors = ["#FCD206", "#B9C909", "#419BE8", "#dddddd", "#122B52"];
var stats_colors_aggregated = ["#43A000", "#DB1456"];

function showStatsPie (detailed_data, aggregated_data, target_id, current_state) {
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
        .value(function(d) { return d.value; }) //we must tell it out to access the value of each element in our data array
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
         return (d.value == 0 ? "" : d.value);
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
    arcs2_text.append("svg:line")
        .attr("x1", lineX)
        .attr("x2", lineX)
        .attr("y1", lineY1)
        .attr("y2", lineY2)
        .attr("style", "stroke:rgb(0,0,0);stroke-width:1");

    function transformAggregatedText(d, i) {
        d.innerRadius = 0;
        d.outerRadius = r/2;
        return "translate(" + arc2.centroid(d)[0] + ", "+ (15 + i*20) +")";
    }
    arcs2_text.append("svg:text")
            .attr("transform", transformAggregatedText)
        .attr("text-anchor", "middle")
        .text(function(d, i) { return (aggregated_data[i].label); });

	var captions = d3.select("#"+target_id).select(".statspie_caption");
    makeCaptions(detailed_data, captions, current_state);

    function updatePie(data) {
        var newDetailedData = data.detailed
        var newAggregatedData = data.aggregated
        d3.select(parts[0][0]).datum(newDetailedData).selectAll("path")
         .data(pie)
         .transition()
         .attr("d", arc);   
        d3.select(parts[0][0]).datum(newDetailedData).selectAll("text")
         .data(pie)
         .transition()
         .attr("transform",function(d) { return translateText(arc,d) })
         .text(textForLabel);
        d3.select(parts[0][1]).datum(newAggregatedData).selectAll("path")
         .data(pie)
         .transition()
         .attr("d", arc2);   
        d3.select(parts[0][1]).datum(newAggregatedData).selectAll("line")
          .data(pie)
          .transition()
          .attr("x1", lineX)
          .attr("x2", lineX)
          .attr("y1", lineY1)
          .attr("y2", lineY2);
        d3.select(parts[0][1]).datum(newAggregatedData).selectAll("text")
          .data(pie)
          .transition()
          .attr("transform", transformAggregatedText);
        captions.datum(newDetailedData).selectAll("span.detail")
            .data(pie)
            .transition()
		    .text(function(d) { return " ("+d.value+")"; });
    }

    return updatePie;
}

function makeCaptions (data, target, current_state) {
	var captions = target.selectAll("div")
		.data(data)
		.enter()
			.append("div")
			.attr("class", "stats_caption_line")

		captions.append("div")
			.attr("class", "stats_caption_box")
			.append("span")
				.attr("class", "stats_caption_color")
				.style("background-color", function(d, i) {return stats_colors[i]; })

		captions.append("a")
			.attr("class", function(d) {
                if(d.id == current_state){
                    return "stats_caption_label activated";
                } else {
                    return "stats_caption_label"; }
            })
            .attr("href", function(d) {
                if(d.id == current_state) {
                    return d.baseurl;
                } else {
                    return d.url;
                } })
			.text(function(d) { return d.label; })
			.append("span")
				.attr("class", "detail")
				.text(function(d) { return d.value; });
    return captions;
}
