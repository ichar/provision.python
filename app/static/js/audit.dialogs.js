// *************************************
// PROVISION DIALOGS: /audit.dialogs.js
// -------------------------------------
// Version: 1.0
// Date: 05-03-2020

// ===========================
// Dialog windows declarations
// ===========================

var $AuditSelectorDialog = {
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
    content_state : 0,

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

    go: function(href) {
        if (is_empty(href))
            href = window.location.href;

        if (this.IsTrace)
            alert('$AuditSelectorDialog.go:'+href);

        var uri = href.split('?');
        var base = uri[0];
        var query_string = uri.length > 1 ? uri[1] : '';
        var params = JSON.parse('{"' + decodeURI(query_string.replace(/&/g, '","').replace(/=/g,'":"')) + '"}');
        var state = Object.assign({}, params);

        params.state = this.content_state == 1 ? 'collapse' : 'expand';
        params.created_after = $("#created_after").val();

        var url = base + '?' + Object.keys(params).map(function(key) { return key+'='+params[key]; }).join('&');

        if (this.IsLog)
            console.log('$AuditSelectorDialog.go:', base, reprObject(params), url);

        $_change_location(state, url);
    },

    expand: function() {
        if (this.IsTrace)
            alert('$AuditSelectorDialog.expand');

        if (this.content_state == 0)
            return;

        var collapsed = $("div[class^='collapsed']", "#line-content");
        collapsed.each(function() { if ($(this).addClass('invisible')); });

        var expanded = $("div[class^='expanded']", "#line-content");
        expanded.each(function() { if ($(this).removeClass('invisible')); });

        $("button[id='audit:expand']", "#caption").removeClass('btn-primary').addClass('btn-warning');
        $("button[id='audit:collapse']", "#caption").removeClass('btn-warning').addClass('btn-primary');

        this.content_state = 0;
    },

    collapse: function() {
        if (this.IsTrace)
            alert('$AuditSelectorDialog.collapse');

        if (this.content_state == 1)
            return;

        var expanded = $("div[class^='expanded']", "#line-content");
        expanded.each(function() { if ($(this).addClass('invisible')); });

        var collapsed = $("div[class^='collapsed']", "#line-content");
        collapsed.each(function() { if ($(this).removeClass('invisible')); });

        $("button[id='audit:expand']", "#caption").removeClass('btn-warning').addClass('btn-primary');
        $("button[id='audit:collapse']", "#caption").removeClass('btn-primary').addClass('btn-warning');

        this.content_state = 1;
    },

    open: function(ob, mode) {
        if (this.IsTrace)
            alert('$AuditSelectorDialog.open, mode:'+mode);

        this.init(ob, 'audit');

        var header = $("#audit-header", this.base.container);

        switch (mode) {
            case 'update':
                header.html(keywords['Input form items to edit Audit attributes']);
                this.base.container.dialog("option", "buttons", [
                    {text: keywords['Save'], click: function() { $AuditSelectorDialog.confirmed(); }},
                    {text: keywords['Cancel'], click: function() { $AuditSelectorDialog.cancel(); }}
                ]);
                break;
            case 'read':
                header.html(keywords['Check form items to apply Audit attributes']);
                this.base.container.dialog("option", "buttons", [
                    {text: keywords['OK'], click: function() { $AuditSelectorDialog.cancel(); }}
                ]);
                break;
            default:
                return;
        }

        var cacheid = this.base.cacheid;
        var html = this.base.box.html().replace('audit-form', cacheid); 

        this.base.load(html);

        $("#command", this.base.form).val(mode);

        this.setDefaultSize();
    },

    handle: function(x) {
        var self = $AuditSelectorDialog;

        $BaseDialog.close();

        var errors = !is_null(x) ? x['errors'] : null;

        switch (self.id) {
            case 'update':
                break;
        }

        self.term();
    },

    validate: function() {
        switch (this.id) {
            case 'update':
                break
        }

        selected_menu_action = this.action;

        this.base.progress();

        $Handle(this.action, function(x) { $AuditSelectorDialog.handle(x); }, this.params);
    },

    onOpen: function() {
        var self = $AuditSelectorDialog;

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

// =======
// Dialogs
// =======

jQuery(function($) 
{
    // --------------------------
    // Audit Email Message Dialog
    // --------------------------

    $("#audit-confirm-container").dialog({
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
            $AuditSelectorDialog.onOpen();
        },
        close: function() {
            $AuditSelectorDialog.onClose();
            $BaseDialog.onClose();
        }
    });
});
