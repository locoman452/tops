var totalMessages = 0;
var displayedMessages = 0;
var maxMessages = 10;
var timer = null;
var uid = null;

function stopTimer() {
	if(timer != null) {
		window.clearInterval(timer);
		timer = null;
	}
}

function ajaxError(request, textStatus, errorThrown) {
	// typically only one of textStatus or errorThrown will have info
	stopTimer();
	var msg = 'Server communication error [status "' + textStatus + '"';
	if(errorThrown != undefined) {
		msg += '; error thrown "' + errorThrown + '"';
	}
	msg += ']. Update OPTIONS to try reconnecting.';
	addLocalRecord(msg);
}

function addLocalRecord(body) {
	addRecord(0,{
		tstamp: new Date(),
		level: 'LOCAL',
		source: '(local)',
		body: body
	});
}

function addRecord(index,record) {
	// insert a clone of the record template with this record's fields inserted
	var when = new Date(record.tstamp);
	$("#content table").append(
		$("#template").clone().removeAttr("id").addClass("message").addClass(record.level)
			.find(".when").html(when.toLocaleTimeString()).end()
			.find(".source").html(record.source).end()
			.find(".body").html(record.body).attr('title',record.level).end()
	);
	// update message counts
	totalMessages++;
	displayedMessages++;
	// alternate rows have a slightly different color
	if(totalMessages % 2 == 0) {
		$("#content table tr:last").addClass("zebra");
	}
	// trim the oldest messages if necessary
	while(maxMessages > 0 && displayedMessages > maxMessages) {
		$(".message:first").remove();
		displayedMessages--;
	}
	// update the message count display
	$("#msgCount").html(displayedMessages);
	// scroll to the bottom of the message area so this new message is visible
	$("#content").each(function() { this.scrollTop = this.scrollHeight; });
}

function processRecords(data,textStatus) {
	var now = new Date();
	$("#lastUpdate").html(now.toLocaleString()+' '+textStatus);
	$.each(data.items,addRecord);
}

function startUpdate() {
	$.getJSON('/feed',{'uid':uid},processRecords);
}

function resetOptions() {
	$("#updateInterval").find(":input").val(["1"]);
	$("#maxMessages").find(":input").val(["1000"]);
	$("#sourceFilter").val("*");
	$("#minLevel").find(":input").val(["DEBUG"]);
}

function updateOptions() {
	// clear any running update timer
	stopTimer();
	// extract the new options from the HTML inputs
	var updateInterval = $("#updateInterval :checked").val();
	maxMessages = $("#maxMessages :checked").val();
	var sourceFilter = $("#sourceFilter").val();
	var minLevel = $("#minLevel :checked").val();
	// generate a local log message describing the new options
	var updateMsg = 'Using OPTIONS: update interval = ' + updateInterval +
		's, max messages = ' + maxMessages + ', source filter is "' + sourceFilter +
		'", min level = ' + minLevel;
	addLocalRecord(updateMsg);
	// tell the server our new options
	$.post('/feed',{
		'uid': uid,
		'sourceFilter': sourceFilter,
		'minLevel': minLevel
	});
	// (re)start timed updates, converting seconds to ms
	timer = window.setInterval('startUpdate()',1000*updateInterval);
}

$(document).ready(
	function() {
		uid = generateID();
		$.ajaxSetup({
			timeout: 5000, /* ms */
			error: ajaxError
		});
		$("#warning").hide();
		resetOptions();
		updateOptions();
		$("#optionsDialog").hide();
		$("#optionsButton").click(function() {
			$("#optionsDialog").show().dialog({
				modal: true,
				overlay: { opacity: 0.5, background: "black" },
				resizable: false,
				width: "500px",
				height: "320px",
				buttons: {
					"RESET": resetOptions,
					"CANCEL": function() { $(this).dialog("close"); },
					"UPDATE": function() { $(this).dialog("close"); updateOptions(); }
				}
			});
		});
		$("#jsready").show();
	}
);
