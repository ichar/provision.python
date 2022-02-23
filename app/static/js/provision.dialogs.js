// ***************************************
// PROVISIO DIALOGS: /provision.dialogs.js
// ---------------------------------------
// Version: 1.0
// Date: 25-06-2019

// ===========================
// Dialog windows declarations
// ===========================

var $ProvisionServiceDialog = {
    container    : null,
    form         : null,

    // ========================
    // Provision Uploader Class
    // ========================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    id           : null,
    action       : '',
    default_form : 'filter',

    init: function(id) {
        this.id = id;

        if (!is_empty(this.id))
            this.container = $("#"+this.id+"-confirm-container");

        this.form = $("#"+(this.id || this.default_form)+"-form");
    },

    upload: function() {
        this.init('provisionuploader');

        $("#filename", this.form).prop('placeholder', keywords['Choose a File']).val('');
        $("#uploadButton", this.form).val('');
        $("#command", this.form).val('admin:upload');

        $BaseDialog.open(this.id);
    },

    download: function() {
        this.init();

        confirm_action = 'admin:download';

        $ConfirmDialog.open(
            keywords['Command:Provision Orders downloading'] + '<br>' +
            keywords['Data will be filtered accordingly'] + 
            '', 
            500);
    },

    deleteOrders: function() {
        this.init();

        confirm_action = 'admin:delete-orders';

        $ConfirmDialog.open(
            keywords['Command:Provision Orders deleting'] + '<br>' +
            keywords['Data will be filtered accordingly'] + 
            '', 
            500);
    },

    clearHistory: function() {
        this.init();

        confirm_action = 'admin:clear-history';

        $ConfirmDialog.open(
            keywords['Command:Provision Orders history clearing'] + '<br>' +
            keywords['Data will be filtered accordingly'] + 
            '', 
            500);
    },

    sendApproval: function() {
        this.action = null;

        confirm_action = 'admin:send-approval';

        $ConfirmDialog.open(
            keywords['Command:Provision Orders send approval request'] + '<br>' +
            'ID: ' + SelectedGetItem(LINE, 'id') + 
            '', 
            500);
    },

    sendReviewNotification: function() {
        this.action = null;

        confirm_action = 'admin:send-review-notification';

        $ConfirmDialog.open(
            keywords['Command:Provision Review notification request'] + '<br>' +
            keywords['Data corresponds to the current status'] + 
            '', 
            600);
    },

    sendOrderNotification: function() {
        this.action = null;

        confirm_action = 'admin:send-order-notification';

        $ConfirmDialog.open(
            keywords['Command:Provision Order notification request'] + '<br>' +
            'ID: ' + SelectedGetItem(LINE, 'id') + 
            '', 
            500);
    },

    lived: function(action) {
        var callback = null;

        switch (confirm_action) {
            case 'admin:send-approval':
                this.action = '844';
                params = {};
                callback = approval_sent;
                break;
            case 'admin:send-review-notification':
                this.action = '851';
                params = {};
                callback = approval_sent;
                break;
            case 'admin:send-order-notification':
                this.action = '852';
                params = {};
                callback = approval_sent;
                break;
        }

        if (!is_empty(this.action))
            $Handle(this.action, function(x) { callback(x); }, params);
    },

    confirmed: function(command) {
        $("#command", this.form).val(command || confirm_action);

        $BaseDialog.run(this.default_form);
    }
};

var $ProvisionImageLoader = {
    container    : null,

    // ========================
    // Provision Selector Class
    // ========================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    action  : null,
    command : null,
    ob      : null,

    init: function() {},

    add_document: function(ob, command) {
        this.action = 'upload';
        this.command = command;
        this.ob = ob;

        var order_id = SelectedGetItem(LINE, 'id');
        var box = $("#uploadDocument");

        //alert(box.attr('id'));

        var data = new FormData();

        data.append('action', this.action);
        data.append('file', box[0].files[0]);
        data.append('order_id', order_id);
        data.append('filename', $("#document_filename").val());
        data.append('note', $("#document_value").val());
        data.append('for_audit', $("#document_for_audit").prop('checked') ? 1 : 0);
        data.append('model', model);

        $web_uploader(this.action, data, function(x) { 
            $PageLoader.handle_document('847', $ProvisionImageLoader.ob, $ProvisionImageLoader.command, x); 
        });
    }
};

