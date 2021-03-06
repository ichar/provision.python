// **************************************
// PROVISION DIALOGS: /decrees.dialogs.js
// --------------------------------------
// Version: 1.0
// Date: 18-10-2021

// ===========================
// Dialog windows declarations
// ===========================

var $DecreeSelectorDialog = {
    base         : $BaseScreenDialog,

    // =============================
    // Provision Order History Class
    // =============================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    action       : '',
    command      : null,
    id           : null,
    params       : null,
    state        : null,

    // Mode of screen available
    mode         : 'available',
    // Flag to use cache
    with_cache   : 0,
    // Flag to lock screen
    with_lock    : 1,

    check_limit_height  : 0,

    init: function(ob, id) {
        this.id = id;
        this.form = $("#"+this.id+"-form");

        this.base.init(ob, this.id, this);
    },

    term: function() {
        this.base.term();

        this.action = '';
        this.command = null;
        this.id = null;
        this.params = null;
        this.state = null;
        
        selected_menu_action = '';
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

    setDefaultSize: function() {
        var offset = {'H' : [210, 0, 0], 'W' : [65, 0, 0], 'init' : [0, 780-$_width(this.mode)]};

        this.base.setDefaultSize(offset);

        $BaseDialog.open(this.id);
    },

    showbar: function(ob, force) {
        var parent = ob.parent();
        var id = parent.attr('id');
        var x = id.split(':');
        var row_id = x[1]+':'+x[2];
        var info = $("div[id='info:"+row_id+"']", "#line-content");
        
        this.state = !is_null(force) ? force : (ob.hasClass('expanded') ? 1 : 0);

        //alert(id+'='+row_id+'='+this.state);

        if (is_exist(info)) {
            info.removeClass('invisible');
            if (this.state == 1) {
                info.hide();
                ob.removeClass('expanded').addClass('collapsed');
            } else {
                info.show();
                ob.removeClass('collapsed').addClass('expanded');
            }
        }
    },

    expand: function() {
        var self = $DecreeSelectorDialog;

        if (this.IsTrace)
            alert('$DecreeSelectorDialog.expand');

        var obs = $("td[class*='showbar']", "#line-content");

        //alert(obs.length);

        obs.each(function() {
            self.showbar($(this), 0);
        });

        $("button[id='decree:expand']", "#caption").removeClass('btn-primary').addClass('btn-warning');
        $("button[id='decree:collapse']", "#caption").removeClass('btn-warning').addClass('btn-primary');
    },

    collapse: function() {
        var self = $DecreeSelectorDialog;

        if (this.IsTrace)
            alert('$DecreeSelectorDialog.collapse');

        var obs = $("td[class*='showbar']", "#line-content");

        //alert(obs.length);

        obs.each(function() {
            self.showbar($(this), 1);
        });

        $("button[id='decree:expand']", "#caption").removeClass('btn-warning').addClass('btn-primary');
        $("button[id='decree:collapse']", "#caption").removeClass('btn-primary').addClass('btn-warning');
    },

    toggle: function() {
        if (this.IsDebug)
            alert('$DecreeSelectorDialog, state:'+this.state);

        if (!this.state)
            this.collapse();
        else
            this.expand();
    },

    open: function(ob, mode) {
        if (this.IsTrace)
            alert('$DecreeSelectorDialog.open, mode:'+mode);

        this.init(ob, 'decree');

        var header = $("#decree-header", this.base.container);

        switch (mode) {
            case 'update':
                header.html(keywords['Input form items to edit Decree attributes']);
                this.base.container.dialog("option", "buttons", [
                    {text: keywords['Save'], click: function() { $DecreeSelectorDialog.confirmed(); }},
                    {text: keywords['Cancel'], click: function() { $DecreeSelectorDialog.cancel(); }}
                ]);
                break;
            case 'read':
                header.html(keywords['Check form items to apply Decree attributes']);
                this.base.container.dialog("option", "buttons", [
                    {text: keywords['OK'], click: function() { $DecreeSelectorDialog.cancel(); }}
                ]);
                break;
            default:
                return;
        }

        var cacheid = this.base.cacheid;
        var html = this.base.box.html().replace('decree-form', cacheid); 

        this.base.load(html);

        $("#command", this.base.form).val(mode);

        this.setDefaultSize();
    },

    print: function(ob) {
        confirm_action = 'print';

        this.validate(ob);
    },

    handle: function(x) {
        var self = $DecreeSelectorDialog;

        if (self.IsTrace)
            alert('$DecreeSelectorDialog.handle');

        var errors = !is_null(x) ? x['errors'] : null;
        var data = !is_null(x) ? x['data'] : [];
        var total = !is_null(x) ? x['total'] : 0;
        var props = !is_null(x) ? x['props'] : {};

        if (self.IsDebug)
            alert(reprObject(data));

        switch (this.command) {
            case 'DECREE_ORDERS_PRINT':
                printDecreeOrders(data, props);
                return;
        }

        self.term();
    },

    validate: function(ob) {
        if (this.IsTrace)
            alert('$DecreeSelectorDialog.validate');

        this.init(ob, 'decree-orders');

        switch (confirm_action) {
            case 'print':
                this.command = 'DECREE_ORDERS_PRINT';
                this.action = '874';
                this.params = {'command':this.command, 'uid':uid};
                break;
        }

        selected_menu_action = this.action;

        this.base.progress();

        $Handle(this.action, function(x) { $DecreeSelectorDialog.handle(x); }, this.params);
    },

    onOpen: function() {
        var self = $DecreeSelectorDialog;

        $BaseScreenDialog.onOpen();
    },

    onClose: function() {
        this.term();
    },

    confirmed: function() {
        $BaseDialog.confirmed();
        
        this.onClose();
    },

    cancel: function() {
        $BaseDialog.cancel();
       
        this.onClose();
    }
};

var $DecreeSubmitDialog = {
    base         : $BaseDialog,

    // =================================
    // PaymentReview Submit Dialog Class
    // =================================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    command      : null,
    id           : null,
    mode         : null,

    callback: function() {
        return this.base.callback();
    },

    is_focused: function() {
        return this.base.is_focused();
    },

    get_state: function() {
        return $DecreeSelectorDialog.state === 0 ? 'expand' : 'collapse';
    },

    setDefaultSize: function() {
        this.base.open(this.id);

        switch (this.mode) {
            case 'selectdate':
                // chain a few methods for the first datepicker, jQuery style!
                $datepicker.pikaday('show').pikaday('currentMonth');
                break;
        }
    },

    submit: function(id) {
        $onParentFormSubmit(id);
    },

    open: function(mode) {
        if (this.base.opened)
            return;

        this.mode = mode;

        switch (this.mode) {
            case 'selectdate':
                this.command = 'refresh';
                this.id = 'selectdate';
                break;
        }

        this.setDefaultSize();
    },

    sort: function(ob) {
        $("#command").val('sort');
        this.submit('decrees-form');
    },

    verified: function() {
        this.confirmed();
    },

    confirmed: function() {
        this.base.close();

        switch (this.mode) {
            case 'selectdate':
                var x = $("#selectdate").val().split('.');
                if (!is_empty(x)) {
                    var search = window.location.search;
                    var date = x[2]+right('00'+x[1], 2)+right('00'+x[0], 2);
                    if (date && date.length == 8) {
                        search = makeLocation(search, 'date_from', date);
                        search = makeLocation(search, 'state', this.get_state());
                        window.location.replace(search);
                    }
                }
                return;
        }

        this.submit();
    },

    refresh: function(ob) {
        var oid = ob.attr('id');
        var value = ob.val();

        if (this.IsTrace)
            alert('$DecreeSubmitDialog.refresh, oid:'+oid+', value:'+value);

        this.command = '';

        switch (oid) {
            case 'executors':
                this.command = app_role_ceo ? 'login' : 'executor';
                if (is_empty(value))
                    value = 'any';
                break;
            case 'statuses':
                this.command = 'status';
                if (value === '')
                    value = -1;
                break;
        }

        if (is_empty(this.command))
            return;

        var search = window.location.search;
        search = makeLocation(search, this.command, value);
        search = makeLocation(search, 'state', this.get_state());
        window.location.replace(search);
    },

    reset: function() {
        var search = '';
        if (app_role_ceo === 0)
            search = makeLocation('', 'with_login', 1);
        search = makeLocation(search, 'state', this.get_state());
        window.location.replace(search);
    },

    cancel: function() {
        this.base.close();
    }
};

var $DecreeActionDialog = {
    base         : $BaseDialog,

    container    : null,
    box          : null,
    ob           : null,
    line         : null,

    // ==========================
    // Decree Submit Dialog Class
    // ==========================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    action       : '',
    command      : null,
    id           : null,
    mode         : null,
    data         : null,
    params       : null,
    columns      : null,
    oid          : null,
    column       : null,
    line_index   : null,
    order_id     : null,
    review_id    : null,
    decree_id    : null,
    report_id    : null,

    is_show_loader : 0,

    buttons : ['validate','accept','finish','reject','remove'],

    button_accept : null,
    button_finish : null,
    button_reject : null,
    button_save   : null,

    is_error : false,

    init: function() {
        this.container = $("#line-content");
        this.oid = null;

        this.is_show_loader = IsShowLoader;
    },

    term: function() {
        this.container = null;
        this.box = null;
        this.ob = null;
        this.line = null;
        this.action = '';
        this.command = null;
        this.id = null;
        this.mode = null;
        this.data = null;
        this.params = null;
        this.columns = null;
        this.oid = null;
        this.column = null;
        this.line_index = null;
        this.order_id = null;
        this.review_id = null;
        this.decree_id = null;
        this.report_id = null;

        should_be_updated = false;
        selected_menu_action = '';

        is_input_focused = false;

        this.button_finish = null;
        this.button_reject = null;
        this.button_save = null;

        this.is_error = false;

        this.base.onClose();
    },

    state_buttons: function(state) {
        var oid = this.oid;
        this.buttons.forEach(function(name, index) {
            var box = 'buttons:'+oid;
            $("button", "#"+box).each(function() {
                $(this).button(state);
            });
        });
    },

    get_params: function(command) {
        var x = command.split(':');
        if (x.length < 4)
            return;

        this.mode = x[1];
        this.oid = x[2];
        this.column = x[3];
        this.line_index = x[4];

        var ids = x[2].split('_');
        if (ids.length < 5)
            return;

        loader_page = '/'+ids[0];

        this.order_id = int(ids[1]);
        this.review_id = int(ids[2]);
        this.decree_id = int(ids[3]);
        this.report_id = int(ids[4]);
    },

    set_params: function(is_author, is_executor) {
        this.params = {
            'command':this.command, 
            'decree_author' : $("#"+this.oid+"_"+"decree_author").val(), 
            'decree_executor' : $("#"+this.oid+"_"+"decree_executor").val(), 
            'is_author' : is_author,
            'is_executor' : is_executor,
            'order_id': this.order_id,
            'review_id': this.review_id,
            'decree_id': this.decree_id,
            'report_id': this.report_id
        };

        var line_id = 'row-line:'+this.oid+':'+this.line_index;
        this.line = $("tr[id^='"+line_id+"']", this.container);

        if (this.IsDebug)
            alert(line_id+', exist:'+is_exist(this.line));

        if (!is_exist(this.line))
            return;

        this.params['decree_duedate'] = $("td[class~='DueDate']", this.line).html();
        this.params['decree_title'] = $("td[class~='Article']", this.line).html();

        if (is_author)
            this.params['decree_note'] = this.ob.val();
        else if (is_executor) {
            this.params['decree_note'] = $("#item_"+this.oid+'_note', this.container).html();
            this.params['decree_report'] = this.ob.val();
        }

        if (this.IsDebug)
            alert(reprObject(this.params));
    },

    keypress: function(ob) {
        var id = ob.attr('id');

        this.button_save = $("button[id*='save']", ob.parent());

        if (is_exist(this.button_save))
            this.button_save.prop("disabled", false);
    },

    check: function(errors) {
        this.is_error = false;

        if (!is_null(errors) && errors.length > 0) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
            this.is_error = true;
        }

        if (is_exist(this.button_save))
            this.button_save.prop("disabled", true);
    },

    handle: function(response) {
        if (this.IsLog)
            console.log('$DecreeActionDialog.handle, mode:'+this.mode, this.id, this.action, response);

        var data = getObjectValueByKey(response, 'data', null);
        var props = getObjectValueByKey(response, 'props', null);
        var errors = getObjectValueByKey(response, 'errors', null);

        this.check(errors);

        if (is_null(data) || this.is_error)
            return;

        function clean_class(ob) {
            ['work','finished','rejected','overdue'].forEach(function(x, index) {
                ob.removeClass(x);
            });
        }

        switch (this.mode) {
            case 'finish':
            case 'reject':
                if (is_exist(this.button_finish))
                    this.button_finish.prop("disabled", true);
                if (is_exist(this.button_reject))
                    this.button_reject.prop("disabled", true);

                var ob = $("td[class~='np']", this.line);
                if (is_exist(ob)) {
                    var status = getattr(props, 'status', '');
                    clean_class(ob);
                    ob.addClass(status[1][0]);
                    ob.html(status[0]);
                }
                break;
            case 'accept':
                if (is_exist(this.button_accept))
                    this.button_accept.prop("disabled", true);

                var ob = $("#item_"+this.oid+"_decree_status", this.container);
                if (is_exist(ob)) {
                    var decree_status = getattr(props, 'decree_status', '');
                    ob.html(decree_status);
                }
                break;
            case 'save':
                break;
        }

        this.term();

        IsShowLoader = this.is_show_loader;
    },

    run: function(mode, ob) {
        if (mode == 0) {
            var command = ob.attr('id');
            var parent = ob.parent();

            if (this.IsLog)
                console.log('$DecreeActionDialog.run, oid:'+command);

            this.button_accept = $("button[class*='accept']", parent);
            this.button_finish = $("button[class*='finish']", parent);
            this.button_reject = $("button[class*='reject']", parent);

            if (this.IsDebug)
                alert(this.button_finish.attr('id'));

            this.get_params(command);

            if (['finish','reject'].indexOf(this.mode) > -1) {
                confirm_action = 'decree:'+this.mode;

                $ConfirmDialog.open(
                    keywords['Command:Decree '+this.mode] +
                    '', 
                    600);

                return;
            }
        }

        var is_author = $("#"+this.oid+"_is_author", this.container).val();
        var is_executor = $("#"+this.oid+"_is_executor", this.container).val();
        var oid = "item_"+this.oid+(is_author ? "_note" :(is_executor ? "_report" : ''));

        this.ob = $("#"+oid, this.container);

        if (this.IsDebug)
            alert(oid+', exist:'+is_exist(this.ob)+', '+is_author+', '+is_executor);

        if (!is_exist(this.ob))
            return;

        this.command = this.mode.toUpperCase()+'_DECREE';
        this.action = '875';

        this.set_params(is_author, is_executor);

        this.state_buttons('disable');

        IsShowLoader = 1;

        should_be_updated = true;
        selected_menu_action = this.action;
        $InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $DecreeActionDialog.handle(x); }, this.params);
    },

    cancel: function() {
        this.base.close();
    }
};

// =======
// Dialogs
// =======

jQuery(function($) 
{
    // ---------------------------------
    // Select Payment Review Date Dialog
    // ---------------------------------

    $("#selectdate-confirm-container").dialog({
        autoOpen: false,
        width:400,
        height:480,
        position:0,
        buttons: [
            {text: keywords['Open'],   click: function() { $DecreeSubmitDialog.confirmed(); }},
            {text: keywords['Cancel'], click: function() { $DecreeSubmitDialog.cancel(); }}
        ],
        modal: true,
        draggable: true,
        resizable: false,
        position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        close: function() {
            $BaseDialog.onClose();
        }
    });

    // --------------------------
    // Decree Email Message Dialog
    // --------------------------

    $("#decree-confirm-container").dialog({
        autoOpen: false,
        width:760,
        height:672,
        position:0,
        buttons: [],
        modal: false,
        draggable: true,
        resizable: true,
        //position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        open: function() {
            $DecreeSelectorDialog.onOpen();
        },
        close: function() {
            $DecreeSelectorDialog.onClose();
            $BaseDialog.onClose();
        }
    });
});
