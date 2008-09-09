function State(options) {
	for (var attr in options) {
		this[attr] = options[attr]
	}
	if(!('name' in this)) {
		alert('state is missing name attribute');
	}
	State.namespace[this.name] = this;
}

State.prototype.enter = function() {
	if(this.initial == null) {
		if(this.compound) lert('no initial state specified for compound state "' + this.name + '"');
		return this;
	}
	else {
		return this.initial.enter();
	}
}

State.prototype.recall = function() {
	if(this.last == null) {
		if(this.compound) alert('no history recorded for compound state "' + this.name + '"');
		return this;
	}
	else {
		return this.last.recall();
	}
}

State.prototype.select = function() {
	this.elem.className = 'selected state';
	this.title.className = 'selected title';
	for(var trigindex in this.triggers) {
		trigger = this.triggers[trigindex];
		trigger.className = 'selected trigger';
		trigger.onclick = this.trighandlers[trigindex];
	}
	// update our parent's history
	if(this.parent) this.parent.last = this;
}

State.prototype.deselect = function() {
	this.elem.className = 'state';
	this.title.className = 'title';
	for(var trigindex in this.triggers) {
		trigger = this.triggers[trigindex];
		trigger.className = 'trigger';
		trigger.onclick = null;
	}
}

State.current = null;
State.namespace = new Array();

State.bind = function(name) {
	return function() { State.setState(name) }
}

State.initialize = function(root) {
	// convert references by name to object references
	for(var name in State.namespace) {
		var state = State.namespace[name];
		state.elem = document.getElementById(name);
		for(var index = 0; index < state.elem.childNodes.length; index++) {
			child = state.elem.childNodes.item(index);
			if(child.className == 'title') {
				state.title = child;
			}
			else if(child.className == 'triggers') {
				state.triggers = [];
				state.trighandlers = [];
				for(var trigindex = 0; trigindex < child.childNodes.length; trigindex++) {
					var elem = child.childNodes[trigindex];
					if(elem.className != 'trigger') continue;
					state.triggers[trigindex] = elem;
					var target = elem.getAttribute('target');
					state.trighandlers[trigindex] = State.bind(target);
				}
			}
		}
		if('initial' in state) {
			state.initial = State.namespace[state.initial];
		}
		else {
			state.initial = null;
		}
		if('parent' in state) {
			state.parent = State.namespace[state.parent];
		}
		else {
			state.parent = null;
		}
		state.last = null;
	}
	// initialize a keypress handler
	document.onkeydown = State.reveal;
	// set the initial state
	State.setState(root);
}

State.setState = function(name) {
	if(name.substring(0,7) == 'recall(') {
		recall = true;
		name = name.substring(7,name.length-1);
	}
	else {
		recall = false;
	}
	if(!(name in State.namespace)) {
		alert('setState: no such state "' + name + '"');
	}
	else {
		// remove the styling of any currently selected node
		if(State.current != null) {
			var iter = State.current;
			do { iter.deselect(); } while(iter = iter.parent);
		}
		// update our current state
		var state = State.namespace[name];
		var newstate = null;
		if(recall) {
			newstate = state.recall();
		}
		else {
			newstate = state.enter();
		}
		State.current = newstate;
		// jump browser to display the new state without cluttering its history buffer
		// window.location.replace('#'+newstate.name);
		// apply styling and history to the newly selected node
		var iter = newstate;
		do { iter.select();	} while(iter = iter.parent);
	}
}

State.reveal = function(e) {
	if(!e || e.keyCode != 32 || !State.current) return true;
	window.location.replace('#'+State.current.name);
	return false;
}