var $ProvisionSelectorDialog = {
    base         : $BaseScreenDialog,

    // ========================
    // Provision Selector Class
    // ========================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    // ---------------------
    // Base class attributes
    // ---------------------

    // ID of base container
    id           : null,
    // Mode of screen available
    mode         : 'available',
    // Flag to use cache
    with_cache   : 0,
    // Flag to lock screen
    with_lock    : 0,

    check_limit_height  : 0,

    // ---------------
    // Form's controls 
    // ---------------

    form         : null,

    timeout      : 300,
    timer        : null,

    // ----------------
    // Local attributes
    // ----------------

    command      : null,
    oid          : null,
    data         : null,
    columns      : null,
    props        : null,

    disabled_form  : '', //' disabled',
    check_on_exit  : false,

    is_active    : false,
    is_open      : false,
    is_error     : false,

    // Flag: this is mobile frame
    is_mobile    : null,

    input_ids    : null,

    init: function(ob, id, title, css) {
        this.id = id;

        this.form = $("#"+this.id+"-form");

        this.base.init(ob, this.id, this);

        if (this.IsLog)
            console.log('$ProvisionSelectorDialog.init:', this.id, this.base.form.width(), this.base.form.height());

        if (!is_null(this.base.box) && !is_empty(css))
            this.base.box.removeClass('create'+this.id).removeClass('update'+this.id).addClass(css);

        if (!is_empty(title))
            this.base.container.dialog("option", "title", title);

        this.oid = $LineSelector.get_id();

        this.initState();
    },

    initState: function() {
        this.is_mobile = $_mobile();

        this.with_lock = this.is_mobile ? 1 : 0;
        this.disabled_form = this.is_mobile ? ' disabled' : '';

        //this.IsTrace = this.is_mobile ? 1 : 0;
    },

    is_focused: function() {
        return this.is_open;
    },

    term: function() {
        this.base.term();
        this.is_open = false;
    },

    reset: function() {
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

    set_disabled_form: function(disabled) {
        var ids = disabled ? [] : (!is_null(this.input_ids) ? this.input_ids.slice() : []);

        $(":input", this.form).each(function() {
            var ob = $(this);
            var id = ob.attr('id');

            if (disabled) {
                if (!ob.prop("disabled")) {
                    $(this).prop("disabled", true);
                    ids.push(id);
                }
            }
            else if (ids.indexOf(id) > -1) {
                $(this).prop("disabled", false);
            }
        });

        this.input_ids = ids.slice();
    },

    setDefaultSize: function() {
        var offset = {'H' : [210, 0, 0], 'W' : [65, 0, 0], 'init' : [0, 760-$_width(this.mode)]};

        if (this.IsTrace)
            alert('$ProvisionSelectorDialog.setDefaultSize');

        this.base.setDefaultSize(offset);

        if (this.disabled_form)
            this.set_disabled_form(true);

        $BaseDialog.open(this.id);
    },

    checked: function(response) {
        var data = getObjectValueByKey(response, 'data', null);
        var errors = getObjectValueByKey(response, 'errors', null);

        if (!is_empty(errors)) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
            this.is_error = true;
        }
        else {
            var id = getObjectValueByKey(data, 'action_id', '');
            var message = getObjectValueByKey(data, 'message', '');

            if (this.IsTrace)
                alert('action_id:['+id+']:'+message);

            if (!is_empty(id)) {
                $_set_body_value(this.id+'_id', id);

                confirm_action = this.id+'.checked';

                $NotificationDialog.open(message);
            }

            this.check_on_exit = true;
        }
    },

    enabled: function() {
        var self = $ProvisionSelectorDialog;

        if (this.IsDebug)
            alert('enabled');

        this.columns.forEach(function(name, index) {
            var control_id = self.id+'_'+name;
            var prop = self.props[name];
            var prop_type = prop['type'];
            var prop_disabled = prop['disabled'];
            var ob = $("#"+control_id, self.base.form);

            if (prop_disabled) {
                ob.prop("disabled", false);

                if (prop_type == 1) {
                    var new_ob = $("#new_"+control_id, self.base.form);
                    new_ob.prop("disabled", false);
                }
            }
        });
    },

    refreshed: function(x) {
        var self = $ProvisionSelectorDialog;

        if (this.IsDebug)
            alert('refreshed');

        this.data = x['data'];
        this.columns = x['columns'];
        this.props = x['props'];

        this.columns.forEach(function(name, index) {
            var control_id = self.id+'_'+name;
            var value = self.data[name];
            var prop = self.props[name];
            var prop_type = prop['type'];
            var prop_disabled = prop['disabled'];
            var ob = $("#"+control_id, self.base.form);

            if (self.IsLog)
                console.log(name, value, prop, is_exist(ob), prop_disabled);

            if (prop_type == 2)
                ob.prop("selectedIndex", value);
            else if (prop_type == 1) {
                var sob = $("#new_"+control_id, self.base.form);
                if (!is_null(sob))
                    sob.val('');
                ob.val(value);
            }
            else
                ob.val(value);

            ob.prop("disabled", prop_disabled);

            if (prop_type == 1) {
                var new_ob = $("#new_"+control_id, self.base.form);
                new_ob.prop("disabled", prop_disabled);
            }
        });

        this.open(this.command);
    },

    resize: function() {
        this.onResize();
    },

    open: function(command) {
        $("#command", this.base.form).val('admin:'+command);

        if (this.IsDebug)        
            alert('open:'+command);

        var cacheid = this.base.cacheid;
        var html = this.base.box.html().replace(this.id+'-form', cacheid); 

        this.base.load(html);

        this.setDefaultSize();

        this.is_open = true;
    },

    create: function(id) {
        this.command = 'create'+id;

        this.init(null, id, keywords['Title:Create form of']+getattr(form_caption, id, 'object'), this.command);

        var action = '843';
        var params = {'command':this.command};

        no_window_scroll = true;

        $Handle(action, function(x) { $ProvisionSelectorDialog.refreshed(x); }, params);
    },

    update: function(id) {
        this.command = 'update'+id;

        this.init(null, id, keywords['Title:Update form of']+getattr(form_caption, id, 'object'), this.command);

        var action = '843';
        var params = {'command':this.command, 'id':this.oid};

        if (is_empty(this.oid)) {
            alert('$ProvisionSelectorDialog.update, oid is empty!');
            return;
        }

        $Handle(action, function(x) { $ProvisionSelectorDialog.refreshed(x); }, params);
    },

    delete: function(id) {
        this.command = 'delete'+id;

        this.init(null, id);

        no_window_scroll = true;

        confirm_action = 'admin:delete'+id;

        $ConfirmDialog.open(
            keywords['Command:'+capitalize(current_context)+' '+capitalize(id)+' removing'] + 
            '<br><div class="removescenario">'+keywords['ID '+current_context+' '+id]+':&nbsp;<span>'+this.oid+'</span></div>', 
            500);
    },

    clone: function(id) {
        this.command = 'clone'+id;

        this.init(null, id, keywords['Title:Clone form of']+getattr(form_caption, id, 'object'), this.command);

        if (is_empty(this.oid)) {
            alert('$ProvisionSelectorDialog.clone, oid is empty!');
            return;
        }

        var action = '843';
        var params = {'command':this.command, 'id':this.oid};

        no_window_scroll = true;

        $Handle(action, function(x) { $ProvisionSelectorDialog.refreshed(x); }, params);
    },

    refreshItem: function(ob) {
        var oid = ob.attr('id');
        var params = null;
        var callback = null;

        switch (oid) {
            case 'order_seller':
                this.action = '855';
                var command = 'seller';
                params = {'command':command, 'id':ob.val()};
                confirm_action = command;
                callback = refresh_order_item;
                break;
        }

        if (!is_empty(this.action))
            $Handle(this.action, function(x) { callback(x); }, params);
    },

    confirmed: function() {
        var action = '864';
        var params = {'command':this.command, 'submit':1};

        $Handle(action, function(x) { $ProvisionSelectorDialog.checked(x); }, params);
    },

    validate: function() {
        var self = $ProvisionSelectorDialog;

        var action = '845';
        var is_limited_length = ['create'+this.id, 'clone'+this.id].indexOf(this.command) > -1 ? 1 : 0;
        var params = {'command':this.command, 'submit':1, 'is_limited_length':is_limited_length};

        this.columns.forEach(function(name, index) {
            var control_id = self.id+'_'+name;
            var ob = $("#"+control_id, self.base.form);

            if (!is_null(ob))
                params[control_id] = ob.val();

            var prop = self.props[name];
            var prop_type = prop['type'];

            if (prop_type == 1) {
                var new_id = 'new_'+control_id;
                var new_ob = $("#"+new_id, self.base.form);

                if (!is_null(new_ob))
                    params[new_id] = new_ob.val();
            }
        });

        $Handle(action, function(x) { $ProvisionSelectorDialog.checked(x); }, params);
    },

    onResize: function() {
        /*
        if (this.is_open && $_mobile()) {
            this.cancel();

            this.setDefaultSize();
        }
        */
    },

    onOpen: function() {
        var self = $ProvisionSelectorDialog;

        $BaseScreenDialog.onOpen();

        if (!this.is_active) {
            this.timer = setTimeout(function() { 
                self.set_disabled_form(false);
                window.clearTimeout(self.timer);
                self.timer = null; 
            }, this.timeout);
        }
    },

    onClose: function() {
        this.term();

        if (this.check_on_exit)
            this.exit();
    },

    cancel: function() {
        $BaseDialog.cancel();
    },

    exit: function() {
        if (this.command == 'update'+this.id)
            $ShowOnStartup();
        else
            $onRefreshClick();

        this.check_on_exit = false;
    }
};

