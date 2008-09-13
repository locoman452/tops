var updateInterval = 1; // seconds
var channels = [ ];
var timer = null;
var uid = null;

function ajaxError(request, textStatus, errorThrown) {
	stopTimer(timer);
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
	var channelDisplay =
		$("#template").clone().attr("id",channel.name).addClass("channel")
		.find(".name").html(channel.name).end();
	channels.push(channelDisplay.find('.value').get(0));
	$("#content").append(channelDisplay);
}

function displayChannels(data,textStatus) {
	$(".channel").remove();
	channels = [ ];
	$.each(data.channels,displayChannel);
	// scroll to the bottom of the channels display area so this new channel is visible
	scrollToBottom("#content");
	// update the channel count display
	$("#chanCount").html(data.channels.length);
	// (re)start timed updates, converting seconds to ms
	stopTimer(timer);
	timer = window.setInterval('startUpdate()',1000*updateInterval);
}

function updateChannel(index,value) {
	channels[index].innerHTML = value;
}

function updateChannels(data,textStatus) {
	var now = new Date();
	$("#lastUpdate").html(now.toLocaleString()+' '+textStatus);
	$.each(data.values,updateChannel);
}

function startUpdate() {
	$.get('/feed',{'uid':uid},updateChannels,"json");
}

function resetOptions() {
	$("#updateInterval").find(":input").val(["1"]);
}

function updateOptions() {
	// extract the new options from the HTML inputs
	updateInterval = $("#updateInterval :checked").val();
	// generate a local log message describing the new options
	var updateMsg = 'Using OPTIONS: update interval = ' + updateInterval;
	// (re)start timed updates, converting seconds to ms
	if(timer != null) {
		stopTimer(timer);
		timer = window.setInterval('startUpdate()',1000*updateInterval);
	}
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
		// install the handler for our pattern text input
		$("input#pattern").change(
			function () {
				stopTimer(timer);
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
