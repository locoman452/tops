// Returns a "unique" ID that allows the server to distinguish between two tabs/windows
// of the same browser visiting the same page (which means they share a session cookie)
function generateID() {
	var chunkSize = 1 << 16; // 2^16
	var now = new Date();
	var part1 = new Number(now.getTime() % chunkSize);
	var part2 = new Number(Math.floor(chunkSize*Math.random()));
	return part1.toString(16) + part2.toString(16);
}

// Returns a dictionary of name,value pairs derived from the query string of this
// window's URL, if any.
function parseQuery() {
	var query = { };
	if(window.location.search.length == 0) {
		// we don't have a query string
		return query;
	}
	// strip off the leading '?' and split into name=value assignments	
	var assignments = window.location.search.substring(1).split('&');
	for(var index = 0; index < assignments.length; index++) {
		var tokens = assignments[index].split('=');
		if(tokens.length == 2) {
			query[tokens[0]] = tokens[1];
		}
	}
	return query;
}

// Scroll to the bottom of the element(s) matching the specified jQuery
function scrollToBottom(query) {
	$(query).each(function() { this.scrollTop = this.scrollHeight; });
}

// Stop the specified window timer routine
function stopTimer(timer) {
	if(timer != null) {
		window.clearInterval(timer);
		timer = null;
	}
}
