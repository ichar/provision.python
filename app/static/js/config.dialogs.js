// **********************************************
// CONFIGURATOR DIALOGS: /configurator.dialogs.js
// ----------------------------------------------
// Version: 1.0
// Date: 22-06-2019

// ===========================
// Dialog windows declarations
// ===========================

var separator = '-';

var TEMPLATE_CONFIG_ID = 'config_value' + separator;
var TEMPLATE_NEW_CONFIG_ITEM = 'new-config-item';

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
