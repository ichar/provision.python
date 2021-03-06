// ****************************************
// REFERENCE DIALOGS: /reference.dialogs.js
// ----------------------------------------
// Version: 1.0
// Date: 14-07-2019

// ===========================
// Dialog windows declarations
// ===========================

var separator = '-';

var TEMPLATE_CONFIG_ID = 'config_value' + separator;
var TEMPLATE_SERVICE = 'service:';
var TEMPLATE_NEW_CONFIG_ITEM = 'new-config-item';

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
    default_size  : 
    {
        'clients'           : [500, 600],
        'batch-create-type' : [520, 420],
        'batch-result-type' : [520, 420],
        'batch-status'      : [520, 480],
        'batch-type'        : [550, 600],
        'file-status'       : [760, 614],
        'file-type'         : [620, 600], //662
        'ftb-post'          : [980, 614],
        'ftv-oper-params'   : [720, 614],
        'oper-list'         : [550, 614],
        'oper-type'         : [550, 480],
        'tag-params'        : [930, 631],

        'linked-batches'    : [620, 480],
        'linked-opers'      : [620, 480],
        'linked-tags'       : [620, 612],
        'linked-tagopers'   : [620, 612],
        'linked-tagvalues'  : [520, 612],
        
        'default'           : [500, 400]
    },

    // ===================================
    // Configurator Reference Dialog Class
    // ===================================

    IsTrace : 0, IsLog : 0,

    actions         : {'default' : 620, 'command' : null, 'mode' : null},
    timeout         : 300,
    timer           : null,

    // ---------
    // Constants
    // ---------

    min_width       : 400,
    min_height      : 260,

    search_width    : 300,
    offset_height   : 218,

    // ---------------
    // Form's controls 
    // ---------------

    container       : null,
    box             : null,
    head            : null,
    content         : null,
    panel           : null,

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

    data            : null,
    props           : null,
    config          : null,
    columns         : null,

    is_active       : false,
    is_open         : false,
    is_error        : false,

    init: function() {
        this.container = $("#reference-container");
        this.box = $("#reference-box");
        this.head = $("#reference-head");
        this.content = $("#reference-items");
        this.panel = $("#reference-panel");

        this.state = new Object();
        this.last = null;
        this.mapping = null;
        this.callback = null;

        this.resizable = null;
        this.variable = null;
        this.search = null;

        this.data = null;
        this.props = null;
        this.config = null;
        this.columns = null;

        this.is_open = false;
        this.is_error = false;
    },

    _response: function(x) {
        if (is_null(x))
            return;

        this.data = x['data'];
        this.props = x['props'];
        this.config = x['config'];
        this.columns = x['columns'];

        this.set_mode(this.props['mode']);
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

        //if (this.IsTrace)
        //    alert(mode+':'+width+':'+height+', size:'+size);

        var w = force ? size[0] : width;
        var h = force ? size[1] : height;

        switch(mode) {
            case 'resizable':
                if (!is_empty(w))
                    this.resizable.css("width", w.toString()+"px");
                break;
            case 'variable':
                if (!is_empty(w))
                    for (i=0; i<this.variable.length; i++) {
                        this.variable[i].css("width", w.toString()+"px");
                    }
                break;
            case 'search':
                if (!is_empty(w))
                    this.search.css("width", w.toString()+"px");
                break;
            case 'panel':
                var panel_height = xround(this.panel.height());
                h = this.actual_size[this.get_mode()][1] - (panel_height + this.offset_height);
                this.box.css("height", h.toString()+"px");
                mode = 'box';
                break;
        }

        this.actual_size[mode] = [w, h];
    },

    get_size: function(mode, size) {
        return this.actual_size[mode][size == 'w' ? 0 : 1];
    },

    set_state: function(ob) {
        if (is_null(ob))
            return;

        var oid = ob.attr('id');

        this.state['ob'] = ob;
        this.state['mode'] = this.get_mode();
        this.state['value'] = getsplitteditem(oid, ':', 1, '');

        try {
            this.state['selected_offset'] = xround(ob.position().top);
        }
        catch(e) {
            this.state['selected_offset'] = 0;
        }

        if (this.IsLog)
            console.log('$ReferenceDialog.set_state, oid:'+oid+', selected_offset:'+this.state['selected_offset']);

        var items = new Object();

        ob.children().each(function(index) {
            var item = $(this);
            var id = item.attr('id').split(':')[0];
            var value = item.html();
            
            if (!is_null(id)) {
                var key = id.split('-')[1];
                items[key] = value;

                var ob = $("#reference_value_"+key);
                if (!is_null(ob))
                    ob.val(value);
            }
        });

        this.state['items'] = items;

        //this.scroll_top(1);
    },

    scroll_top: function(debug) {
        var content_height = xround(this.content.height());
        var box_height = xround(this.box.height());

        var t = xround(this.box.position().top);
        var s = this.box.scrollTop();
        var m = xround((box_height - this.state['ob'].height()) / 2);
        var x = this.state['selected_offset'];
        var offset = x - t - m;

        if (this.IsLog)
            console.log('box_top:'+t, 'box_middle:'+m, 'box_scroll:'+s, 'ob:'+x, 'offset:'+offset);

        if (content_height <= box_height || is_empty(x) || debug)
            return;

        this.box.scrollTop(offset);
    },

    collect_items: function() {
        var items = new Object();

        // ---------------------------------
        // Collect changed input data values
        // ---------------------------------

        for(var key in this.mapping) {
            var name = get_attr(this.mapping, key, 'name');
            var ob = $("#reference_value_"+key);

            if (!is_null(ob))
                items[name] = ob.val();
        }

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
        if (is_null(ob))
            return;

        if (this.IsLog)
            console.log('$ReferenceDialog.toggle', 'mode:'+this.get_mode(), 'selected:'+ob.attr('id'));

        if (this.last != null)
            $onToggleSelectedClass(REFERENCE, this.last, 'remove', null);
        
        $onToggleSelectedClass(REFERENCE, ob, 'add', null);

        this.set_state(ob);

        this.last = ob;
    },

    setContent: function() {
        $("#reference-title").html(this.props['title']);
        $("#reference-confirmation").remove();

        var html = 
            '<div class="common-confirmation" id="reference-confirmation">'+
            '<h4>'+keywords['select referenced item']+'</h4>'+
            '<div class="common-box"><div id="reference-box">'+
            '</div></div>'+
            '<div class="common-box"><div id="reference-panel">'+
            '</div></div>'+
            '</div>';

        this.container.append(html);

        this.box = $("#reference-box");
        this.panel = $("#reference-panel");
    },

    setBox: function() {
        var mode = this.get_mode();
        var id = this.props['id'];
        
        var columns = this.config['columns'];
        var headers = this.config['headers'];

        var head = '';
        var item = '';

        columns.forEach(function(name, index) {
            var header = headers[name];
            if (!is_null(header) && header.show) {
                head += '<th class="reference-head" id="reference-head-KEY">TITLE</td>'
                    .replace(/TITLE/g, header.title)
                    .replace(/KEY/g, header.key);
                item += '<td class="reference-KEYSELECTED" id="reference-KEY:#ID" title="TITLE">VALUE:NAME</td>'
                    .replace(/NAME/g, name)
                    .replace(/STYLE/g, header.style)
                    .replace(/TITLE/g, header.title)
                    .replace(/KEY/g, header.key);
            }
        });

        head = '<tr class="reference-item" id="reference-head">'+head+'</tr>';
        item = '<tr class="reference-itemSELECTED" id="reference:#ID">'+item+'</tr>';

        var content = '';

        this.data.forEach(function(row, index) {
            var selected = !is_empty(row['selected']) ? ' selected' : '';
            var line = item;
            for (i=0; i<columns.length; i++) {
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
                .replace(/#ID/g, row[id]);
        });

        content = '<table class="reference-'+mode+'" id="reference-items">'+head+content+'</table>';

        this.box.html(content);

        this.head = $("#reference-head");
        this.content = $("#reference-items");
        this.resizable = $("#reference-head-name");
    },

    setPanel: function(mode) {
        var src = $SCRIPT_ROOT+'static/img/';
        var content = '';

        var columns = this.columns;
        var headers = this.config['headers'];
        var fields = this.config['fields'];
            
        this.variable = new Array();

        this.actions.mode = mode;

        if (is_null(this.mapping))
            this.mapping = make_reference_mapping(columns, headers);

        if (is_null(mode) || mode == 0) {
            content = (
                '<table border="0"><tr>'+
                '<td class="icon"><img class="reference-icon" id="reference-icon:add" src="'+src+'add-40.png" title="'+keywords['Add']+'" alt=""></td>'+
                '<td class="icon"><img class="reference-icon" id="reference-icon:update" src="'+src+'update-40.png" title="'+keywords['Update']+'" alt=""></td>'+
                '<td class="icon"><img class="reference-icon" id="reference-icon:remove" src="'+src+'remove-40.png" title="'+keywords['Remove']+'" alt=""></td>'+
                '<td class="search"><input id="reference-search" type="text" value="QUERY"></td>'+
                '<td class="icon"><img class="reference-icon" id="reference-icon:search" src="'+src+'search-40.png" title="'+keywords['Search']+'" alt=""></td>'+
                '</tr></table>')
                    .replace(/QUERY/g, this.props['query'] || '');
        }
        else if (mode == 1 || mode == 2) {
            for (i=0; i<columns.length; i++) {
                var name = columns[i];
                var header = headers[name];

                if (is_null(header) || !header.show)
                    continue;

                var field = fields[name];
                var key = header.key;
                var id = 'reference_value_'+key;

                var value = mode == 1 ? '' : (key in this.state['items'] ? this.state['items'][key] : '...');

                content += (
                    '<tr>'+
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
        }

        this.panel.html(content);

        if (!is_null(this.variable))
            for (i=0; i<this.variable.length; i++) {
                var ob = $("#"+this.variable[i]);
                this.variable[i] = ob;
            }

        this.search = $("#reference-search");

        if (is_null(mode))
            return;

        this.onResize(false);
    },

    setDefaultSize: function(force) {
        var mode = this.get_mode();

        if (!(mode in this.actual_size) || force) {
            var s = mode in this.default_size ? this.default_size[mode] : this.default_size['default'];
            var f = !$IS_FRAME ? true : false;
            var c = $_screen_center();

            if (f)
                s = [Math.min(c.W, s[0]), Math.min(c.H-120, s[1])];
            else
                s[1] += 4;

            this.actual_size[mode] = s;
        }

        var size = this.actual_size[mode];

        this.set_size('resizable', size[0], null);
        this.set_size('variable', size[0] - this.search_width, null);
        this.set_size('search', size[0] - this.search_width, null);

        if (this.IsLog)
            console.log('setDefaultSize:'+mode+':'+this.container.width()+':'+this.container.height()+':'+size+':'+force);

        if (!this.is_open || force) {
            this.container.dialog("option", "width", size[0]);
            this.container.dialog("option", "height", size[1]);
        }

        // --------------------------------
        // Set default float content height
        // --------------------------------

        if (!force)
            return;
        
        this.set_size('panel');
    },

    onResize: function(force) {
        var mode = this.get_mode();

        if (!(mode in this.actual_size))
            return false;

        //if (this.IsTrace)
        //    alert('resize:'+mode+':'+this.container.width()+':'+this.container.height()+':'+force);

        // ------------------
        // New container size
        // ------------------
        
        var width = xround(this.container.width());
        var height = xround(this.container.height());

        if ((width < this.min_width) || (height < this.min_height)) {
            this.setDefaultSize(true);
            return false;
        }

        var size = this.actual_size[mode];

        // -------------
        // Resize offset
        // -------------

        var w = width - size[0];
        var h = height - size[1];

        // ----------------------------
        // Adjust float dialog controls
        // ----------------------------

        this.set_size('resizable', this.get_size('resizable', 'w') + w, null);
        this.set_size('variable', this.get_size('variable', 'w') + w, null);
        this.set_size('search', this.get_size('search', 'w') + w, null);
        this.set_size('panel');

        // -------------
        // Save new size
        // -------------

        if (force)
            this.actual_size[mode] = [
                width, 
                height + 90 // + offset + 5 // ???
            ];

        return true;
    },

    onOpen: function() {
        this.onResize(false);
        this.box.scrollTop(0);

        this.is_open = true;
    },

    onClose: function() {
        this.timer = setTimeout(function() { 
            $ReferenceDialog.is_open = false; 
            window.clearTimeout($ReferenceDialog.timer);
            $ReferenceDialog.timer = null; 
        }, this.timeout);
    },

    onButtonClick: function(ob) {
        var command = ob.attr('id').split(':')[1];

        if (!(IsAdmin || command == 'back'))
            return;

        switch(command) {
            case 'save':
                this.save(command);
                break;
            case 'back':
                this.setPanel(0);
                break;
            default:
                $ShowError('Command is not responsable:'+this.get_mode()+':'+command, true, true, false);
        }
    },

    onEnter: function() {
        if (this.is_open)
            this.submit('search');
    },

    onIconClick: function(ob) {
        var command = ob.attr('id').split(':')[1];

        if (!(IsAdmin || command == 'search'))
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
                if (!(is_null(this.last) || is_null(this.state['value']))) {
                    confirm_action = 'reference:remove';
                    $ConfirmDialog.open(keywords['Command:Reference item removing'], 500);
                }
                break;
            default:
                $ShowError('Command is not responsable:'+this.get_mode()+':'+command, true, true, false);
        }
    },

    confirmation: function(command, callback) {
        if (this.is_open)
            return;

        this.init();

        this.command = command;
        this.callback = callback;

        var action = this.actions['default'];
        var x = command.split(DEFAULT_HTML_SPLITTER);
        var command = x.length > 1 ? x[0] : command;
        var mode = x.length > 1 ? x[1] : '';
        var id = x.length > 2 ? x[2] : '';
        var params = {'command':command, 'mode':mode, 'id':id};

        //if (this.IsTrace)
        //    alert('confirmation:'+action+':'+command+':'+mode);

        $web_logging(action, function(x) { $ReferenceDialog.open(x); }, params);
    },

    submit: function(command) {
        var mode = this.get_mode();
        var action = this.actions['default'];
        var query = (command == 'refresh' || is_null(command) ? this.props['query'] : this.search.val()) || '';
        var params = {'command':command, 'mode':mode, 'query':query};

        //if (this.IsTrace)
        //    alert('submit:'+action+':'+command+':'+mode+':'+query);

        confirm_action = '';

        $web_logging(action, function(x) { $ReferenceDialog.open(x); }, params);
    },

    check: function(x) {
        this._response(x);

        var errors = this.props['errors'];

        if (!is_null(errors) && errors.length > 0) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
            this.is_error = true;
            return;
        }

        confirm_action = 'reference:refresh';

        $NotificationDialog.open(keywords['Message:Action was done successfully']);
    },

    save: function(command) {
        var mode = this.get_mode();
        var action = this.actions['default'];
        var x = this.actions.command ? this.actions.command : command;
        var query = this.props['query'] || '';
        var params = {'command':x, 'mode':mode, 'query':query};

        params['items'] = this.collect_items();
        params['id'] = this.state['value'] || '';

        //if (this.IsTrace)
        //    alert('save:'+action+':'+x+':'+mode+':'+query);

        if (this.IsLog)
            console.log('$ReferenceDialog.params:'+reprObject(params));

        $web_logging(action, function(x) { $ReferenceDialog.check(x); }, params);
    },

    remove: function(command) {
        if (is_null(this.state['value']))
            return;

        var mode = this.get_mode();
        var action = this.actions['default'];
        var query = this.props['query'] || '';
        var id = this.state['value'] || '';
        var params = {'command':command, 'mode':mode, 'query':query, 'id':id};

        //if (this.IsTrace)
        //    alert('remove:'+action+':'+command+':'+mode+':'+query);

        $web_logging(action, function(x) { $ReferenceDialog.check(x); }, params);
    },

    open: function(x) {
        this._response(x);

        if (!this.is_open)
            this.setContent(0);

        this.setBox();

        if (!this.is_open) {
            this.setPanel();
            //this.container.dialog("option", "title", keywords['Status confirmation form']);
            //$("#ui-id-6").html(keywords['Status confirmation form']);
        }

        this.setDefaultSize(false);
        
        if (this.is_open)
            return;

        if (!this.is_active) {
            var is_service = this.command.startswith(TEMPLATE_SERVICE);
            var f = !is_service ? true : false;
            if (f)
                this.container.dialog("option", "position", {my:"right-40px top+20px", at:"right top", of:window, collision:"none"});
            else
                //this.container.dialog("option", "position", "center");
                this.container.dialog("option", "position", {my:"center center", at:"center center", of:window, collision:"none"});

            if (!is_service)
                this.is_active = true;
        }

        this.container.dialog("open");

        var ob = $("tr[class~='selected']", this.content);

        this.toggle(ob);

        this.scroll_top();
    },

    confirmed: function(command) {
        switch(command) {
            case 'remove':
                this.actions.command = command;
                this.remove(command);
                break;
            case 'ok':
                if (typeof this.callback === 'function') {
                    var id = this.state['value'];
                    var item = this.get_selected_item();
                    var name = this.props['value'];
                    var key = this.config['headers'][name].key;
                    var value = item[key];
                    var x = {'id' : id, 'value' : value};

                    //alert(id+', item:'+reprObject(item)+', name:'+name+', key:'+key+', value:'+value+', x:'+reprObject(x));

                    // ---------------------------------
                    // Return to callable selected value
                    // ---------------------------------

                    this.callback(x);
                }
                
                this.close();
        }
    },

    is_focused: function() {
        return this.is_open;
    },

    close: function() {
        this.container.dialog("close");
    }
};

var $ConfigSelector = {
    actions       : {'default' : 621, 'command' : null},
    timeout       : 300,

    // ================================
    // Configurator View Selector Class
    // ================================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    // -----------------------------------
    // Config Object ID (current Tab name)
    // -----------------------------------

    mode          : '',

    // ---------------
    // Form's controls 
    // ---------------

    container     : null,
    current       : null,
    oid           : '',
    rid           : 0,
    number        : 0,

    backup        : new Object(),
    mapping       : null,
    links         : new Object(),
    selected_link : null,
    callback      : null,

    // -----------------
    // DB response items
    // -----------------

    data          : null,
    props         : null,
    config        : null,
    columns       : null,

    active_links  : new Object(),

    is_open       : false,
    is_blank      : false,
    is_changed    : false,
    is_error      : false,

    init: function(ob) {
        this.rollback();

        this.set_mode(ob);

        if (this.IsLog)
            console.log('$ConfigSelector.init, mode:'+this.get_mode());

        this.backup = new Object();
        this.mapping = null;
        this.links = new Object();
        this.selected_link = null;
        this.callback = null;

        this.is_open = false;

        this.reset();
    },

    rollback: function() {
        // ---------------------------------------------------------------
        // Rollbacks state of previously current item, for `blank` special
        // ---------------------------------------------------------------

        if (!(is_null(this.current) || is_null(this.backup.html)))
            this.setContent(1);
    },

    reset: function() {
        // ------------------------------------
        // Reset current item and his container
        // ------------------------------------

        this.container = null;

        this.current = null;
        this.oid = '';
        this.rid = 0;
        this.number = 0;

        this.is_changed = false;
        this.is_blank = false;
        this.is_error = false;

        if (this.IsLog)
            console.log('$ConfigSelector.reset');
    },

    _response: function(x) {
        // ------------------------------
        // Receives data for current item
        // ------------------------------

        if (is_null(x))
            return;

        if (this.IsLog)
            console.log('$ConfigSelector._response');

        this.data = x['data'];
        this.props = x['props'];
        this.config = x['config'];
        this.columns = x['columns'];

        this.mapping = null;
    },

    is_occupied: function() {
        var f = this.is_blank ? true : false;
        if (f)
            $InProgress(null);
        return f;
    },

    is_focused: function() {
        return this.is_open;
    },

    get_id: function() {
        return $_get_item_id(this.current);
    },

    get_mode: function() {
        return this.mode;
    },

    set_mode: function(ob) {
        this.mode = ob && ob.attr('id').split('-').slice(-1)[0];
    },

    set_callback: function(callback) {
        this.callback = callback;

        if (this.IsLog)
            console.log('$ConfigSelector.set_callback:'+typeof this.callback);
    },

    set_current: function(ob) {
        if (is_null(ob))
            return;

        this.current = ob;
        this.oid = ob.attr('id');
        this.rid = parseInt($_get_item_id(ob, 1)) || 0;
        this.number = parseInt($_get_item_id(ob, 2)) || 0;

        this.active_links = new Object();

        if (this.rid > 0)
            this.container = this.current.parent();

        if (this.IsLog)
            console.log('$ConfigSelector.set_current, oid:'+this.oid+', rid:'+this.rid);
    },

    set_line: function(content, is_blank) {
        return (
            '<td colspan="'+this.props['columns'].length.toString()+'">'+
            '<div id="config-container" class="config-'+(is_blank ? 'blank' : 'default')+'">'+
            '<table class="config-changeform '+this.get_mode()+'" id="config-changeform">'+
              content+
            '<tr><td>&nbsp;</td><td>'+
            '<div class="config-panel" id="config-panel">'+
            '<button class="config-button" id="config-button:save">'+keywords['Save']+'</button>'+
            '<button class="config-button" id="config-button:back">'+keywords['Cancel']+'</button>'+
            '</div></td></tr></table>'+
            '</div>'+
            '</td>'
        );
    },

    set_link: function(links, header, id, name, pk, value) {
        // -------------------------------------------------------
        // Set a `link` item and registers it inside `this.links`.
        // -------------------------------------------------------
        //      links     : this.links object reference
        //      header    : header of the field
        //      id        : id of LinkIcon control
        //      name      : name of the field
        //      pk        : flag is it PK or not
        //      value     : value of the field (link reference value)
        //
        // Links items register:
        //      name      : name of the field
        //      reference : String, FK reference view name
        //      alias     : String, view field name
        //      link      : Int, FK type [{1|2}]: 1-editable, 2-frozen
        //      value     : value of the field (link reference value)

        var src = $SCRIPT_ROOT+'static/img/';

        if (is_empty(header.link) || pk)
            return '';

        links[id] = {'name' : name, 'reference' : header.reference, 'alias' : header.alias, 'link' : header.link, 'value' : value};

        return (
            '<td class="icon">'+
              '<img class="config-icon" id="config-icon:link:'+id+'" src="'+src+
              (header.link==2 ? 'link-40.png' : 'more-40.png')+'" title="'+
              (header.link==2 ?  keywords['Frozen link'] : keywords['Link'])+'" alt="'+
              keywords['Link']+'">'+
            '</td>'
        );
    },

    set_blank: function(class_name, is_nodata, line) {
        var i = -1;
        var x = makeTabLineAttrs(null, class_name, i);
        var selected = x[0], id = x[1];
        var row = makeTabLineRow(id, class_name, i, selected, line);

        if (is_nodata)
            this.container.empty();

        this.container.append(row);

        var ob = $("#"+id);

        this.set_current(ob);
    },

    set_nodata: function(class_name, is_nodata) {
        var row = makeTabNoData(class_name, 'nodata', keywords['No data'], this.props['columns'].length);

        if (is_nodata)
            this.container.empty();

        this.container.append(row);

        var ob = $("#"+class_name+'-no-data');

        this.set_current(ob);
    },

    set_total: function() {
        $("#tab-rows-total").html(this.props['total']);
    },

    collect_items: function() {
        var headers = this.config['headers'];
        var mapping = this.mapping;
        var selector = '*[id^="'+TEMPLATE_CONFIG_ID+'"]';

        var items = this.data[0];

        // ---------------------------------
        // Collect changed input data values
        // ---------------------------------

        this.current.find(selector).each(function(index) {
            var item = $(this);
            var id = item.attr('id');

            if (!is_empty(id) && id.startswith(TEMPLATE_CONFIG_ID)) {
                var key = id.split(separator)[1];
                var name = get_attr(mapping, key, 'name');

                if (is_empty(name) && this.IsLog)
                    console.log('$ConfigSelector.Empty mapping! key:'+key+', name:['+name+'], mapping:'+reprObject(mapping));

                var header = headers[name];

                if (!is_null(header)) {

                    //alert(name+':'+item.val());

                    if (is_empty(header.link))
                        items[name] = item.val();
                    else if (name == header.alias && items[name] == item.val())
                        delete items[name];
                }
            }
        });

        return items;
    },

    get_active_links: function() {
        return this.active_links;
    },

    move: function(ob, force) {
        if (this.IsLog)
            console.log('move:'+this.is_open+':'+this.is_blank);

        if (this.is_occupied() && !force)
            return false;

        if (this.IsLog)
            console.log('$ConfigSelector.move, is_open:'+this.is_open);

        // -------------------------------------
        // Move to another line in the container
        // -------------------------------------

        if (this.is_changed && !force) {
            this.backup.confirmed = ob;
            confirm_action = 'config:changed';

            $ConfirmDialog.open(keywords['Command:Item was changed. Continue?'], 500);
            return false;
        }

        // ---------------------------------------------------
        // Close (restore HTML-content of) line open to update
        // ---------------------------------------------------

        if (!is_null(this.data))
            this.setContent(1);

        // ------------------
        // Go on via callback
        // ------------------

        if (!is_null(ob) || force)
            this.runCallback(ob);
    
        return true;
    },

    runCallback: function(ob) {
        if (typeof this.callback === 'function') {
            if (this.IsLog)
                console.log('$ConfigSelector.runCallback');

            this.callback(ob);
        }
    },

    toggle: function(ob) {
        if (this.is_occupied())
            return;

        if (this.IsLog)
            console.log('$ConfigSelector.toggle, is_open:'+this.is_open);

        this.set_current(ob);

        // --------------------------------------
        // Set current line and open it to update
        // --------------------------------------

        if (this.is_open)
            this.confirmation(this.actions.command);
    },

    setContent: function(mode) {
        var columns = this.columns;
        var headers = this.config['headers'];
        var fields = this.config['fields'];
        var class_name = this.props['class_name'] || this.get_mode();
        var is_nodata = false;

        var content = '';

        // ---------------------
        // Get current line data
        // ---------------------

        var data = this.data[0];

        if (is_null(this.mapping))
            this.mapping = make_reference_mapping(columns, headers);

        if (this.IsLog)
            console.log('$ConfigSelector.setContent:'+mode+', is_blank:'+this.is_blank);

        // ------------------------------------------
        // Check whether container is empty (no data)
        // ------------------------------------------

        if (is_null(this.container)) {
            var id = class_name+"-no-data";
            //var ob = $("#"+id);
            var ob = $("tr[id='"+id+"']", $("#"+this.get_mode()+"-container")).first();

            //alert(class_name+':'+id+':'+ob.attr('id'));

            if (!is_null(ob)) {
                this.container = ob.parent();
                this.current = null;
                is_nodata = true;
            }
        }

        // ===========
        // DESIGN MODE
        // ===========

        if (is_null(mode) || mode == 0) {

            // -------------------
            // Backup current line
            // -------------------

            this.backup.current = this.current;
            this.backup.html = !is_null(this.current) ? this.current.html() : this.container.html();

            // -----------------------------------
            // Check and make blank line to insert
            // -----------------------------------

            if (this.is_blank)
                this.set_blank(class_name, is_nodata, '');

            // ---------------------------------------------------------
            // Make content of current line to update (open design mode)
            // ---------------------------------------------------------

            var links = new Object();

            for (i=0; i<columns.length; i++) {
                var name = columns[i];
                var header = headers[name];

                if (is_null(header) || !header.show)
                    continue;

                var alias = header.alias || name;
                var field = fields[alias];
                var id = TEMPLATE_CONFIG_ID+header.key;
                var pk = name == 'TID' ? true : false;

                content += (
                    '<tr>'+
                        '<td class="config-title">TITLE:</td>'
                        )
                        .replace(/TITLE/g, header.title);

                var tag = (
                    header.tag == 'textarea' ? 
                            '<textarea class="config-DBTYPEPK" id="ID" rows="3">VALUE</textarea>' :
                            '<input type="ITYPE" class="config-DBTYPEPK" id="ID" value="VALUE"DISABLED>'
                        )
                        .replace(/DISABLED/g, (header.link || pk) ? ' disabled=1' : '')
                        .replace(/DBTYPE/g, header.style || field.type)
                        .replace(/ITYPE/g, get_input_type(field.type, header.link))
                        .replace(/ID/g, id)
                        .replace(/PK/g, pk ? ' config-pk' : '')
                        .replace(/VALUE/g, data[alias]);

                content += (
                        '<td class="config-value"COLSPAN>'+tag+'</td>'+
                          this.set_link(links, header, id, name, pk, data[name])+
                    '</tr>'
                        )
                        .replace(/COLSPAN/g, header.link ? '' : ' colspan="2"');
            }

            this.links = links;
            this.selected_link = null;

            this.current.removeClass(class_name);

            content = this.set_line(content, this.is_blank);

            //this.active_links = new Object();

            this.backup.is_nodata = is_nodata;
            this.backup.oid = this.oid;
        }
        else if (mode == 1) {

            // ---------------------------------------------------------------------------------------------
            // Restore current line on exit (close design mode, press button Cancel or move to another line)
            // ---------------------------------------------------------------------------------------------

            if (is_empty(this.backup.html))
                return;

            is_nodata = is_nodata || this.backup.is_nodata || false;

            if (this.backup.command == 'blank') {
                this.current.remove();

                if (!is_nodata) {
                    this.current.remove();
                    this.set_current(this.backup.current);
                }
                else {
                    //this.container.empty();
                    this.current = this.container;
                    content = this.backup.html;
                    this.container = null;
                }
            }
            else {
                content = this.backup.html;
                this.current.addClass(class_name);
            }

            this.onClose();
        }
        else if (mode == 2 && !is_null(data)) {

            // -----------------------------------------------
            // Refresh changed line after update (button Save)
            // -----------------------------------------------

            content = makeTabLineColumns(data, this.props['columns'], data['selected'] || '');

            if (this.backup.command == 'blank') {
                this.current.remove();

                var i = this.container.children().length;
                var x = makeTabLineAttrs(data, class_name, i);
                var selected = x[0], id = x[1];
                var row = makeTabLineRow(TEMPLATE_NEW_CONFIG_ITEM, class_name, i, selected, '');

                this.container.append(row);

                var ob = $("#"+TEMPLATE_NEW_CONFIG_ITEM);

                ob.attr('id', id);

                if (this.backup.is_nodata)
                    this.container.removeAttr('id');

                content = makeTabLineColumns(data, this.props['columns'], selected);

                this.set_current(ob);

                this.set_total();
            }

            this.runCallback(this.current);

            this.current.addClass(class_name);

            if (this.is_blank && $web_free())
                this.confirmation("service:add");
            else
                this.close();
        }
        else if (mode == 3 || (mode == 2 && is_null(data))) {

            // --------------------------------------
            // Remove current line (confirmed remove)
            // --------------------------------------

            this.current.remove();

            var len = this.container.children().length;

            is_nodata = len==0 ? true : false;

            var current = null;

            if (is_nodata) {
                this.set_nodata(class_name, is_nodata);
                this.container = null;
                this.current = null;
                content = '';
            }
            else {
                var number = this.number > len ? len : this.number;

                this.container.children().each(function(i) {
                    var ob = $(this);
                    
                    var x = ob.attr('id').split(':');
                    x[x.length-1] = i+1;
                    var id = x.join(':');
                    ob.attr('id', id);
                    
                    var n = parseInt($_get_item_id(ob, 2)) || 0;
                    if (is_null(current) && (n >= number || number == i+1))
                        current = ob;
                    ob.removeClass('even').removeClass('odd').addClass(class_even_odd(i));
                });

                this.set_current(current);
            }

            this.set_total();

            this.runCallback(this.current);
        }

        if (content.length > 0)
            this.current.html(content);

        if (mode == 0) {
            this.container.find("input").bind("change", function() { $ConfigSelector.is_changed = true; });

            if (this.is_blank)
                $(window).scrollTop($(document).height());
        }
    },

    onButtonClick: function(ob, command) {
        if (is_null(command)) {
            var x = ob.attr('id').split(DEFAULT_HTML_SPLITTER);
            command = x[1];
        }

        // ------------------------------------------
        // Press a design mode button: Save or Cancel
        // ------------------------------------------

        switch(command) {
            case 'save':
                this.save(command);
                break;
            case 'back':
                this.setContent(1);
                this.close();
                break;
            default:
                $ShowError('Command is not responsable:'+this.get_mode()+':'+command, true, true, false);
        }
    },

    onIconClick: function(ob) {
        var id = ob.attr('id');
        var x = id.split(DEFAULT_HTML_SPLITTER);
        var command = x[1];

        switch(command) {
            case 'link':
                this.selected_link = x[2];

                var link = this.links[this.selected_link];
                var reference = link.reference;
                var alias = link.alias;
                var value = link.value || '';
                var mode = command+
                    DEFAULT_HTML_SPLITTER+getsplitteditem(reference, '.', 1, '')+
                    DEFAULT_HTML_SPLITTER+value;

                //alert(mode+', alias:'+alias);

                $ReferenceDialog.confirmation(mode, function(x) { $ConfigSelector.onLinkUpdate(x); });
                break;
            default:
                $ShowError('Command is not responsable:'+this.get_mode()+':'+command, true, true, false);
        }
    },

    onLinkUpdate: function(x) {
        var id = x.id;
        var value = x.value;
        var link = this.links[this.selected_link];

        //alert(id+':'+value+':'+this.selected_link+':'+reprObject(link));

        // ----------------------------
        // Keep updated link item value
        // ----------------------------

        if (link.link != 1)
            return;

        var ob = $("#"+this.selected_link);

        //alert(ob.attr('id'));

        ob.val(value);

        var data = this.data[0];

        data[link.name] = id;

        if (link.alias && link.name != link.alias)
            data[link.alias] = value;

        //alert(reprObject(data));

        // ---------------------
        // Set active link value
        // ---------------------

        this.active_links[link.name] = id;

        this.is_changed = true;
    },

    confirmation: function(command) {
        var action = this.actions['default'];
        var x = command.split(DEFAULT_HTML_SPLITTER);
        var service = x[0];
        var command = x.length > 1 ? x[1] : command;
        var mode = this.get_mode();
        var id = this.rid || '';

        // -------------------------
        // Check if command is valid
        // -------------------------

        if ((['add','update','remove'].indexOf(command) == -1) ||
            (is_empty(id) && ['update','remove'].indexOf(command) > -1) ||
            //(this.backup.command && (this.backup.command != command || command == 'add')) || 
            (this.backup.oid && this.backup.oid == this.oid) ||
            !IsAdmin) {

            //alert('invalid:'+command+':'+this.backup.command+':'+this.oid+':'+this.backup.oid);

            $InProgress(null);
            return;
        }

        this.actions.command = command;

        // -------------------
        // Remove current line
        // -------------------

        if (command == 'remove') {
            confirm_action = 'config:remove';
            $ConfirmDialog.open(keywords['Command:Config item removing'], 500);

            return;
        }

        // -------------------------------------
        // Activate blank mode (make a new line)
        // -------------------------------------

        if (command == 'add') {
            this.is_blank = true;
            command = 'blank';
            id = '';
        }

        // -------------
        // else - update
        // -------------

        this.backup.command = command;

        var params = {'command':command, 'mode':mode, 'id':id};

        if (this.IsLog)
            console.log('$ConfigSelector.confirmation:'+command);

        $web_logging(action, function(x) { $ConfigSelector.open(x); }, params);
    },

    check: function(x) {
        var errors = x['props']['errors'];

        if (this.IsLog)
            console.log('$ConfigSelector.check, errors:', errors.length);

        if (!is_null(errors) && errors.length > 0) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
            this.is_error = true;
            return;
        }

        this._response(x);

        switch (this.actions.command) {
            case 'add':
            case 'update':
                confirm_action = 'config:refresh';
                this.setContent(2);
                break;
            case 'remove':
                confirm_action = 'config:remove';
                this.setContent(3);
                break;
        }

        if (!is_empty(this.oid))
            $NotificationDialog.open(keywords['Message:Action was done successfully']);
        else
            $ShowError('Error in action: '+this.get_mode()+':'+this.actions.command, true, true, false);
    },

    save: function(command) {
        var mode = this.get_mode();
        var action = this.actions['default'];
        var params = {'command':command, 'mode':mode};

        params['items'] = this.collect_items();
        params['id'] = this.props['id'] || '';

        if (this.IsLog)
            console.log('$ConfigSelector.save, params:'+reprObject(params)+', current:'+this.current.attr('id'));

        this.is_changed = false;

        $web_logging(action, function(x) { $ConfigSelector.check(x); }, params);
    },

    remove: function(command) {
        var mode = this.get_mode();
        var action = this.actions['default'];
        var id = this.rid || '';
        var params = {'command':command, 'mode':mode, 'query':'', 'id':id};

        if (this.IsLog)
            console.log('$ConfigSelector.remove:'+action+':'+command+', mode:'+mode+', id:'+id);

        $web_logging(action, function(x) { $ConfigSelector.check(x); }, params);
    },

    open: function(x) {
        this._response(x);

        if (this.IsLog)
            console.log('$ConfigSelector.open');

        this.setContent(0);

        $SidebarControl.onFrameMouseOut();

        this.is_open = true;
    },

    confirmed: function(command) {
        switch(command) {
            case 'continue':
                this.is_changed = false;
                this.move(this.backup.confirmed, 1);
                this.toggle(this.backup.confirmed);
                break;
            case 'remove':
                this.remove(this.actions.command);
                break;
        }
    },

    onClose: function() {
        this.is_blank = false;

        this.backup.is_nodata = false;
        this.backup.oid = '';
        this.backup.command = '';
        this.backup.html = null;
        //this.backup.confirmed = null;

        this.mapping = null;
        data = null;
    },

    close: function(x) {
        this.is_open = false;
        this.onClose();
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

    // https://jwcooney.com/2015/01/25/how-to-fix-a-jquery-ui-dialog-strangely-positioning-itself/

    $("#reference-container").dialog({
        autoOpen: false,
        buttons: [
            {text: keywords['OK'], click: function() { $ReferenceDialog.confirmed('ok'); }},
            {text: keywords['Cancel'],  click: function() { $ReferenceDialog.close(); }}
        ],
        modal: true,
        draggable: true,
        resizable: true,
        //position: {my: "right top", at: "right top", of: "#line-content", collision: "none"},
        //position: {my: "center center", at: "center center", of: window, collision: "none"},
        //position: {my: "right top", at: "right-40px top+20px", of: window, collision: "none"},
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
