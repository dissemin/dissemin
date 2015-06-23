var stats_colors = ["#F68212", "#FCD821", "#419BE8", "#eeeeee", "#122B52"];

function showStatsPie (data, target_id) {
    var w = 220, h = 120, r = 100;
    var color = d3.scale.ordinal().range(stats_colors);

    var vis = d3.select("#"+target_id).select(".statspie_graph")
        .append("svg:svg")              //create the SVG element inside the <body>
        .data([data])                   //associate our data with the document
            .attr("width", w)           //set the width and height of our visualization (these will be attributes of the <svg> tag
            .attr("height", h)
        .append("svg:g")                //make a group to hold our pie chart
            .attr("transform", "translate(" + r + "," + r + ")")    //move the center of the pie chart from 0, 0 to radius, radius

    var arc = d3.svg.arc()              //this will create <path> elements for us using arc data
        .outerRadius(r)
		.innerRadius(r/2);

    var pie = d3.layout.pie()           //this will create arc data for us given a list of values
        .value(function(d) { return d.value; }) //we must tell it out to access the value of each element in our data array
		.sort(null)
		.startAngle(-Math.PI/2)
		.endAngle(Math.PI/2);

    var arcs = vis.selectAll("g.slice")     //this selects all <g> elements with class slice (there aren't any yet)
        .data(pie)                          //associate the generated pie data (an array of arcs, each having startAngle, endAngle and value properties) 
        .enter()                            //this will create <g> elements for every "extra" data element that should be associated with a selection. The result is creating a <g> for every object in the data array
            .append("svg:g")                //create a group to hold each slice (we will have a <path> and a <text> element associated with each slice)
                .attr("class", "slice");    //allow us to style things in the slices (like text)

        arcs.append("svg:path")
                .attr("fill", function(d, i) { return color(i); } ) //set the color for each slice to be chosen from the color function defined above
                .attr("d", arc);                                    //this creates the actual SVG path using the associated data (pie) with the arc drawing function

        arcs.append("svg:text")                                     //add a label to each slice
                .attr("transform", function(d) {                    //set the label's origin to the center of the arc
                //we have to make sure to set these before calling arc.centroid
                d.innerRadius = r/2;
                d.outerRadius = r;
                return "translate(" + arc.centroid(d) + ")";        //this gives us a pair of coordinates like [50, 50]
            })
            .attr("text-anchor", "middle")                          //center the text on it's origin
            .text(function(d, i) { return (data[i].value == 0 ? "" : data[i].value); });        //get the label from our original data array

	makeCaptions(data, d3.select("#"+target_id).select(".statspie_caption"));
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
