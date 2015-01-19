// Copyright 2014 Mitchell Kember. Subject to the MIT License.

// How often to synchronize with the server (ms).
var syncInterval = 10000;

// Timeout for AJAX requests (ms).
var ajaxTimeout = 30000;

// Functon to call on the next sync.
var nextSyncFn = null;

// Keep track of lines in the console.
var consoleLines = 0;
var scrolling = true;

// Adds a line of text to the console, and (optionally) scrolls down to it.
function addToConsole(text) {
	var console = document.getElementById('console');
	if (consoleLines == 0) {
		setEnabled('btnc-clear', true);
	} else {
		console.innerHTML += '\n';
	}
	console.innerHTML += " [" + consoleLines + "] " + text;
	scrollConsole();
	consoleLines++;
}

// Scrolls the console down to the bottom line if scrolling is enabled.
function scrollConsole() {
	if (scrolling) {
		var console = document.getElementById('console');
		console.scrollTop = console.scrollHeight;
	}
}

// Clears the console and resets the counter.
function clearConsole() {
	if (isEnabled('btnc-clear')) {
		var console = document.getElementById('console');
		console.innerHTML = "";
		consoleLines = 0;
		setEnabled('btnc-clear', false);
	}
}

// Returns true if the button is enabled and false otherwise.
function isEnabled(id) {
	return document.getElementById(id).className != 'disabled-button';
}

// Enable or disable a button by its element ID.
function setEnabled(id, yes) {
	document.getElementById(id).className = yes? '' : 'disabled-button';
}

// Activate or disactivate a button by its element ID.
function setActive(id, yes) {
	document.getElementById(id).className = yes? 'active' : '';
}

// Toggles the auto-scrolling whenever a new line is added to the console.
function btnFreeScroll() {
	btn = document.getElementById('btnc-freescroll');
	if (scrolling) {
		btn.innerHTML = 'Scroll';
	} else {
		btn.innerHTML = 'Free';
	}
	scrolling = !scrolling;
}

// Keep track of the currently executing program.
var currentProgram = 'tracie';
var allPrograms = ['avoid', 'tracie'];

// Disables the specified program button and enables the rest.
function enableOtherPrograms(name) {
	if (name != 'calib') {
		setEnabled('btnc-' + name, false);
	}
	for (var i = 0, len = allPrograms.length; i < len; i++) {
		if (allPrograms[i] != name) {
			setEnabled('btnc-' + allPrograms[i], true);
		}
	}
}

// Tells the server to switch programs. Disables the clicked button and enables
// the others (only one can be selected at a time).
function switchProgram(name) {
	if (name == currentProgram) {
		return;
	}
	enableOtherPrograms(name);
	setStartStop(true);
	setEnabled('btnc-reset', false);
	setVisible('btnc-draw', name == 'tracie');
	if (name == 'tracie' && enoughPoints()) {
		nextSyncFn = sendPoints;
	}
	send('program:' + name);
	currentProgram = name;
}

// Either switches to the calibration program or displays the `att` value.
function btnCalib() {
	if (currentProgram != 'calib') {
		switchProgram('calib');
	} else {
		send('short:att');
	}
}

// Keep track of the state of program execution.
var running = false;

// Sets the text of the start/stop button according to the action.
function setStartStop(start) {
	var btn = document.getElementById('btnc-startstop');
	if (start) {
		btn.innerHTML = 'Start';
	} else {
		btn.innerHTML = 'Stop';
	}
}

// Tells the server to start/stop the program. Changes the text of the button
// and enables/disables the reset button accordingly.
function btnStartStop() {
	toggleStartStop();
	if (running) {
		traceStop();
	} else {
		traceStart();
	}
}

function toggleStartStop() {
	if (running) {
		setStartStop(true);
		running = false;
		send('control:stop');
	} else {
		setStartStop(false);
		setEnabled('btnc-reset', true);
		running = true;
		send('control:start');
	}
}

// Tells the server to stop and reset the program. Changes the text of the
// start/stop button and disables itself.
function btnReset() {
	if (isEnabled('btnc-reset')) {
		setStartStop(true);
		setEnabled('btnc-reset', false);
		send('control:reset');
		running = false;
	}
}

// Changes the value of a parameter in the program based on the text fields.
function setParameter() {
	var name = document.getElementById('c-param-name').value;
	var val = document.getElementById('c-param-value').value;
	send('set:' + name + '=' + val);
}