var $ProvisionReviewDialog = {
    base         : $BaseDialog,

    container    : null,
    box          : null,
    ob           : null,

    total_selected_row : null,
    total_selected_info : null,

    // ======================
    // Provision Review Class
    // ======================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    action       : '',
    command      : null,
    id           : null,
    mode         : null,
    params       : null,
    oid          : null,
    force        : null,

    timer        : null,

    init: function() {
        this.container = $("#"+this.id+"-confirm-container");
        this.oid = $LineSelector.get_id();
        this.total_selected_row = $("#total_selected_row");
        this.total_selected_info = $("#total_selected_info");
    },

    term: function() {
        this.container = null;
        this.box = null;
        this.ob = null;
        this.action = '';
        this.command = null;
        this.id = null;
        this.params = null;
        this.oid = null;

        selected_menu_action = '';
        is_input_focused = false;

        this.base.onClose();
    },

    reset: function() {
    },

    lock_scroll: function() {
    },

    unlock_scroll: function() {
    },

    setDefaultSize: function(mode) {
        this.box = $("#"+this.id+"-box");

        var caption = null;
        var s = '';

        switch (mode) {
            case 'delivered':
                $("#delivered_in_part").show();
                this.container.dialog("option", "height", 322);
                break;
            default:
                $("#delivered_in_part").hide();
                this.container.dialog("option", "height", 296);
        }

        switch (mode) {
            case 'decree':
                caption = $("*[class~='order']", $("#"+this.id+"-request")).first();
                s = ' № '+this.oid+'.';
                break;
            default:
                $("#order-request").html(keywords[
                    mode == 'paid' ? 'Assign pay date for the current order' : (
                    mode == 'delivered' ? 'Assign delivery date for the current order' : (
                    mode == 'failure' ? 'Assign failure date for the current order' : 
                        'You have to assign due date for confirmation of the order'
                    ))
                ]);
                $("#review-caption").html(keywords[
                    mode == 'paid' ? 'Order pay date assigment see in the application documentation' : (
                    mode == 'delivered' ? 'Order delivery date assigment see in the application documentation' : (
                    mode == 'failure' ? 'Order failure date assigment see in the application documentation' : 
                        'Review confirmation rules see in the application documentation.'
                    ))
                ]);
                
                caption = $("*[class~='duedate']", this.box).first();

                s = keywords[
                    mode == 'paid' ? 'Order pay date' : (
                    mode == 'delivered' ? 'Order delivery date' : (
                    mode == 'failure' ? 'Order failure date' : 
                        'Review due date'
                    ))
                ] + ':';
        }

        if (!is_empty(s))
            caption.html(s);
        /*
        if (mode == 'failure')
            this.container.dialog("option", "height", 314);
        */
    },

    open: function(ob, mode) {
        if (this.IsTrace)
            alert('$ProvisionReviewDialog.open, mode:'+mode);

        this.ob = ob;

        switch (mode) {
            case 'review':
                this.command = 'REVIEW_CONFIRM';
                this.action = '834';
                this.id = 'review';
                break;
            case 'paid':
                this.command = 'REVIEW_PAID';
                this.action = '846';
                this.id = 'review';
                break;
            case 'delivered':
                this.command = 'REVIEW_DELIVERED';
                this.action = '854';
                this.id = 'review';
                break;
            case 'failure':
                this.command = 'REVIEW_FAILURE';
                this.action = '858';
                this.id = 'review';
                break;
            case 'decree':
                this.command = 'REVIEW_DECREE';
                this.action = '857';
                this.id = 'decree';
                break;
        }

        this.init();

        this.setDefaultSize(mode);

        this.base.open(this.id);
    },

    handle: function(response) {
        $PageLoader.refresh_after_review(response);

        this.base.close();

        this.term();
    },

    validate: function() {
        if (this.id == 'decree')
            this.params = {
                'command':this.command, 
                'decree_title' : $("#decree_title").val(), 
                'decree_note' : $("#decree_note").val(), 
                'decree_duedate' : $("#decree_duedate").val(), 
                'decree_executor' : $("#decree_executor").val()
            };
        else
            this.params = {
                'command':this.command, 
                'review_duedate' : $("#review_duedate").val(), 
                'delivered_in_part' : $("#item-delivered-in-part").prop('checked') ? 1 : 0,
                'with_mail' : $("#item-with-mail").prop('checked') ? 1 : 0
            };

        should_be_updated = true;
        selected_menu_action = this.action;
        $InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $ProvisionReviewDialog.handle(x); }, this.params);
    },

    is_line_unread: function() {
        return $LineSelector.get_current().attr('class').split(' ').indexOf('unread') > -1 ? 1 : 0;
    },

    set_unread: function(ob, force) {
        this.ob = ob;
        this.action = '848';
        this.command = 'SET_UNREAD';

        this.force = force || 0;

        if (this.is_line_unread())
            return;

        this.params = {
            'command':this.command,
            'total_selected':this.total_selected_info.html(),
            'force':force
        };

        should_be_updated = true;
        selected_menu_action = this.action;
        $InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $ProvisionReviewDialog.done(x); }, this.params);
    },

    set_read: function(ob, mode, force) {
        this.ob = ob;
        this.action = '849';
        this.command = 'SET_READ';
        this.mode = mode;

        this.force = force || 0;

        if (mode == 'all' && force) {
            this.total_selected_row.html('0.00');
            this.total_selected_info.html('0 | 0.00');
        }
        else if (!this.is_line_unread())
            return;

        this.params = {
            'command':this.command,
            'mode':mode || '',
            'total_selected':this.total_selected_info.html(),
            'force':force
        };

        should_be_updated = true;
        selected_menu_action = this.action;
        $InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $ProvisionReviewDialog.done(x); }, this.params);
    },

    print_order: function(ob) {
        this.ob = ob;
        this.action = default_print_action;
        this.command = 'PRINT_ORDER';

        this.params = {
            'command':this.command
        };

        should_be_updated = true;
        selected_menu_action = this.action;
        $InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $ProvisionReviewDialog.done(x); }, this.params);
    },

    onOpen: function() {
        is_input_focused = true;
    },

    onClose: function() {
        this.term();
    },

    update_total: function(x) {
        if (this.IsLog)
            console.log('$ProvisionReviewDialog.update_totale:', x);

        var data = getObjectValueByKey(x, 'data', null);
        var total_selected = getattr(data, 'total_selected', '0 | 0.00');

        if (is_empty(total_selected))
            return;

        var x = total_selected.split('|');

        if (is_empty(x) || x.length != 2)
            return;

        var rows = strip(x[0]);
        var total = strip(x[1]);

        if (this.IsDebug)
            alert('$ProvisionReviewDialog.update_total:'+rows+':'+total);

        this.total_selected_row.html(total);

        function clear_timeout() {
            if (!is_null(this.timer)) {
                clearTimeout(this.timer);
                this.timer = null;
            }
        }

        function hide(ob) {
            clear_timeout();
            ob.hide();
        }

        function down(ob) {
            this.timer = setTimeout(function() { hide(ob); }, 10000);
        }

        if (is_exist(this.total_selected_info) && this.force) {
            this.total_selected_info.html(total_selected);

            if (this.mode == 'all' || search_is_empty())
                return;

            var ob = this.total_selected_info.parent();
            var top = 50;
            var left = $_width('client')-280;

            clear_timeout();

            ob.css({'top':top, 'left':left}).show()
                .animate({height:$_get_css_size(20), width:$_get_css_size(200)}, 600, "easeInQuad", 
                    function() { down(ob); });
        }
    },

    done: function(x) {
        var self = $ProvisionReviewDialog;

        $InProgress(self.ob, 0);

        self.update_total(x);

        if (should_be_updated) {
            var ob = SelectedGetItem(LINE, 'ob');
            var items = self.mode == 'all' ? $LineSelector.getSelectedItems(null) : [ob];

            switch (self.command) {
                case 'SET_UNREAD':
                    ob.addClass("unread");
                    break;
                case 'SET_READ':
                    items.forEach(function(x, index) {
                        x.removeClass("unread");
                    });
                    break;
                case 'PRINT_ORDER':
                    printProvisionOrder(x);
                    break;
            }
        }

        self.term();
    },

    cancel: function() {
        this.base.cancel();

        this.term();
    },

    is_focused: function() {
        return this.base.is_focused();
    }
};

