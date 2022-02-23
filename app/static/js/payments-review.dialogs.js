// **********************************************
// PROVISION DIALOGS: /payments-review.dialogs.js
// ----------------------------------------------
// Version: 1.0
// Date: 27-07-2020

// ===========================
// Dialog windows declarations
// ===========================

var $PaymentReviewSelectorDialog = {
    base         : $BaseScreenDialog,

    // =============================
    // Provision Order History Class
    // =============================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    action       : '',
    command      : null,
    id           : null,
    params       : null,

    pointer      : null,
    box          : null,
    changes      : null,

    // Mode of screen available
    mode         : 'available',
    // Flag to use cache
    with_cache   : 0,
    // Flag to lock screen
    with_lock    : 0,
    // Refresh page on way submit or loader action
    with_submit  : 0,

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

    confirmation: function(mode) {
        if (this.IsTrace)
            alert('$PaymentReviewSelectorDialog.confirmation, mode:'+mode);

        var msg = keywords['Do you realy wish to '+mode+' selected payments']+'?';

        confirm_action = mode;

        var width = msg.length*9;
        var height = 180;

        $ConfirmDialog.open(msg, width, 0, keywords['Payments Review confirmation']);
    },

    forward: function() {
        window.location.replace(forward);
    },

    back: function() {
        window.location.replace(back);
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
        var self = $PaymentReviewSelectorDialog;

        if (this.IsTrace)
            alert('$PaymentReviewSelectorDialog.expand');

        var obs = $("td[class*='showbar']", "#line-content");

        //alert(obs.length);

        obs.each(function() {
            self.showbar($(this), 0);
        });

        $("button[id='payments:expand']", "#caption").removeClass('btn-primary').addClass('btn-warning');
        $("button[id='payments:collapse']", "#caption").removeClass('btn-warning').addClass('btn-primary');
    },

    collapse: function() {
        var self = $PaymentReviewSelectorDialog;

        if (this.IsTrace)
            alert('$PaymentReviewSelectorDialog.collapse');

        var obs = $("td[class*='showbar']", "#line-content");

        //alert(obs.length);

        obs.each(function() {
            self.showbar($(this), 1);
        });

        $("button[id='payments:expand']", "#caption").removeClass('btn-warning').addClass('btn-primary');
        $("button[id='payments:collapse']", "#caption").removeClass('btn-primary').addClass('btn-warning');
    },

    open: function(ob, mode) {
        if (this.IsTrace)
            alert('$PaymentReviewSelectorDialog.open, mode:'+mode);

        this.init(ob, 'payments');

        var header = $("#payments-header", this.base.container);

        switch (mode) {
            case 'update':
                break;
            case 'read':
                break;
            default:
                return;
        }

        var cacheid = this.base.cacheid;
        var html = this.base.box.html().replace('payments-form', cacheid); 

        this.base.load(html);

        $("#command", this.base.form).val(mode);

        this.setDefaultSize();
    },

    _get_changes: function(ob) {
        this.pointer = ob;

        //this.init(ob, 'payments');

        this.box = $("#payments-changes-container");

        var id = $_get_item_id(this.pointer.parent());

        this.command = 'PAYMENTS_REVIEW_CHANGES';
        this.action = '873';
        this.params = {'command':this.command, 'id':id, 'date':selected_date};

        //this.base.progress();

        $Handle(this.action, function(x) { $PaymentReviewSelectorDialog.handle(x); }, this.params);
    },

    showChanges: function() {
        if (is_empty(this.changes))
            return;

        var position = this.pointer.position();
        var top = position.top + this.pointer.height() + 40;
        var left = position.left - 400;
        var content = '';

        content += '<div class="changes"><table border="0">';

        this.changes.forEach(function(x, index) {
            content += 
                '<tr>'+
                    '<td class="id">'+x['TID']+'</td>'+
                    '<td class="id">'+x['PaymentID']+'</td>'+
                    '<td class="date">'+x['RD']+'</td>'+
                    '<td class="login">'+x['Login']+'</td>'+
                    '<td class="status">'+x['StatusName']+'</td>'+
                '</tr>';
        });

        content += '</table></div>';

        this.box.html(content).css({ top:top, left:left, width:"auto" }).show();
    },

    hideChanges: function() {
        this.box.hide();
        this.changes = null;
    },

    refresh: function(ob) {
        if (this.with_submit) {
            $("#command").val(confirm_action);
            $onParentFormSubmit('payments-form');
        } else {
            this.validate(ob);
        }
    },

    print: function(ob) {
        confirm_action = 'print';

        this.validate(ob); // $("#page-section")
    },

    _get_selected_payments: function() {
        var ids = new Array();
        var checks = $("input[type='checkbox']", "#line-content");

        checks.each(function() { if ($(this).prop("checked")) ids.push($(this).attr('value')); });

        if (this.IsTrace)
            alert(joinToPrint(ids));

        return ids;
    },

    _set_selected_payments: function(data) {
        var review_classes = ['accept', 'reject'];
        var checks = $("input[type='checkbox']", "#line-content");

        function clean_class(ob) {
            review_classes.forEach(function(x, index) {
                ob.removeClass(x);
            });
        }

        //alert(selected_columns);

        var columns = selected_columns.split(':');

        //console.log('data:', data, 'columns:', columns);

        checks.each(function(index) { 
            var ob = $(this);
            var check_id = ob.attr('value');
            var parent_id = check_id+':'+(index+1);
            var parent = $("tr[id='row-line:"+parent_id+"']");

            //console.log('check_id:', check_id);

            if (is_exist(parent)) {
                if (check_id in data) {
                    columns.forEach(function(column) { 
                        var item = $("td[class~='"+column+"']", parent);

                        //console.log('$PaymentReviewSelectorDialog._set_selected_payments', parent_id, parent, item, column);

                        if (is_exist(item)) {
                            var prop = data[check_id];
                            clean_class(item);
                            item.attr('title', prop['title'][column]).addClass(prop['class']);
                        }
                    });
                }
                else {
                    parent.remove();

                    var info = $("div[id='info:"+parent_id+"']");
                    if (is_exist(info))
                        info.remove();
                }
            }
        });

        if ('sum_price' in data)
            $(".sum_price").each(function() { $(this).html(data['sum_price']); });
    },

    handle: function(x) {
        var self = $PaymentReviewSelectorDialog;

        if (self.IsTrace)
            alert('$PaymentReviewSelectorDialog.handle');

        var errors = !is_null(x) ? x['errors'] : null;
        var data = !is_null(x) ? x['data'] : [];
        var total = !is_null(x) ? x['total'] : 0;
        var props = !is_null(x) ? x['props'] : {};
        var with_notification = false;

        if (self.IsDebug)
            alert(reprObject(data));

        switch (this.command) {
            case 'PAYMENTS_REVIEW_ACCEPT':
                self._set_selected_payments(data);
                with_notification = true;
                break;
            case 'PAYMENTS_REVIEW_REJECT':
                self._set_selected_payments(data);
                with_notification = true;
                break;
            case 'PAYMENTS_REVIEW_CHANGES':
                self.changes = data;
                return;
            case 'PAYMENTS_REVIEW_PRINT':
                printProvisionPayments(data, props);
                return;
        }

        if (with_notification) {
            if (errors.length > 0) {
                var msg = errors.join('<br>');
                $ShowError(msg, true, true, false);
            }
            else if ('OK' in props)
                $NotificationDialog.open(props['OK']);
            else {
                $NotificationDialog.open(
                    '<p>'+keywords['Message:Action was done successfully']+'</p>'+
                    '<div class="done">'+keywords['Total']+': '+total+'</div>'
                );
            }
        }

        self.term();
    },

    validate: function(ob) {
        if (this.IsTrace)
            alert('$PaymentReviewSelectorDialog.validate');

        this.init(ob, 'payments');

        var checks = this._get_selected_payments();

        switch (confirm_action) {
            case 'accept':
                this.command = 'PAYMENTS_REVIEW_ACCEPT';
                this.action = '871';
                this.params = {'command':this.command, 'checks':checks, 'date':selected_date};
                break;
            case 'reject':
                this.command = 'PAYMENTS_REVIEW_REJECT';
                this.action = '872';
                this.params = {'command':this.command, 'checks':checks, 'date':selected_date};
                break;
            case 'print':
                this.command = 'PAYMENTS_REVIEW_PRINT';
                this.action = '874';
                this.params = {'command':this.command, 'checks':checks, 'date':selected_date};
                break;
        }

        selected_menu_action = this.action;

        this.base.progress();

        $Handle(this.action, function(x) { $PaymentReviewSelectorDialog.handle(x); }, this.params);
    },

    onOpen: function() {
        var self = $PaymentReviewSelectorDialog;

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

var $PaymentReviewSubmitDialog = {
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
        this.submit('payments-form');
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
                    var date = x[2]+right('00'+x[1], 2)+right('00'+x[0], 2);
                    if (date && date.length == 8)
                        window.location.replace(date);
                }
                return;
        }

        this.submit();
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
    // ---------------------
    // Payment Review Dialog
    // ---------------------

    $("#payments-confirm-container").dialog({
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
            $PaymentReviewSelectorDialog.onOpen();
        },
        close: function() {
            $PaymentReviewSelectorDialog.onClose();
            $BaseDialog.onClose();
        }
    });

    // ---------------------------------
    // Select Payment Review Date Dialog
    // ---------------------------------

    $("#selectdate-confirm-container").dialog({
        autoOpen: false,
        width:400,
        height:480,
        position:0,
        buttons: [
            {text: keywords['Open'],   click: function() { $PaymentReviewSubmitDialog.confirmed(); }},
            {text: keywords['Cancel'], click: function() { $PaymentReviewSubmitDialog.cancel(); }}
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
});
