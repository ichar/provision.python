// ************************************
// PROVISION DIALOGS: /stock.dialogs.js
// ------------------------------------
// Version: 1.0
// Date: 04-12-2019

// ===========================
// Dialog windows declarations
// ===========================

var $StockSelectorDialog = {
    base         : $BaseScreenDialog,

    // =============================
    // Provision Order History Class
    // =============================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    action       : '',
    command      : null,
    id           : null,
    params       : null,

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
        var state = !is_null(force) ? force : (ob.hasClass('expanded') ? 1 : 0);
        var info = $("div[id='info:"+row_id+"']", "#line-content");

        //alert(id+'='+row_id+'='+state);

        if (is_exist(info)) {
            info.removeClass('invisible');
            if (state == 1) {
                info.hide();
                ob.removeClass('expanded').addClass('collapsed');
            } else {
                info.show();
                ob.removeClass('collapsed').addClass('expanded');
            }
        }
    },

    expand: function() {
        var self = $StockSelectorDialog;

        if (this.IsTrace)
            alert('$StockSelectorDialog.expand');

        var obs = $("td[class*='showbar']", "#line-content");

        //alert(obs.length);

        obs.each(function() {
            self.showbar($(this), 0);
        });

        $("button[id='stock:expand']", "#caption").removeClass('btn-primary').addClass('btn-warning');
        $("button[id='stock:collapse']", "#caption").removeClass('btn-warning').addClass('btn-primary');
    },

    collapse: function() {
        var self = $StockSelectorDialog;

        if (this.IsTrace)
            alert('$StockSelectorDialog.collapse');

        var obs = $("td[class*='showbar']", "#line-content");

        //alert(obs.length);

        obs.each(function() {
            self.showbar($(this), 1);
        });

        $("button[id='stock:expand']", "#caption").removeClass('btn-warning').addClass('btn-primary');
        $("button[id='stock:collapse']", "#caption").removeClass('btn-primary').addClass('btn-warning');
    },

    open: function(ob, mode) {
        if (this.IsTrace)
            alert('$StockSelectorDialog.open, mode:'+mode);

        this.init(ob, 'stock');

        var header = $("#stock-header", this.base.container);

        switch (mode) {
            case 'update':
                header.html(keywords['Input form items to edit Stock attributes']);
                this.base.container.dialog("option", "buttons", [
                    {text: keywords['Save'], click: function() { $StockSelectorDialog.confirmed(); }},
                    {text: keywords['Cancel'], click: function() { $StockSelectorDialog.cancel(); }}
                ]);
                break;
            case 'read':
                header.html(keywords['Check form items to apply Stock attributes']);
                this.base.container.dialog("option", "buttons", [
                    {text: keywords['OK'], click: function() { $StockSelectorDialog.cancel(); }}
                ]);
                break;
            default:
                return;
        }

        var cacheid = this.base.cacheid;
        var html = this.base.box.html().replace('stock-form', cacheid); 

        this.base.load(html);

        $("#command", this.base.form).val(mode);

        this.setDefaultSize();
    },

    print: function(ob) {
        confirm_action = 'print';

        this.validate(ob);
    },

    handle: function(x) {
        var self = $StockSelectorDialog;

        if (self.IsTrace)
            alert('$StockSelectorDialog.handle');

        var errors = !is_null(x) ? x['errors'] : null;
        var data = !is_null(x) ? x['data'] : [];
        var total = !is_null(x) ? x['total'] : 0;
        var props = !is_null(x) ? x['props'] : {};

        if (self.IsDebug)
            alert(reprObject(data));

        switch (this.command) {
            case 'STOCK_ORDERS_PRINT':
                printStockOrders(data, props);
                return;
        }

        self.term();
    },

    validate: function() {
        switch (confirm_action) {
            case 'print':
                this.command = 'STOCK_ORDERS_PRINT';
                this.action = '874';
                this.params = {'command':this.command, 'uid':uid, 'seller':seller};
                break;
        }

        selected_menu_action = this.action;

        this.base.progress();

        $Handle(this.action, function(x) { $StockSelectorDialog.handle(x); }, this.params);
    },

    onOpen: function() {
        var self = $StockSelectorDialog;

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

var $StockSubmitDialog = {
    base         : $BaseDialog,

    // =========================
    // Stock Submit Dialog Class
    // =========================

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

    submit: function(id) {
        $onParentFormSubmit(id);
    },

    sort: function(ob) {
        $("#command").val('sort');
        this.submit('stock-orders-form');
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
    // --------------------------
    // Stock Email Message Dialog
    // --------------------------

    $("#stock-confirm-container").dialog({
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
            $StockSelectorDialog.onOpen();
        },
        close: function() {
            $StockSelectorDialog.onClose();
            $BaseDialog.onClose();
        }
    });
});