var $ProvisionDecreeDialog = {
    base         : $BaseDialog,

    container    : null,
    box          : null,
    ob           : null,

    // ======================
    // Provision Decree Class
    // ======================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    default_height : 620,

    action       : '',
    command      : null,
    id           : null,
    mode         : null,
    data         : null,
    params       : null,
    oid          : null,
    review_id    : null,
    decree_id    : null,
    report_id    : null,
    is_author    : 0,
    is_executor  : 0,
    save_duedate : null,

    is_show_loader : 0,

    columns      : ['author','title','note','duedate','executor','report','status'],
    buttons      : ['validate','finish','reject','remove'],

    init: function() {
        this.container = $("#"+this.id+"-confirm-container");
        this.oid = $LineSelector.get_id();

        this.is_show_loader = IsShowLoader;
    },

    term: function() {
        if (this.IsTrace)
            alert('term');

        this.clear();

        this.container = null;
        this.box = null;
        this.ob = null;
        this.action = '';
        this.command = null;
        this.id = null;
        this.mode = null;
        this.data = null;
        this.params = null;
        this.oid = null;
        this.review_id = null;
        this.decree_id = null;
        this.report_id = null;
        this.is_author = 0;
        this.is_executor = 0;
        this.save_duedate = null;

        should_be_updated = false;
        selected_menu_action = '';

        is_input_focused = false;

        this.base.onClose();
    },

    clear: function() {
        var self = $ProvisionDecreeDialog;

        if (this.IsLog)
            console.log('$ProvisionDecreeDialog.clear:', self.columns);

        if (is_null(self.columns))
            return;

        self.columns.forEach(function(name, index) {
            var ob = $("#decree_"+name, self.container);
            if (is_exist(ob)) {
                ob.prop("disabled", false);
                ob.val('');
            }
        });
    },

    state_buttons: function(state) {
        this.buttons.forEach(function(name, index) {
            $("#decree-confirm-button-"+name).button(state);
        });
    },

    set_params: function() {
        this.params = {
            'command':this.command, 
            'review_id': this.review_id,
            'decree_id': this.decree_id,
            'report_id': this.report_id,
            'is_author' : this.is_author ? 1 : 0,
            'is_executor' : this.is_executor ? 1 : 0,
            'decree_title' : $("#decree_title").val(), 
            'decree_note' : $("#decree_note").val(), 
            'decree_status' : $("#decree_status").val(), 
            'decree_duedate' : [$("#decree_duedate").val(), this.save_duedate], 
            'decree_author' : $("#decree_author").val(), 
            'decree_executor' : $("#decree_executor").val(), 
            'decree_report' : $("#decree_report").val(), 
        };

        if (this.IsDebug)
            alert(reprObject(this.params));
    },

    check_size: function() {
        var height = this.default_height;
        var ob = $("#"+this.id+'_author', this.container);

        if (is_exist(ob))
            height += 54;

        this.container.dialog("option", "height", Math.min($_height('available'), height));
    },

    reset: function() {
    },

    lock_scroll: function() {
    },

    unlock_scroll: function() {
    },

    setDefaultSize: function(mode) {
        this.box = $("#"+this.id+"-box");

        var caption = null;
        var s = '';

        switch (mode) {
            case 'decree':
                caption = $("*[class~='order']", $("#"+this.id+"-request")).first();
                s = ' № '+this.oid+'.';
                break;
            default:
                break;
        }

        if (!is_empty(s))
            caption.html(s);

        this.check_size();
    },

    handle: function(response) {
        if (this.IsLog)
            console.log('$ProvisionDecreeDialog.handle, mode:'+this.mode, this.id, this.action, response);

        IsShowLoader = this.is_show_loader;

        switch (this.mode) {
            case 'update_decree':
                var self = $ProvisionDecreeDialog;

                this.data = response['data'];
                //this.columns = response['columns'];
                this.props = response['props'];

                this.is_author = getattr(this.data, 'is_author', 0);
                this.is_executor = getattr(this.data, 'is_executor', 0);
                this.save_duedate = getattr(this.data, 'duedate', null);
                
                var is_disabled = getattr(this.data, 'is_disabled', 0);

                this.columns.forEach(function(name, index) {
                    var control_id = self.id+'_'+name;
                    var value = self.data[name];
                    var ob = $("#"+control_id, self.container);
                    var prop_disabled = is_disabled ||
                        (self.props['author'].indexOf(name) > -1 && !self.is_author) || 
                        (self.props['executor'].indexOf(name) > -1 && !self.is_executor) ? true : false;

                    if (self.IsLog)
                        console.log(name, value, is_exist(ob));

                    if (is_exist(ob)) {
                        ob.val(value);
                        ob.prop("disabled", prop_disabled);
                    }
                });

                $("#decree_status").val(this.props['status'][0]);

                this.decree_id = this.data['decree_id'];
                this.report_id = this.data['report_id'];

                if (!is_disabled && (this.is_executor || this.is_author)) {
                    if (this.is_executor) {
                        $("#decree-confirm-button-finish").button("disable");
                        $("#decree-confirm-button-reject").button("disable");
                        $("#decree-confirm-button-remove").button("disable");
                        $("#decree-confirm-button-validate").button("enable");
                    }
                    else if (this.is_author) {
                        $("#decree-confirm-button-finish").button("enable");
                        $("#decree-confirm-button-reject").button("enable");
                        $("#decree-confirm-button-remove").button("enable");
                        $("#decree-confirm-button-validate").button("enable");
                    }
                }
                else {
                    $("#decree-confirm-button-finish").button("disable");
                    $("#decree-confirm-button-reject").button("disable");
                    $("#decree-confirm-button-remove").button("disable");
                    $("#decree-confirm-button-validate").button("disable");
                }

                if (this.is_executor)
                    $("#decree_report", this.container).prop("disabled", false);

                this.setDefaultSize('decree');

                this.base.open(this.id);

                break;
            case 'finish_decree':
            case 'reject_decree':
            case 'remove_decree':
            default:
                $PageLoader.refresh_after_review(response);

                this.base.close();

                this.term();
        }
    },

    open: function(ob, mode) {
        if (this.IsLog)
            console.log('$ProvisionDecreeDialog.open, mode:'+mode);

        this.ob = ob;

        switch (mode) {
            case 'decree':
                this.id = 'decree';

                $("#decree-confirm-button-finish").button("disable");
                $("#decree-confirm-button-reject").button("disable");
                $("#decree-confirm-button-remove").button("disable");
                $("#decree-confirm-button-validate").button("enable");

                this.clear();

                $("#decree_report", this.container).prop("disabled", true);
        }

        this.init();

        this.setDefaultSize(mode);

        this.base.open(this.id);
    },

    update_decree: function(ob) {
        var subline = ob.parent().parent();
        var review_id = $_get_item_id(subline);

        if (this.IsLog)
            console.log('$ProvisionDecreeDialog.update_decree, review_id:'+review_id);

        $SublineSelector.set_current(subline);

        this.ob = ob;

        this.command = 'UPDATE_DECREE';
        this.action = '843';
        this.id = 'decree';
        this.mode = 'update_decree';

        this.review_id = review_id;

        this.params = {
            'command':this.command,
            'review_id':this.review_id,
        };

        this.init();

        IsShowLoader = 0;

        this.state_buttons('disable');

        //$InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $ProvisionDecreeDialog.handle(x); }, this.params);

        interrupt(true, 5, 500);
    },

    finish: function(mode) {
        if (mode == 0) {
            confirm_action = 'decree:finish';

            $ConfirmDialog.open(
                keywords['Command:Decree finish'] +
                '', 
                600);

            return;
        } else {
            this.command = 'FINISH_DECREE';
            this.action = '857';
            this.mode = 'finish_decree';

            this.set_params();
        }

        this.state_buttons('disable');

        IsShowLoader = 1;

        should_be_updated = true;
        selected_menu_action = this.action;
        $InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $ProvisionDecreeDialog.handle(x); }, this.params);
    },

    reject: function(mode) {
        if (mode == 0) {
            confirm_action = 'decree:reject';

            $ConfirmDialog.open(
                keywords['Command:Decree reject'] +
                '', 
                500);

            return;
        } else {
            this.command = 'REJECT_DECREE';
            this.action = '857';
            this.mode = 'reject_decree';

            this.set_params();
        }

        this.state_buttons('disable');

        IsShowLoader = 1;

        should_be_updated = true;
        selected_menu_action = this.action;
        $InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $ProvisionDecreeDialog.handle(x); }, this.params);
    },

    remove: function(mode) {
        if (mode == 0) {
            confirm_action = 'decree:remove';

            $ConfirmDialog.open(
                keywords['Command:Decree remove'] + '<br>' +
                keywords['Item will be removed from database!'] +
                '', 
                550);

            return;
        } else {
            this.command = 'REMOVE_DECREE';
            this.action = '857';
            this.mode = 'remove_decree';

            this.set_params();
        }

        this.state_buttons('disable');

        IsShowLoader = 1;

        should_be_updated = true;
        selected_menu_action = this.action;
        $InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $ProvisionDecreeDialog.handle(x); }, this.params);
    },

    validate: function() {
        if (this.id == 'decree') {
            this.command = 'SAVE_DECREE';
            this.action = '857';
            this.mode = 'save_decree';

            this.set_params();
        }

        this.state_buttons('disable');

        IsShowLoader = 1;

        should_be_updated = true;
        selected_menu_action = this.action;
        $InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $ProvisionDecreeDialog.handle(x); }, this.params);
    },

    cancel: function() {
        if (this.IsTrace)
            alert('cancel');

        this.base.cancel();
        this.term();
    },

    onOpen: function() {
        is_input_focused = true;
    },

    onClose: function() {
        if (this.IsTrace)
            alert('cancel');

        this.term();
    },

    is_focused: function() {
        return this.base.is_focused();
    }
};

