// **************************************
// PROVISION DIALOGS: /barcode.dialogs.js
// --------------------------------------
// Version: 1.0
// Date: 02-09-2021

// ===========================
// Dialog windows declarations
// ===========================

var $BarcodeSelectorDialog = {
    base         : $BaseScreenDialog,

    // ================================
    // Provision Barcode Selector Class
    // ================================

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
        var self = $BarcodeSelectorDialog;

        if (this.IsTrace)
            alert('$BarcodeSelectorDialog.expand');

        var obs = $("td[class*='showbar']", "#line-content");

        //alert(obs.length);

        obs.each(function() {
            self.showbar($(this), 0);
        });

        $("button[id='barcode:expand']", "#caption").removeClass('btn-primary').addClass('btn-warning');
        $("button[id='barcode:collapse']", "#caption").removeClass('btn-warning').addClass('btn-primary');
    },

    collapse: function() {
        var self = $BarcodeSelectorDialog;

        if (this.IsTrace)
            alert('$BarcodeSelectorDialog.collapse');

        var obs = $("td[class*='showbar']", "#line-content");

        //alert(obs.length);

        obs.each(function() {
            self.showbar($(this), 1);
        });

        $("button[id='barcode:expand']", "#caption").removeClass('btn-warning').addClass('btn-primary');
        $("button[id='barcode:collapse']", "#caption").removeClass('btn-primary').addClass('btn-warning');
    },

    open: function(ob, mode) {
    },

    print: function(ob) {
    },

    handle: function(x) {
    },

    validate: function(ob) {
    },

    onOpen: function() {
        var self = $BarcodeSelectorDialog;

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

var $BarcodeSubmitDialog = {
    base         : $BaseDialog,

    // ===========================
    // Barcode Submit Dialog Class
    // ===========================

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
        this.submit('barcode-orders-form');
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
    // --------------
    // Barcode Dialog
    // --------------
});