// Sends a message to the server and adds the response to the console.
function send(message) {
	post(message, function(text) {
		addToConsole(text);
		synchronize();
	}, function(sn) {
		addToConsole(message + " failed (" + String(sn) + ")");
	}, function() {
		addToConsole(message + " timed out");
	});
}

// Requests the latest status from the server, adds the response to the console,
// and repeats immediately. There is no delay because the server uses
// long-polling, so the connection will stay open until there is a new status.
function updateStatus() {
	post('long:status', function(text) {
		addToConsole(text);
		updateStatus();
	}, updateStatus, updateStatus);
}

// Synchronizes the client state with the server.
function synchronize() {
	post('short:sync', function(text) {
		var vals = text.split(' ');
		var sProgram = vals[0];
		var sRunning = (vals[1] == 'True');
		var sCanReset = (vals[2] == 'True');
		enableOtherPrograms(sProgram);
		setStartStop(!sRunning);
		setEnabled('btnc-reset', sCanReset);
		setVisible('btnc-draw', sProgram == 'tracie');
		currentProgram = sProgram;
		running = sRunning;
		if (traceMode && !running) {
			toggleTrace();
		}
		if (nextSyncFn) {
			nextSyncFn();
			nextSyncFn = null;
		}
	}, function(sn) {
		addToConsole("sync failed (" + String(sn) + ")");
	}, function() {
		addToConsole("sync timed out");
	})
}

// Sends data to the server via a POST request. Calls the onreceive function
// with the response text as the argument when the request is completed. Calls
// the onfail function with the response status if it is not 200 OK. Calls the
// ontimeout function if the request times out.
function post(data, onreceive, onfail, ontimeout) {
	var r = new XMLHttpRequest();
	r.onreadystatechange = function() {
		if (r.readyState == 4) {
			if (r.status == 200) {
				onreceive(r.responseText);
			} else if (r.status != 0) {
				// For some reason, if the request times out, it calles the
				// `ontimeout` function but also completes the request with a
				// status of zero. So let's ignore that.
				onfail(r.status);
			}
		}
	};
	r.open('POST', '/', true);
	r.setRequestHeader('Content-type', 'application/json');
	r.timeout = ajaxTimeout;
	r.ontimeout = ontimeout;
	r.send(data);
}

// Keep track of the currently visible view.
var currentView = 'controls';
var allViews = ['controls', 'param-help', 'drawing'];

// Sets the visibility of the element indicated by the given identifier.
function setVisible(id, visible) {
	document.getElementById(id).style.display = visible? 'block' : 'none';
}

// Shows the named view and hides the others.
function showView(name) {
	setVisible(name, true);
	for (var i = 0, len = allViews.length; i < len; i++) {
		if (allViews[i] != name) {
			setVisible(allViews[i], false);
		}
	}
}

// Switches to the named view.
function switchToView(view) {
	if (view == 'controls') {
		if (currentView == 'drawing') {
			removeEventListeners();
			// Don't send the points if it's tracing or running.
			if (!running && !traceMode) {
				if (enoughPoints()) {
					sendPoints();
				} else {
					addToConsole("not enough points");
				}
			}
		}
	} else if (view == 'param-help') {
		generateParamHelp();
	} else if (view == 'drawing') {
		addEventListeners();
	}
	showView(view);
	currentView = view;
	scrollConsole();
}

// Generates the help information for the current program and inserts the HTML
// into the param-help section.
function generateParamHelp() {
	post('short:param-help', function(data) {
		var codes = JSON.parse(data);
		var html = Object.keys(codes).sort().map(function(sc) {
			return '<div><dt>' + sc + '</dt><dd>' + codes[sc] + '</dd></div>';
		}).join('');
		document.getElementById('pdefinitions').innerHTML = html;
	}, function(sn) {
		addToConsole("help fetch failed (" + String(sn) + ")");
	}, function() {
		addToConsole("help fetch timed out");
	});
}

window.onload = function() {
	synchronize();
	addToConsole("in sync with server");
	// Sync every so often.
	setInterval(synchronize, syncInterval);
	// Begin the long-polling.
	updateStatus();
	// Ensure that only one page is showing.
	showView(currentView);
	setupCanvas();
}