var $ProvisionOrderHistoryDialog = {
    base         : $BaseScreenDialog,

    // ==========================
    // Provision Order Base Class
    // ==========================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    // ---------------------
    // Base class attributes
    // ---------------------

    // ID of base container
    id           : null,
    // Mode of screen available
    mode         : 'available',
    // Flag to use cache
    with_cache   : 1,
    // Flag to lock screen
    with_lock    : 1,

    check_limit_height  : 0,

    // ---------------
    // Form's controls 
    // ---------------

    form         : null,

    // ----------------
    // Local attributes
    // ----------------

    action       : '',
    command      : null,
    params       : null,

    // ----------------
    // Local attributes
    // ----------------

    is_active    : false,
    is_open      : false,
    is_error     : false,

    init: function(ob) {
        this.base.init(ob, this.id, this);

        this.initState();
    },

    initState: function() {
        //this.with_lock = $_mobile() ? 1 : 0;
    },

    term: function() {
        this.base.term();

        this.action = '';
        this.command = null;
        this.id = null;
        this.params = null;

        selected_menu_action = '';
    },

    reset: function() {
        this.base.reset(this.with_cache);

        var tab = $("#"+this.id+"-view-content");

        if (!is_exist(tab))
            return;

        $TablineSelector.init(tab);
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

    setDefaultSize: function() {
        var offset = {'H' : [190, 5, 0], 'W' : [64, 0, 0], 'init' : [0, -120]};

        this.base.setDefaultSize(offset);

        var width = $_get_css_size(this.base.ssp['W']['box']);

        $("#history-caption").css({"width" : width, "white-space" : "nowrap"});

        $BaseDialog.open(this.id);
    },

    open: function(ob, mode) {
        if (this.IsTrace)
            alert('$ProvisionOrderHistoryDialog.open, mode:'+mode);

        switch (mode) {
            case 'order':
                this.command = 'ORDER_HISTORY';
                this.action = '853';
                this.id = 'history';
                break;
        }

        this.init(ob);

        this.validate();
    },

    handle: function(x) {
        var self = $ProvisionOrderHistoryDialog;

        if (!is_null(x)) {
            var data = x['data'];
            var props = x['props'];

            this.base.load(
                $updateTabData(selected_menu_action, data['data'], data['config'], data['total'], data['status'], null)
                    .replace('tab-view-content', this.base.cacheid)
            );
        }

        this.base.handle(function() { $ProvisionOrderHistoryDialog.setDefaultSize(); });
    },

    validate: function() {
        this.params = {
            'command':this.command, 
            'history_duedate' : $("#history_duedate").val()
        };

        should_be_updated = true;
        selected_menu_action = this.action;

        this.base.progress();

        $Handle(this.action, function(x) { $ProvisionOrderHistoryDialog.handle(x); }, this.params);
    },

    onOpen: function() {
        $BaseScreenDialog.onOpen();
    },

    onClose: function() {
        this.term();
    },

    confirmed: function() {
        $BaseDialog.close();
    },

    cancel: function() {
        $BaseDialog.cancel();
    }
};

var $ProvisionCheckedReviewersDialog = {
    base         : $BaseDialog,

    // ====================================
    // Order Checked Reviewers Dialog Class
    // ====================================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    command      : null,
    id           : null,
    mode         : null,
    oid          : null,

    init: function() {
        this.base.init(this.id);
        this.oid = $LineSelector.get_id();
    },

    _check_disabled: function(ob) {
        var parent = ob.parents("*[class^='panel']").first();
        return parent.hasClass('disabled');
    },

    activate: function(checked) {
        $ListItemSideControl.activate(checked);
    },

    left: function(ob, force) {
        if (!this._check_disabled(ob))
            $ListItemSideControl.setLeft(ob, force);
    },

    right: function(ob, force) {
        if (!this._check_disabled(ob))
            $ListItemSideControl.setRight(ob, force);
    },

    insert: function(ob) {
        if (!this._check_disabled(ob))
            $ListItemSideControl.onInsertItem(ob);
    },

    remove: function(ob) {
        if (!this._check_disabled(ob))
            $ListItemSideControl.onRemoveItem(ob);
    },

    setDefaultSize: function() {
        var caption = $("*[class~='order']", $("#"+this.id+"-request")).first();
        var s = ' № '+this.oid+'.';

        caption.html(s);
    },

    open: function(ob, mode) {
        if (this.IsTrace)
            alert('$ProvisionCheckedReviewersDialog.open, mode:'+mode);

        switch (mode) {
            case 'order':
                this.command = 'GET_REVIEWERS';
                this.action = '866';
                this.id = 'checked-reviewers';
                break;
        }

        this.init();

        this.setDefaultSize();

        this.validate();
    },

    handle: function(x) {
        if (!is_null(x)) {
            var data = x['data'];
            var props = x['props'];

            if (this.command == 'SET_REVIEWERS') {
                $ListItemSideControl.term();
                //
                // Order Reviewers list has updated
                //
                $BaseDialog.close();
                return;
            }

            $ListItemSideControl.init(this.id);
            $ListItemSideControl.update(data);
        }

        this.base.open(this.id);
    },

    validate: function() {
        this.params = {
            'command':this.command, 
            'data':$ListItemSideControl.getItems().join(DEFAULT_HTML_SPLITTER),
        };

        $Handle(this.action, function(x) { $ProvisionCheckedReviewersDialog.handle(x); }, this.params);
    },

    confirmed: function() {
        this.command = 'SET_REVIEWERS';
        //
        // Update Order Reviewer list
        //
        this.validate();
    },

    cancel: function() {
        this.base.close();
    },

    is_focused: function() {
        return this.base.is_focused();
    }
};

// =======
// Dialogs
// =======

jQuery(function($) 
{
    // --------------------------------
    // Create Scenario Generator Dialog
    // --------------------------------

    $("#provisionuploader-confirm-container").dialog({
        autoOpen: false,
        width:590,
        height:270,
        position:0,
        buttons: [
            {text: keywords['Run'], click: function() { $BaseDialog.confirmed(); }},
            {text: keywords['Reject'], click: function() { $BaseDialog.cancel(); }}
        ],
        modal: false,
        draggable: true,
        resizable: true,
        position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        close: function() {
            $BaseDialog.onClose();
        }
    });

    // -----------------------------
    // Create Provision Order Dialog
    // -----------------------------

    $("#order-confirm-container").dialog({
        autoOpen: false,
        width:0,
        height:0,
        position:0,
        buttons: [
            {text: keywords['Save'], click: function() { $ProvisionSelectorDialog.validate(); }},
            {text: keywords['Cancel'], click: function() { $ProvisionSelectorDialog.cancel(); }}
        ],
        modal: true,
        draggable: true,
        resizable: true,
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        open: function() {
            $ProvisionSelectorDialog.onOpen();
        },
        close: function() {
            $ProvisionSelectorDialog.onClose();
            $BaseDialog.onClose();
        },
        resize: function() {
            $ProvisionSelectorDialog.onResize();
        }
    });

    // --------------------------
    // Confirmation Review Dialog
    // --------------------------

    $("#review-confirm-container").dialog({
        autoOpen: false,
        width:530,
        height:300,
        position:0,
        buttons: [
            {text: keywords['Run'], click: function() { $ProvisionReviewDialog.validate(); }},
            {text: keywords['Reject'], click: function() { $ProvisionReviewDialog.cancel(); }}
        ],
        modal: false,
        draggable: true,
        resizable: false,
        position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        close: function() {
            $ProvisionReviewDialog.onClose();
        }
    });

    // ------------------------------
    // Create Provision Decree Dialog
    // ------------------------------

    $("#decree-confirm-container").dialog({
        autoOpen: false,
        width:778,
        height:620,
        position:0,
        buttons: [
            {
                id: "decree-confirm-button-finish",
                text: keywords['Finished'],
                click: function() {
                    $ProvisionDecreeDialog.finish(0);
                }
            },
            {
                id: "decree-confirm-button-reject",
                text: keywords['Rejected'],
                click: function() {
                    $ProvisionDecreeDialog.reject(0);
                }
            },
            {
                id: "decree-confirm-button-validate",
                text: keywords['Save'],
                click: function() {
                    $ProvisionDecreeDialog.validate();
                }
            },
            {
                id: "decree-confirm-button-remove",
                text: keywords['Remove'],
                click: function() {
                    $ProvisionDecreeDialog.remove(0);
                }
            },
            {
                id: "decree-confirm-button-cancel",
                text: keywords['Close'],
                click: function() {
                    $ProvisionDecreeDialog.cancel();
                }
            }
        ],
        modal: false,
        draggable: true,
        resizable: false,
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        open: function() {
            $ProvisionDecreeDialog.onOpen();
        },
        close: function() {
            $ProvisionDecreeDialog.onClose();
            $BaseDialog.onClose();
        },
    });

    // ----------------------------
    // Order Changes History Dialog
    // ----------------------------

    $("#history-confirm-container").dialog({
        autoOpen: false,
        width:0,
        height:0,
        position:0,
        buttons: [
            {text: keywords['OK'], click: function() { $ProvisionOrderHistoryDialog.confirmed(); }},
            {text: keywords['Cancel'], click: function() { $ProvisionOrderHistoryDialog.cancel(); }}
        ],
        modal: true,
        draggable: true,
        resizable: false,
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        open: function() {
            $ProvisionOrderHistoryDialog.onOpen();
        },
        close: function() {
            $ProvisionOrderHistoryDialog.onClose();
            $BaseDialog.onClose();
        }
    });

    // ----------------------------------------
    // Provision Order Checked Reviewers Dialog
    // ----------------------------------------

    $("#checked-reviewers-confirm-container").dialog({
        autoOpen: false,
        width:640,
        height:474,
        position:0,
        buttons: [
            {text: keywords['OK'], click: function() { $ProvisionCheckedReviewersDialog.confirmed(); }},
            {text: keywords['Cancel'], click: function() { $ProvisionCheckedReviewersDialog.cancel(); }}
        ],
        modal: true,
        draggable: true,
        resizable: false,
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        close: function() {
            $BaseDialog.onClose();
        }
    });
});
