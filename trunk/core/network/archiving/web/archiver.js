var totalMessages = 0;
var displayedMessages = 0;
var maxMessages = 10;
var timer = null;
var uid = null;

function ajaxError(request, textStatus, errorThrown) {
	// typically only one of textStatus or errorThrown will have info
	var msg = 'Server communication error [status "' + textStatus + '"';
	if(errorThrown != undefined) {
		msg += '; error thrown "' + errorThrown + '"';
	}
	msg += ']. Update OPTIONS to try reconnecting.';
	alert(msg);
}

function displayChannel(index,channel) {
	// insert a clone of the channel template
	$("#content").append(
		$("#template").clone().removeAttr("id").addClass("channel")
			.find(".name").html(channel.name).end()
	);
	// scroll to the bottom of the channels display area so this new channel is visible
	$("#content").each(function() { this.scrollTop = this.scrollHeight; });
}

function displayChannels(data,textStatus) {
	var now = new Date();
	$("#lastUpdate").html(now.toLocaleString()+' '+textStatus);
	$.each(data.items,displayChannel);
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
	alert(updateMsg);
	// tell the server our new options
	$.post('feed',{
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
		//updateOptions();
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
		// install the handler for our pattern text input
		$("input#pattern").change(
			function () {
				$("#intro-help").hide();
				$.post('/feed',{'uid':uid,'pattern':$("input#pattern").val()},
					displayChannels,"json");
			}
		);
		// did we get a pattern in the URL?
		var query = parseQuery();
		if('pattern' in query) {
			// display the pattern we have been passed and get the results
			$("input#pattern").val(query['pattern']);
			$("#intro-help").hide();
		}
		else {
			// prompt the user to enter a pattern
			var pattern = $("input#pattern").val('*').get(0);
			$(window).load(
				function() {
					pattern.select();
					pattern.focus();
				}
			);
		}
		$("#jsready").show();
	}
);
