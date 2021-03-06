// ********************************************
// TREE DIALOGS: based on /reference.dialogs.js
// --------------------------------------------
// Version: 1.0
// Date: 14-12-2019

// ===========================
// Dialog windows declarations
// ===========================

var IsES6 = 0;

var TEMPLATE_SERVICE = 'service:';

function make_reference_mapping(columns, headers) {
    var mapping = new Object();

    // -------------------------------------
    // Mapping is Dict: key -> (name, value)
    // -------------------------------------

    for (i=0; i<columns.length; i++) {
        var name = columns[i];
        var header = headers[name];
        var key = header.key;
        var value = header.value;

        mapping[key] = [name, value];
    }

    return mapping;
}

function get_attr(mapping, key, attr) {
    var x = mapping[key];
    return is_null(x) ? '' : (attr == 'name' ? x[0] : (attr == 'value' ? x[1] : null));
}

function get_input_type(type, link) {
    return link ? 'text' : (['int','bigint'].indexOf(type) > -1 ? 'number' : (type == 'date' ? 'date' : 'text'));
}

// =========================================================== //

var $ReferenceDialog = {
    base         : $BaseScreenDialog,

    // ======================
    // Reference Dialog Class
    // ======================

    IsTrace : 0, IsDebug : 0, IsDeepDebug : 0, IsLog : 0,

    // ---------------------
    // Base class attributes
    // ---------------------

    // ID of base container
    id           : null,
    // Mode of screen available
    mode         : 'client',
    // Flag to use cache
    with_cache   : 0,
    // Flag to lock screen
    with_lock    : 0,

    check_limit_height  : 0,

    // ----------------
    // Local attributes
    // ----------------

    default_size : 
    {
        'stocklist'     : [880, 724+29*10],
        'default'       : [500, 400]
    },

    actions         : {'default' : 620, 'command' : null, 'mode' : null},
    timeout         : 300,
    timer           : null,

    // ---------
    // Constants
    // ---------

    min_width       : 400,
    min_height      : 260,

    search_width    : 300,
    offset          : 
    {
        'height'    : 208,   // ???????????????? ???? ???????????? (??????????????????+????????????)
        'padding'   : 10,    // padding + border ????????????
    },

    // ---------------
    // Form's controls 
    // ---------------

    container       : null,
    box             : null,
    table           : null,
    head            : null,
    content         : null,
    panel           : null,
    form            : null,

    actual_size     : new Object(),
    state           : new Object(),
    last            : null,
    mapping         : null,
    command         : null,
    callback        : null,

    // --------------------------
    // Controls for form rezising
    // --------------------------

    resizable       : null,
    variable        : null,
    search          : null,

    // -----------------
    // DB response items
    // -----------------

    action          : null,
    title           : null,
    data            : null,
    props           : null,
    config          : null,
    columns         : null,
    hidden_columns  : null,

    disabled_form       : '', //' disabled',

    is_active       : false,
    is_refresh      : false,
    is_open         : false,
    is_panel_open   : false,
    is_scroll_top   : false,
    is_error        : false,

    init: function() {
        this.id = 'reference';

        this.container = $("#"+this.id+"-container");
        this.box = $("#"+this.id+"-box");
        this.table = $("#"+this.id+"-table");
        this.head = $("#"+this.id+"-head");
        this.content = $("#"+this.id+"-content");
        this.panel = $("#"+this.id+"-panel");
        this.form = $("#"+this.id+"-form");

        this.base.init(null, this.id, this);

        this.mapping = null;
        this.callback = null;

        this.resizable = null;
        this.variable = null;
        this.search = null;

        this.is_active = false;
        this.is_open = false;
        this.is_refresh = false;
        this.is_error = false;

        this.is_panel_open = false;

        this.initState();
    },

    initState: function() {
        this.state = {'ob': null, 'mode': '', 'selected_offset': 0, 'items': new Object(), 'value':null};
        this.last = null;

        this.with_lock = $_mobile() ? 1 : 0;
        this.disabled_form = $_mobile() ? ' disabled' : '';

        this.data = null;
        this.props = null;
        this.config = null;
        this.columns = null;
        
        this.hidden_columns = null;
    },

    term: function() {
        this.base.term();

        this.is_active = false;

        this.actual_size = new Object();
    },

    reset: function() {
        if (this.IsTrace)
            alert('reset');

        this.base.reset(this.with_cache);
    },

    lock_scroll: function() {
        if (!this.with_lock)
            return;

        this.base.lock_scroll();
    },

    unlock_scroll: function() {
        if (!this.with_lock)
            return;

        this.base.unlock_scroll();
    },

    _response: function(x) {
        if (this.IsTrace)
            alert('_response:'+reprObject(x));

        if (is_null(x))
            return;

        this.data = x['data'];
        this.props = x['props'];
        this.config = x['config'];
        this.columns = x['columns'];
        
        this.hidden_columns = this.config['hidden_columns'] || [];

        if (this.IsLog)
            console.log('$ReferenceDialog._response columns:', this.columns, 'hidden_columns:', this.hidden_columns);

        this.set_mode(this.props['mode']);
    },

    _refresh: function() {
        if (!this.is_active || this.is_refresh) {
            if (!this.is_active)
                this.setContainer();

            if (!this.is_open || this.is_refresh) {
                this.setContent();

                this.setBox();
            }

            if (!this.is_open)
                this.setPanel();
        }

        this.toggle();

        if (this.is_refresh && this.is_panel_open)
            this.setPanel(2);

        this.setDefaultSize(false);

        this.is_refresh = false;
    },

    get_id: function() {
        return this.container.attr('id');
    },

    get_mode: function() {
        return this.container.attr('mode');
    },

    set_mode: function(mode) {
        this.container.attr('mode', mode);
    },

    set_size: function(mode, width, height, force) {
        var size = this.actual_size[mode];

        if (force && is_null(size))
            return;

        if (this.IsLog)
            console.log('$ReferenceDialog.set_size mode:', mode, width, height, 'size:', size);

        var w = force ? size[0] : width;
        var h = force ? size[1] : height;

        //alert('set_size, mode:'+mode+':w-'+w+':h-'+h);

        switch(mode) {
            case 'resizable':
                if (!is_empty(w))
                    this.resizable.css("width", $_get_css_size(w));
                break;
            case 'variable':
                if (!is_empty(w))
                    for (i=0; i < this.variable.length; i++) {
                        this.variable[i].css("width", $_get_css_size(w));
                    }
                break;
            case 'search':
                if (!is_empty(w))
                    this.search.css("width", $_get_css_size(w));
                break;
            case 'panel':
                /*
                if (is_empty(h)) {
                    //w = this.actual_size[this.get_mode()][0] - 20;
                    h = this.actual_size[this.get_mode()][1] - (this.panel.height() + this.offset.height + this.offset.padding);
                } else {
                    //w += size[0];
                    h += size[1];
                }
                //this.table.css({"width" : $_get_css_size(w), "height" : $_get_css_size(h)});
                */
                h = this.actual_size[this.get_mode()][1] - (this.panel.height() + this.offset.height + this.offset.padding);
                this.table.css("height", $_get_css_size(h));
        }

        this.actual_size[mode] = [w, h];
    },

    get_size: function(mode, size) {
        return this.actual_size[mode][size.toLowerCase() == 'w' ? 0 : 1];
    },

    set_state: function(ob) {
        if (is_null(ob))
            return;

        var self = $ReferenceDialog;

        if (this.IsDeepDebug)
            alert('set_state, actions.command:'+this.actions.command);

        var oid = ob.attr('id');

        this.state['ob'] = ob;
        this.state['mode'] = this.get_mode();
        this.state['value'] = getsplitteditem(oid, ':', 1, '');
        /*
        try {
            this.state['selected_offset'] = ob.position().top;
        }
        catch(e) {
            this.state['selected_offset'] = 0;
        }

        if (this.IsLog)
            console.log('$ReferenceDialog.set_state oid:'+oid+', selected_offset:'+this.state['selected_offset']);
        */
        var items = new Object();
        var is_update = this.actions.command === 'update';

        ob.children().each(function(index) {
            var item = $(this);
            var id = item.attr('id').split(':')[0];
            var value = item.html();
            
            if (!is_null(id)) {
                var key = id.split('-')[1];
                items[key] = value;

                if (is_update) {
                    var x = $("#reference_value_"+key, self.panel);
                    if (is_exist(x))
                        x.val(value);
                }
            }
        });

        this.state['items'] = items;
    },

    scroll_bottom: function() {
        var content_height = this.content.height();
        var table_height = this.table.height();

        if (this.actions.command == 'add' && content_height > table_height)
            this.table.scrollTop(table_height);
    },

    scroll_top: function(debug) {
        if (!this.is_scroll_top)
            return;

        var content_height = this.content.height();
        var table_height = this.table.height();

        //alert(content_height+':'+table_height);

        /*
        var t = this.table.position().top;
        var s = this.table.scrollTop();
        var m = (table_height - this.state['ob'].height()) / 2;
        var x = this.state['selected_offset'];
        var offset = x - t - m;

        if (this.IsLog)
            console.log('$ReferenceDialog.scroll_top, t:', t, 'm:', m, 's:', s, 'x:', x, 'offset:', offset);
        */
        if (content_height <= table_height)
            return;

        var x = int(content_height / table_height);
        var offset = int(this.state['ob'].position().top - int((table_height - this.state['ob'].height()) / 2) / x);

        //alert(offset);

        this.table.scrollTop(offset);
    },

    collect_items: function() {
        var items = new Object();

        // ---------------------------------
        // Collect changed input data values
        // ---------------------------------

        for (var key in this.mapping) {
            var name = get_attr(this.mapping, key, 'name');
            var ob = $("#reference_value_"+key);

            if (!is_null(ob))
                items[name] = ob.val();
        }

        if (this.IsLog)
            console.log('$ReferenceDialog.collect_items items:', items);

        return items;
    },

    get_selected_item: function() {
        var ob = new Object();

        this.state['ob'].children().each(function(index) {
            var item = $(this);
            var id = item.attr('id').split(':')[0];
            var value = item.html();
            
            if (!is_null(id)) {
                var key = id.split('-')[1];
                ob[key] = value;
            }
        });

        // -------------------------------------------
        // Get `value` of the item if it's not visible
        // -------------------------------------------

        var value = this.props['value'];
        var id = this.props['id'];

        //alert(value+':'+id+', ob:'+reprObject(ob));

        if (!is_empty(value) && !('value' in ob) && !is_empty(ob.id) && !is_null(this.data)) {
            for (i=0; i<this.data.length; i++) {
                var row = this.data[i];

                if (row[id] == ob.id) {
                    //alert(reprObject(row));

                    ob['value'] = row[value];
                    break;
                }
            }
        }

        return ob;
    },

    toggle: function(ob) {
        var ob = ob || $("tr[class~='selected']", this.content);

        if (!is_exist(ob))
            ob = $("tr[class~='parent']", this.content).last();

        if (this.IsLog)
            console.log('$ReferenceDialog.toggle mode:'+this.get_mode(), 'ob:', ob.attr('id'), 'last:', this.last);

        if (is_exist(this.last))
            $onToggleSelectedClass(REFERENCE, this.last, 'remove', null);

        $onToggleSelectedClass(REFERENCE, ob, 'add', null);

        this.set_state(ob);

        this.last = ob;
    },

    setTitle: function() {
        $("#"+this.id+"-title").html(this.props['title']+(this.title ? ' ['+this.title+']' : ''));
    },

    setContainer: function() {
        this.setTitle();

        $("#"+this.id+"-confirmation").remove();

        var html = 
            '<div class="common-confirmation" id="'+this.id+'-confirmation">'+
              '<h4>'+keywords['select referenced item']+'</h4>'+
              '<div id="'+this.id+'-box">'+
                '<div class="common-box"><div id="'+this.id+'-table"></div></div>'+
                '<div class="common-box"><div id="'+this.id+'-panel"></div></div>'+
              '</div>'+
            '</div>';

        this.container.append(html);

        this.table = $("#"+this.id+"-table");
        this.panel = $("#"+this.id+"-panel");

        this.box = $("#"+this.id+"-box");

        this.is_refresh = false;
    },

    setBox: function() {
        this.head = $("#"+this.id+"-head");
        this.content = $("#"+this.id+"-content");
        this.resizable = $("#"+this.id+"-head-name");

        this.last = $("tr[class~='selected']", this.table).first();

        if (this.IsLog)
            console.log('$ReferenceDialog.setBox last:', this.last);

        if (!is_null(this.last))
            $onToggleSelectedClass(REFERENCE, this.last, 'add', null);
    },

    setContent: function() {
        var self = $ReferenceDialog;

        var mode = this.get_mode();
        var id = this.props['id'];

        var columns = this.config['columns'].union(this.hidden_columns);
        var headers = this.config['headers'];

        if (this.IsLog)
            console.log('$ReferenceDialog.setContent columns:', columns, 'headers:', headers, 'data:', this.data);

        var head = '';
        var item = '';

        if (!is_null(this.last))
            $onToggleSelectedClass(REFERENCE, this.last, 'remove', null);

        columns.forEach(function(name, index) {
            var header = headers[name];
            if (!is_null(header) && header.show) {
                var style = header.style ? ' '+header.style : '';
                head += '<th class="reference-headSTYLE" id="reference-head-KEY">TITLE</td>'
                    .replace(/TITLE/g, header.title)
                    .replace(/STYLE/g, style)
                    .replace(/KEY/g, header.key);
                item += '<td class="reference-KEYSTYLESELECTED" id="reference-KEY:#ID" title="TITLE">VALUE:NAME</td>'
                    .replace(/NAME/g, name)
                    .replace(/STYLE/g, style)
                    .replace(/TITLE/g, header.title)
                    .replace(/KEY/g, header.key);

                if (name == 'TID') {
                    head += '<td class="reference-head"></td>';
                    item += '<td class="level-icon" id="level-icon:#ID"><div id="level:#ID"></div></td>';
                }
            }
        });

        head = '<tr class="reference-item" id="reference-head">'+head+'</tr>';
        item = '<tr class="reference-itemSTYLESELECTED" id="reference:#ID">'+item+'</tr>';

        var content = '';

        this.data.forEach(function(row, index) {
            var selected = !is_empty(row['selected']) ? ' selected' : '';
            var style = !is_empty(row['style']) ? ' '+row['style'] : '';
            var line = item;
            for (i=0; i < columns.length; i++) {
                var name = columns[i];
                var header = headers[name];

                if (is_null(header) || !header.show)
                    continue;

                var value_regexp = new RegExp('VALUE:'+name, 'ig');
                line = line
                    .replace(value_regexp, row[name]);
            }
            content += line
                .replace(/SELECTED/g, selected)
                .replace(/STYLE/g, style)
                .replace(/#ID/g, row[id]);
        });

        if (this.is_refresh) {
            this.content.html(head+content);
            return;
        }

        content = '<table class="'+this.id+'-'+mode+'" id="'+this.id+'-content">'+head+content+'</table>';

        this.table.empty().html(content);
    },

    setPanel: function(mode) {
        var src = $SCRIPT_ROOT+'static/img/';

        var columns = this.columns.union(this.hidden_columns);
        var headers = this.config['headers'];
        var fields = this.config['fields'];
            
        this.variable = new Array();

        this.actions.mode = mode;

        if (this.IsDeepDebug)
            alert('setPanel, actions.command:'+this.actions.command+', mode:'+mode);

        if (is_null(this.mapping))
            this.mapping = make_reference_mapping(columns, headers);

        if (this.IsLog)
            console.log('$ReferenceDialog.setPanel mode:', mode, 'mapping:', this.mapping);

        var content = '';

        if (is_null(mode) || mode == 0) {
            content = (
                '<table border="0"><tr>'+
                '<td class="icon"><img class="reference-icon" id="#ID-icon:add" src="'+src+'add-40.png" title="'+keywords['Add']+'" alt=""></td>'+
                '<td class="icon"><img class="reference-icon" id="#ID-icon:update" src="'+src+'update-40.png" title="'+keywords['Update']+'" alt=""></td>'+
                '<td class="icon"><img class="reference-icon" id="#ID-icon:remove" src="'+src+'remove-40.png" title="'+keywords['Remove']+'" alt=""></td>'+
                '<td class="search"><form class="reference-form" id="#ID-form" action="javascript:void(0);"><input id="#ID-search" type="text" value="QUERY"'+
                    this.disabled_form+'></form></td>'+
                '<td class="icon"><img class="reference-icon" id="#ID-icon:search" src="'+src+'search-40.png" title="'+keywords['Search']+'" alt=""></td>'+
                '</tr></table>')
                    .replace(/QUERY/g, this.props['query'] || '')
                    .replace(/#ID/g, this.id);

            this.is_panel_open = false;
        }
        else if (mode == 1 || mode == 2) {
            for (i=0; i < columns.length; i++) {
                var name = columns[i];
                var header = headers[name];

                if (is_null(header) || !header.show)
                    continue;

                var field = fields[name];
                var key = header.key;
                var id = 'reference_value_'+key;
                var value = mode == 1 && this.columns.indexOf(name) > -1 ? '' : (key in this.state['items'] ? this.state['items'][key] : '');
                var invisible = this.hidden_columns.indexOf(name) > -1 ? ' class="invisible"' : '';

                content += (
                    '<tr'+invisible+'>'+
                    '<td class="reference-title">TITLE:</td>'+
                    '<td><input type="text" class="reference-TYPE" id="ID" value="VALUE"></td></tr>')
                        .replace(/TITLE/g, header.title)
                        .replace(/TYPE/g, field.type)
                        .replace(/VALUE/g, value)
                        .replace(/ID/g, id);

                if (['varchar','text'].indexOf(field.type) > -1)
                    this.variable.push(id);
            }

            content = 
                '<table class="reference-changeform '+this.get_mode()+'">'+
                  content+
                '<tr><td>&nbsp;</td><td>'+
                '<div>'+
                '<button class="reference-button" id="reference-button:save">'+keywords['Save']+'</button>'+
                '<button class="reference-button" id="reference-button:back">'+keywords['Back']+'</button>'+
                '</div></td></tr></table>';

            this.is_panel_open = true;
        }

        this.panel.html(content);

        if (!is_null(this.variable))
            for (i=0; i < this.variable.length; i++) {
                this.variable[i] = $("#"+this.variable[i]);
            }

        this.search = $("#"+this.id+"-search", this.panel);
        this.form = $("#"+this.id+"-form", this.panel);

        if (is_null(mode))
            return;

        this.onResize(0);
    },

    setDefaultSize: function(force) {
        var mode = this.get_mode();

        if (!(mode in this.actual_size) || force) {
            var s = mode in this.default_size ? this.default_size[mode] : this.default_size['default'];
            var c = $_screen_center();

            this.actual_size[mode] = [Math.min(c.W-0, s[0]), Math.min(c.H-0, s[1])];
        }

        if (this.IsLog)
            console.log('$ReferenceDialog.setDefaultSize mode:', mode, 'actual_size:', this.actual_size, 'force:', force);

        var size = this.actual_size[mode];

        this.set_size('resizable', size[0]);
        this.set_size('variable', size[0] - this.search_width);
        this.set_size('search', size[0] - this.search_width);

        this.set_size('panel');

        this.setTitle();

        // --------------------------------
        // Set default float content height
        // --------------------------------

        if (!force)
            return;

        this.make_item_visiable();
    },

    make_item_visiable: function() {
        var self = $ReferenceDialog;

        self.timer = setTimeout(function() { 
            self.scroll_top();
            window.clearTimeout(self.timer);
            self.timer = null; 
        }, self.timeout);

        this.is_scroll_top = false;
    },

    make_query: function() {
        if (is_null(this.config))
            return null;

        var columns = this.config['columns'].union(this.hidden_columns);
        var headers = this.config['headers'];

        var query = new Array(), name, value, key, item;

        if (is_null(this.last))
            return query;

        for (var i=0; i < columns.length; i++) {
            name = columns[i];
            value = '';
            if (name in headers) {
                key = headers[name]['key'];
                item = $("td[id^='"+this.id+"-"+key+"']", this.last);
                if (is_exist(item));
                    value = item.html();
            }
            query.push([name, value]);
        }

        if (this.IsLog)
            console.log('$ReferenceDialog.make_query, query:', query, 'columns:', columns, 'headers:', headers, 'last:', this.last);

        return query;
    },

    openNode: function(ob, command, action) {
        this.toggle(ob);

        if (this.IsLog)
            console.log('$ReferenceDialog.openNode id:'+ob.attr('id'));

        var query = this.make_query();

        this.is_refresh = true;

        this.confirmation(command, null, action, query, null, this.title);
    },

    openReferenceItem: function(command, callback, action, query, id) {
        this.initState();

        this.is_refresh = true;

        this.is_scroll_top = true;

        this.confirmation(command, callback, action, query, id, this.title);
    },

    confirmation: function(command, callback, action, query, id, title) {
        if (this.IsLog)
            console.log('$ReferenceDialog.confirmation, is_open:', this.is_open, 'is_refresh:', this.is_refresh, 'is_active:', this.is_active);

        if (this.is_open && !this.is_refresh)
            return;

        if (this.is_active && (is_null(this.base) || this.base.id !== this.id))
            this.is_active = false;

        if (!this.is_active)
            this.init();
        else if (this.is_refresh)
            this.initState();

        this.command = command;

        if (!is_null(callback))
            this.callback = callback;
            
        this.action = action || this.actions['default'];
        this.title = title || '';

        var x = command.split(DEFAULT_HTML_SPLITTER);
        var command = x.length > 1 ? x[0] : command;
        var mode = x.length > 1 ? x[1] : '';
        //var id = x.length > 2 ? x[2] : '';
        var state = this.state['value'] || '';
        var params = {'command':command, 'mode':mode, 'id':id, 'query':query, 'state':state};

        if (this.IsLog)
            console.log('$ReferenceDialog.confirmation, action:', this.action, 'params:', params);

        $web_logging(this.action, function(x) { $ReferenceDialog.open(x); }, params);
    },

    submit: function(command) {
        var mode = this.get_mode();
        var action = this.action || this.actions['default'];
        var query = (command == 'refresh' || is_null(command) ? this.props['query'] : this.search.val()) || '';
        var params = {'command':command, 'mode':mode, 'query':query};

        if (this.IsLog)
            console.log('$ReferenceDialog.submit, action:', this.action, 'params:', params, 'query:', query);

        confirm_action = '';

        this.is_refresh = true;

        $web_logging(action, function(x) { $ReferenceDialog.open(x); }, params);
    },

    check: function(x) {
        if (this.IsLog)
            console.log('$ReferenceDialog.check');

        this._response(x);

        var errors = this.props['errors'];

        if (!is_null(errors) && errors.length > 0) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
            this.is_error = true;
            return;
        }

        if (!is_null(this.last)) // && this.actions.command == 'add'
            $onToggleSelectedClass(REFERENCE, this.last, 'remove', null);

        this._refresh();

        this.scroll_bottom();

        confirm_action = 'reference:refresh';

        $NotificationDialog.open(keywords['Message:Action was done successfully']);
    },

    save: function(command) {
        var mode = this.get_mode();
        var action = this.action || this.actions['default'];
        var command = this.actions.command || command;
        var id = this.state['value'] || '';
        var query = this.make_query();
        var params = {'command':command, 'mode':mode, 'query':query, 'id':id};

        params['items'] = this.collect_items();

        if (this.IsLog)
            console.log('$ReferenceDialog.save, action:', this.action, 'params:', params);

        this.is_refresh = true;

        $web_logging(action, function(x) { $ReferenceDialog.check(x); }, params);
    },

    remove: function(command) {
        if (is_null(this.state['value']))
            return;

        var mode = this.get_mode();
        var action = this.action || this.actions['default'];
        var id = this.state['value'] || '';
        var query = this.make_query();
        var params = {'command':command, 'mode':mode, 'query':query, 'id':id};

        params['items'] = this.collect_items();

        if (this.IsLog)
            console.log('$ReferenceDialog.remove, action:', this.action, 'params:', params);

        this.is_refresh = true;

        $web_logging(action, function(x) { $ReferenceDialog.check(x); }, params);
    },

    resize: function() {
        /*
        if (this.is_active)
            delete this.actual_size[this.get_mode()];

        if ($_mobile())
            this.is_open = false;
        */
    },

    open: function(x) {
        this._response(x);

        this._refresh();
        
        if (this.is_open)
            return;

        if (!this.is_active) {
            var mode = this.get_mode();

            this.base.box = this.box;

            var cacheid = this.base.cacheid;
            var html = this.box.html().replace(this.id+'-form', cacheid); 

            if (this.IsDebug)
                alert('cacheid:'+cacheid+', html:'+html);

            this.base.load(html);

            var H = this.get_size(mode, 'h');
            var W = this.get_size(mode, 'w');
            //var init = [H - $_height(this.mode), W - $_width(this.mode)];
            //var x = this.offset_height + design_settings.dialog.offset.height;
            var offset = {'H' : [210, 0, H], 'W' : [65, 0, W], 'init' : [$_mobile() && $_window_landscape() && this.mode == 'available' ? -12 : 0, 0]}; //-44
            //var offset = {'H' : [210, 0, H], 'W' : [65, 0, W], 'init' : [0, 0]};

            this.base.setDefaultSize(offset);

            this.actual_size[mode] = [this.base.width(), this.base.height()];

            if (this.IsLog)
                console.log('$ReferenceDialog.open, actual_size:', this.actual_size[mode], 'base.activated:', this.base.activated);

            $BaseDialog.open(this.id, this.container);

            this.is_active = true;
        }
        else {
            $BaseDialog.activate();
        }

        this.scroll_top();
    },

    confirmed: function(command) {
        switch(command) {
            case 'remove':
                this.actions.command = command;
                this.remove(command);
                break;
            case 'save':
                if (typeof this.callback === 'function') {
                    var mode = this.get_mode();
                    var state = this.state['value'];
                    var item = this.get_selected_item();
                    var name = this.props['value'];
                    var key = this.config['headers'][name].key;
                    var value = item[key];
                    var params = {'command':command, 'mode':mode, 'state':state, 'value':value};

                    if (this.IsLog)
                        console.log('$ReferenceDialog.confirmed save, state:', state, 'item:', reprObject(item), 'name:', name, 'key:', key, 'value:', value);

                    // ---------------------------------
                    // Return to callable selected value
                    // ---------------------------------

                    this.callback(params);
                }
                
                this.close();
        }
    },

    is_focused: function() {
        return this.is_open;
    },

    onButtonClick: function(ob) {
        var command = ob.attr('id').split(':')[1];

        if (!(is_reference_edit_allowed || command == 'back'))
            return;

        switch(command) {
            case 'save':
                this.save(command);
                break;
            case 'back':
                this.setPanel(0);
                this.search.prop("disabled", false);
                break;
            default:
                $ShowError('Command is not responsable:'+this.get_mode()+':'+command, true, true, false);
        }
    },

    onIconClick: function(ob) {
        var command = ob.attr('id').split(':')[1];

        if (!(is_reference_edit_allowed || command == 'search'))
            return;

        switch(command) {
            case 'search':
                this.submit(command);
                break;
            case 'add':
                this.actions.command = 'add';
                this.setPanel(1);
                break;
            case 'update':
                if (!is_null(this.last)) {
                    this.actions.command = 'update';
                    this.setPanel(2);
                    this.set_state(this.last);
                }
                break;
            case 'remove':
                //alert(is_null(this.last)+':'+is_null(this.state['value']));

                if (!(is_null(this.last) || is_null(this.state['value']))) {
                    confirm_action = 'reference:remove';
                    $ConfirmDialog.open(keywords['Command:Reference item removing'], 500);
                }
                break;
            default:
                $ShowError('Command is not responsable:'+this.get_mode()+':'+command, true, true, false);
        }
    },

    onDoubleClick: function(ob, command, action) {
        //pass
    },

    onEnter: function() {
        if (this.is_open)
            this.submit('search');
    },

    onResize: function(force) {
        var mode = this.get_mode();

        if (!(mode in this.actual_size))
            return;

        // ------------------
        // New container size
        // ------------------
        
        var width = this.container.width();
        var height = this.container.height();

        if (this.IsLog)
            console.log('$ReferenceDialog.onResize, mode:', mode, 'width:', width, 'height:', height, 'force:', force);

        if (width < this.min_width || height < this.min_height) {
            this.setDefaultSize(true);
            return;
        }

        var size = this.actual_size[mode];

        // -------------
        // Resize offset
        // -------------

        var w = width - size[0];
        var h = height - size[1];
        /*
        function _set(ob, w, h) {
            ob.css({"width" : $_get_css_size(ob.width() + w), "height" : $_get_css_size(ob.height() + h)});
        }

        _set(this.box, w, h);
        */
        // ----------------------------
        // Adjust float dialog controls
        // ----------------------------

        this.set_size('resizable', this.get_size('resizable', 'w') + w);
        this.set_size('variable', this.get_size('variable', 'w') + w);
        this.set_size('search', this.get_size('search', 'w') + w);

        // -------------
        // Save new size
        // -------------

        if (force)
            this.actual_size[mode] = [width, height + 90];

        this.set_size('panel');
    },

    onOpen: function() {
        var self = $ReferenceDialog;

        $BaseScreenDialog.onOpen();

        if (!this.is_active) {
            this.onResize(0);

            this.table.scrollTop(0);

            this.timer = setTimeout(function() { 
                self.search.prop("disabled", false);
                window.clearTimeout(self.timer);
                self.timer = null; 
            }, this.timeout);
        }
        else {
            this.box.css("height", "auto");

            this.onResize(1);
        }

        this.is_open = true;
    },

    onClose: function() {
        $BaseDialog.onClose();

        this.title = '';

        this.is_open = false;

        if (!$_mobile())
            return;

        this.term();
    },

    close: function() {
        $BaseDialog.deactivate();
    },

    cancel: function() {
        this.close();
    }
};

// =======
// Dialogs
// =======

jQuery(function($) 
{
    // ----------------
    // Reference Dialog
    // ----------------

    $("#reference-container").dialog({
        autoOpen: false,
        buttons: [
            {text: keywords['Select'],  click: function() { $ReferenceDialog.confirmed('save'); }},
            {text: keywords['Cancel'],  click: function() { $ReferenceDialog.cancel(); }}
        ],
        modal: true,
        draggable: true,
        resizable: true,
        //position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        open: function() {
            $ReferenceDialog.onOpen();
        },
        close: function() {
            $ReferenceDialog.onClose();
        },
        resize: function() {
            $ReferenceDialog.onResize(true);
        }
    });
});
