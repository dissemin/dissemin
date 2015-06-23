var stats_colors = ["#F68212", "#FCD821", "#419BE8", "#eeeeee", "#122B52"];
var stats_colors_aggregated = ["#D2ED1D", "#E62029"];

function showStatsPie (detailed_data, aggregated_data, target_id) {
    var w = 220, h = 145, r = 100;
    var color = d3.scale.ordinal().range(stats_colors);
    var color_agg = d3.scale.ordinal().range(stats_colors_aggregated);

	// Create the svg element
	
    var vis = d3.select("#"+target_id).select(".statspie_graph")
        .append("svg:svg")
            .attr("width", w)
            .attr("height", h)
        .append("svg:g")
            .attr("transform", "translate(" + r + "," + r + ")")    //move the center of the pie chart from 0, 0 to radius, radius

	var parts = vis.selectAll("g.chart")
		.data([detailed_data, aggregated_data])  
		.enter()
			.append("svg:g")
				.attr("class", "chart")

	// Outer detailed statistics
				
    var arc = d3.svg.arc()              //this will create <path> elements for us using arc data
        .outerRadius(r)
		.innerRadius(r/2);

    var pie = d3.layout.pie()           //this will create arc data for us given a list of values
        .value(function(d) { return d.value; }) //we must tell it out to access the value of each element in our data array
		.sort(null)
		.startAngle(-Math.PI/2)
		.endAngle(Math.PI/2);

    var arcs = d3.select(parts[0][0]).selectAll("g.slice")     //this selects all <g> elements with class slice (there aren't any yet)
        .data(pie)                          //associate the generated pie data (an array of arcs, each having startAngle, endAngle and value properties) 
        .enter()                            //this will create <g> elements for every "extra" data element that should be associated with a selection. The result is creating a <g> for every object in the data array
            .append("svg:g")                //create a group to hold each slice (we will have a <path> and a <text> element associated with each slice)
                .attr("class", "slice");    //allow us to style things in the slices (like text)

        arcs.append("svg:path")
                .attr("fill", function(d, i) { return color(i); } ) //set the color for each slice to be chosen from the color function defined above
                .attr("d", arc);                                    //this creates the actual SVG path using the associated data (pie) with the arc drawing function

	// Outer labels
				
	var arcs_text = d3.select(parts[0][0]).selectAll("g.slicetext")
        .data(pie)
        .enter()
            .append("svg:g")
                .attr("class", "slicetext");
		
        arcs_text.append("svg:text")                                     //add a label to each slice
                .attr("transform", function(d) {                    //set the label's origin to the center of the arc
                //we have to make sure to set these before calling arc.centroid
                d.innerRadius = r/2;
                d.outerRadius = r;
                return "translate(" + arc.centroid(d) + ")";        //this gives us a pair of coordinates like [50, 50]
            })
            .attr("text-anchor", "middle")                          //center the text on it's origin
            .text(function(d, i) { return (detailed_data[i].value == 0 ? "" : detailed_data[i].value); });        //get the label from our original data array

	// Inner aggregated statistics		
	
	var arc2 = d3.svg.arc()
        .outerRadius(r/2)
		.innerRadius(0);
		
	var arcs2 = d3.select(parts[0][1]).selectAll("g.slice")     //this selects all <g> elements with class slice (there aren't any yet)
        .data(pie)                          //associate the generated pie data (an array of arcs, each having startAngle, endAngle and value properties) 
        .enter()                            //this will create <g> elements for every "extra" data element that should be associated with a selection. The result is creating a <g> for every object in the data array
            .append("svg:g")                //create a group to hold each slice (we will have a <path> and a <text> element associated with each slice)
                .attr("class", "slice");    //allow us to style things in the slices (like text)

        arcs2.append("svg:path")
                .attr("fill", function(d, i) { return color_agg(i); } ) //set the color for each slice to be chosen from the color function defined above
                .attr("d", arc2);                                    //this creates the actual SVG path using the associated data (pie) with the arc drawing function

	
	var arcs2_text = d3.select(parts[0][1]).selectAll("g.slicetext")
        .data(pie)
        .enter()
            .append("svg:g")
                .attr("class", "slicetext");
				
        arcs2_text.append("svg:text")                                     //add a label to each slice
            .attr("transform", function(d) {                    //set the label's origin to the center of the arc
                //we have to make sure to set these before calling arc.centroid
                d.innerRadius = 0;
                d.outerRadius = r/2;
                return "translate(" + arc2.centroid(d) + ")";        //this gives us a pair of coordinates like [50, 50]
            })
            .attr("text-anchor", "middle")                          //center the text on it's origin
            .text(function(d, i) { return (aggregated_data[i].value == 0 ? "" : aggregated_data[i].value); });        //get the label from our original data array
		
		arcs2_text.append("svg:line")
			.attr("x1", function(d, i) { return arc2.centroid(d)[0] + (i==0 ? -1 : 1)*10 })
			.attr("x2", function(d, i) { return arc2.centroid(d)[0] + (i==0 ? -1 : 1)*10 })
			.attr("y1", function(d, i) { return arc2.centroid(d)[1] + 6 })
			.attr("y2", function(d, i) { return 2 + i*20; })
            .attr("style", "stroke:rgb(0,0,0);stroke-width:1")
		
		arcs2_text.append("svg:text")                                     //add a label to each slice
                .attr("transform", function(d, i) {                    //set the label's origin to the center of the arc
                //we have to make sure to set these before calling arc.centroid
                d.innerRadius = 0;
                d.outerRadius = r/2;
                return "translate(" + arc2.centroid(d)[0] + ", "+ (15 + i*20) +")";        //this gives us a pair of coordinates like [50, 50]
            })
            .attr("text-anchor", "middle")                          //center the text on it's origin
            .text(function(d, i) { return (aggregated_data[i].label); });        //get the label from our original data array
	
	makeCaptions(detailed_data, d3.select("#"+target_id).select(".statspie_caption"));
}

function makeCaptions (data, target) {
	var captions = target.selectAll("div")
		.data(data)
		.enter()
			.append("div")
			.attr("class", "stats_caption_line")

		captions.append("div")
			.attr("class", "stats_caption_box")
			.style("background-color", function(d, i) {return stats_colors[i]; })

		captions.append("a")
			.attr("class", "stats_caption_text")
            .attr("href", function(d) { return d.url })
			.text(function(d) { return d.label; })
			.append("span")
				.attr("class", "detail")
				.text(function(d) { return " ("+d.value+")"; });
}
