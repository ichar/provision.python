// ********************************
// HELPER FUNCTION CONTROLS MANAGER
// --------------------------------
// Version: 1.0
// Date: 14-07-2019

// =======================
// Component control class
// =======================

var $PageScroller = {
    page      : { 'base':null, 'top':0, 'height':0 },
    control   : { 'ob':null, 'default_position':0, 'top':0, 'height':0, 'isDefault':0, 'isMoved':0, 'isShouldBeMoved':0 },
    position  : 0,
    is_trace  : 0,

    init: function() {
    },

    reset: function(force) {
    },

    trace: function(force) {
    },

    checkPosition: function(reset) {
    },

    move: function() {
    }
};

// Current review container ID
var selected_review_id = 'subline_review';
// Size for scroll after activate
var window_scroll = 0;
// Page scroll mode by default
var default_scroll_mode = 'on-place';

var $PageLoader = {
    container   : null,
    actions     : {'param':'830-1','item':'830-2','payment':'830-3','refer':'830-6','comment':'830-4','document':'830-5'},

    IsDebug : 0, IsDeepDebug : 0, IsTrace : 0, IsLog : 0,

    action      : null,
    id          : null,
    command     : '',
    mode        : '',
    box         : null,
    
    scroll_mode : '',
    scroll_top  : 0,
    top         : 0,
    height      : 0,

    is_error    : false,
    is_shown    : false,
    is_locked   : false,

    line        : {'id' : null, 'state_is_open' : -1},

    init: function() {
        this.container = $("#"+selected_review_id);

        if (this.IsTrace)
            alert('init:'+$LineSelector.get_id()+':'+$LineSelector.get_current().get(0).outerHTML);

        this.line['id'] = null;

        this.scroll_top = $(window).scrollTop();
    },

    reset: function() {
        this._show();
        this._reset();

        this.scroll_top = $(window).scrollTop();
    },

    scroll: function() {
        if (window_scroll != null) {
            $(window).scrollTop(window_scroll || 0);

            window_scroll = null;

            $_show_page(0);
            return;
        }

        var current_top = $LineSelector.get_current().position().top;

        if (this.IsDebug)
            alert(['scroll', this.scroll_mode, this.line['state_is_open'], this.scroll_top, this.height, int(this.top), int(current_top)].join(':'));

        if (this.top == 0 || this.height == 0 || this.top > current_top)
            return;

        var offset = 5;

        switch (this.scroll_mode) {
            case 'top':
                $(window).scrollTop(current_top - offset);
                break;
            case 'on-place':
                if (this.line['state_is_open'] != 0) {
                    var x = this.scroll_top - this.height - offset;
                    if (x > 0)
                        $(window).scrollTop(x);
                }
                break;
            default:
                break;
        }

        this.scroll_mode = '';
    },

    remove_current: function() {
        if (!is_null(this.container)) {
            try {
                this.top = this.container.position().top;
                this.height = this.container.height();
            } 
            catch(e) {
                if (this.IsTrace) 
                    alert('$PageLoader.remove_current: Error');
                this.height = 0;
            }
            this.container.remove();
        }
    },

    update_tab: function(mode, data) {
        if (is_null(data)) {
            $onInfoContainerChanged('refresh');
            return;
        }

        $updateTabData(mode, data['data'], data['config'], data['total'], data['status'], null);
    },

    update_tab_count: function(info) {
        var menu = info['menu'];

        if (this.IsDebug)
            alert(joinToPrint([selected_review_id, reprObject(menu)]));

        var line = $("#"+selected_review_id);

        if (!is_empty(menu)) {
            $("div[class^='menu']", line).each(function(index) { 
                var key = $(this).attr('id').split('-').slice(-1)[0];
                var count = getObjectValueByKey(menu, key);
                if (count > 0) {
                    $(this).addClass('data_menu_count');
                    $(this).attr('count', count);
                }
                else if (count == 0) {
                    $(this).removeClass('data_menu_count');
                    $(this).attr('count', '');
                }
            });
        }
    },

    _lock: function() {
        this.is_locked = true;
    },

    _unlock: function() {
        this.is_locked = false;
    },

    locked: function() {
        return this.is_locked;
    },

    _before: function(ob, command) {
        should_be_updated = false;
        selected_menu_action = default_log_action;

        this.box = ob;
        this.command = command;

        if (!is_null(this.command)) {
            if (this.command.toLowerCase().search('add') > -1)
                this.id = null;
            else
                this.id = $TablineSelector.get_id();
        }

        $InProgress(ob, 1);

        this.is_error = false;
    },

    _reset: function() {
        this.action = null;
        this.id = null;
        this.mode = null;
        this.box = null;
    },

    _hide: function() {
        if (is_empty(this.mode))
            return;

        var key = this.mode.toUpperCase();

        $("#ADD_"+key).hide();
        $("#EDIT_"+key).hide();
        $("#DEL_"+key).hide();
        $("#SAVE_"+key).show();
        $("#CANCEL_"+key).show();

        this.is_shown = true;
    },

    _show: function() {
        if (is_empty(this.mode))
            return;

        var key = this.mode.toUpperCase();

        $("#ADD_"+key).show();
        $("#EDIT_"+key).show();
        $("#DEL_"+key).show();
        $("#SAVE_"+key).hide();
        $("#CANCEL_"+key).hide();

        this.is_shown = false;
    },

    _clean: function() {
        switch (this.mode) {
            case 'param':
                $("#param").val('0');
                $("#new_param").val('');
                $("#param_value").val('');
                $("#new_param_value_combo").val('');

                check_param(null, 1);
                break;
            case 'item':
                $("#item_name").val('');
                //setprop($("#item_vendor"), "selectedIndex", 0);
                setvalue($("#item_vendor"), 0);
                setvalue($("#new_item_vendor"), '');
                $("#item_qty").val(0);
                $("#item_units").val('');
                $("#item_total").val('');
                $("#item_currency").val('');
                $("#item_account").val('');
                break;
            case 'payment':
                $("#payment").val('0');
                $("#new_payment").val('');
                $("#payment_date").val('');
                $("#payment_total").val('');
                $("#payment_currency").val('');
                $("#payment_rate").val('');
                $("#payment_exchange_rate").val('');
                $("#payment_status").val('0');
                //$("#payment_status").prop("selectedIndex", 1);
                $("#payment_comment").val('');
                break;
            case 'refer':
                $("#refer").val('0');
                $("#new_refer").val('');
                $("#refer_value").val('');
                $("#refer_note").val('');

                check_refer(null, 1);
                break;
            case 'comment':
                $("#comment").val('0');
                $("#new_comment").val('');
                $("#comment_value").val('');
                break;
            case 'document':
                $("#document_filename").val('');
                $("#document_value").val('');
                $("#document_for_audit").prop('checked', 1);
                break;
        }
    },

    set: function(x) {
        var data = x['data']['data'][0];

        if (this.IsLog)
            console.log('$PageLoader.set, mode:', this.mode, data, x);

        switch (this.mode) {
            case 'param':
                $("#param").val(data['ParamID']);
                $("#new_param").val('');
                //$("#param_value").val(data['Value']);

                check_param(data['Value'], 0);
                break;
            case 'item':
                $("#item_name").val(data['Name']);
                //setprop($("#item_vendor"), "selectedIndex", data['VendorID']);
                setvalue($("#item_vendor"), data['VendorID']);
                setvalue($("#new_item_vendor"), '');
                $("#item_qty").val(data['Qty']);
                $("#item_units").val(data['Units']);
                $("#item_total").val(data['Total']);
                $("#item_currency").val(data['Currency']);
                $("#item_account").val(data['Account']);
                break;
            case 'payment':
                $("#payment").val(data['PaymentID']);
                $("#new_payment").val('');
                $("#payment_date").val(data['PaymentDate']);
                $("#payment_total").val(data['Total']);
                $("#payment_currency").val(data['Currency']);
                $("#payment_rate").val(data['Rate']);
                $("#payment_exchange_rate").val(data['ExchangeRate']);
                $("#payment_status").val(data['StatusID']);
                $("#payment_comment").val(data['Comment']);
                break;
            case 'refer':
                $("#refer").val(data['ReferID']);
                $("#new_refer").val('');
                $("#refer_value").val(data['Value']);
                $("#refer_note").val(data['Note']);

                check_refer(null, 0);
                break;
            case 'comment':
                $("#comment").val(data['CommentID']);
                $("#new_comment").val('');
                $("#comment_value").val(data['Value']);
                break;
            case 'document':
                $("#document_filename").val(data['FileName']);
                $("#document_value").val(data['Note']);
                $("#document_for_audit").prop('checked', data['ForAudit'] ? 1 : 0);
                break;
        }

        this._hide();
        this._after();
    },

    get: function(action, ob, command) {
        this.action = action;
        this.mode = command.split('_')[1].toLowerCase();

        this._before(ob, command);

        var params = {'command':command, 'id':this.id};

        $Handle(this.action, function(x) { $PageLoader.set(x); }, params);
    },

    cancel: function(action, ob, command) {
        this._clean();
        this._show();
        this._after();
    },

    check: function(x) {
        var errors = x['errors'];

        if (this.IsLog)
            console.log('$PageLoader.check, errors:', errors.length);

        if (!is_null(errors) && errors.length > 0) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
            this.is_error = true;

            this._show();
        }
    },

    check_reference: function(x) {
        var reference = x['reference'];

        if (is_empty(reference))
            return;

        var key = reference[0];
        var id = reference[1];
        var value = reference[2];

        var obs = [$("select[id='__"+key+"']", $("#provision_container_template")), 
                   $("select[id='"+key+"']", $("#"+key+"s-items")),
                   $("select[id='"+this.mode+"_"+key+"']", $("#"+this.mode+"s-items")),
                   $("select[id='"+key+"']", $("#sidebar-filter-scroller"))];

        if (this.IsLog)
            console.log('$PageLoader.check_reference, reference:', name, reference, obs);

        obs.forEach(function(ob, index) {
            if (is_exist(ob)) {
                var options = ob.prop("options");
                var option = new Option(value, id, false, false);

                if (!is_null(options))
                    options[options.length] = option;
            }
        });
    },

    check_paid: function(info) {
        payment_total = getObjectValueByKey(info, 'payment_total') || '';

        var panel = $("#paid-panel");
        var value = $("#paid-panel-value");

        if (is_exist(panel)) {
            var paid = getObjectValueByKey(info, 'paid_total');

            //alert('check_paid:['+paid+']');

            if (!is_null(paid)) {
                value.html(paid || '0.0');
                panel.show();
            }
            else
                panel.hide();
        }
    },

    check_refers: function(info) {
        refers_info = getObjectValueByKey(info, 'refers_info');

        var panel = $("#refers-info");
        var title = $("#refers-info-title");
        var value = $("#refers-info-value");

        if (is_exist(panel)) {
            var total = getObjectValueByKey(refers_info, 'value');

            //alert('check_refers.total:['+total+']');

            if (!is_empty(total)) {
                title.html(getObjectValueByKey(refers_info, 'title'));
                value.html(total);
                panel.show();
            }
            else
                panel.hide();
        }
    },

    check_images: function(currentfile) {
        if (currentfile.length > 3)
            refresh_subline_images(currentfile[3]);
    },

    set_status: function(status) {
        if (this.IsTrace)
            alert('$PageLoader.set_status:'+status[0]);

        $("#status-info").removeClass().addClass(status[0]).html(status[1]);
    },

    set_barcode: function(props) {
        var barcode = props && getObjectValueByKey(props, 'barcode');
        var box = $("#barcode_box");
        var ob = $("#barcode");

        if (!is_empty(barcode) && is_exist(ob)) {
            ob.attr("src", barcode);
            box.show();
        }
        else
            box.hide();
    },

    update_param_combo: function(x) {
        this.check(x);

        if (!this.is_error) {
            var values = x['data'];
            var current_value = x['props'][0];
            var options = this.box.prop("options");

            if (!is_null(options)) {
                $('option', this.box).remove();

                values.forEach(function(value, index) {
                    var option = new Option(value, value, false, false);
                    options[options.length] = option;
                });
            }

            if (current_value)
                $("#param_value_combo").val(current_value);
        }

        //this._reset();
        this._after();
    },

    handle: function(x) {
        this.check(x);

        if (this.mode in this.actions) {
            if (!this.is_error) {
                this.update_tab(this.actions[this.mode], x['data']);
                this.check_reference(x['data']);
            }

            var currentfile = getObjectValueByKey(x, 'currentfile');

            if (!is_null(currentfile)) {
                var info = currentfile[1];

                this.update_tab_count(info);

                switch (this.mode) {
                    case 'payment':
                        this.check_paid(info);
                        break;
                    case 'refer':
                        this.check_refers(info);
                        break;
                    case 'document':
                        this.check_images(currentfile);
                        break;
                }
            }

            var props = getObjectValueByKey(x, 'props');

            if (this.mode == 'item')
                this.set_barcode(props);

            this._clean();
            this._show();
        
            if (this.command.toLowerCase().search('del') > -1)
                this.id = null;

            var menu = 'data-menu-'+this.mode+'s';

            $ShowMenu(menu);

            if (this.IsLog)
                console.log('$PageLoader.handle, command:', this.command, this.id);

            if (!is_null(this.id))
                $TablineSelector.set_current_by_id(this.id);
        } 
        else if (this.mode == 'set-status') {
            var status = x['data'];
            
            if (!this.is_error) {
                this.set_status(status[0]);

                var new_status = status[1][0];
                var title = status[1][1];
                var line = $LineSelector.get_current();
                var ob = $(".status", line);

                if (this.IsLog)
                    console.log('$PageLoader.handle, mode:', this.mode, status, new_status);

                order_statuses.forEach(function(name, index) { ob.removeClass(name); });
                ob.addClass(new_status);
                ob.attr('title', title);

                if (['autoclosed', 'audit', 'finish'].indexOf(new_status) > -1)
                    $ShowOnStartup();
            }
        }
        else if (this.mode == 'barcode') {
            var props = x['props'];

            if (!this.is_error)
                this.set_barcode(props);
        }

        this._reset();
        this._after();
    },

    handle_param: function(action, ob, command) {
        this.action = action;
        this.mode = 'param';

        this._before(ob, command);

        var param_id = $("#param").val();
        var new_param = $("#new_param").val();
        var value = param_value_mode == 1 ? $("#param_value").val() : ($("#new_param_value_combo").val() || $("#param_value_combo").val());
        var params = {'command':command, 'id':this.id, 'param_id':param_id, 'new_param':new_param, 'param_value_mode':param_value_mode, 'value':value};

        $Handle(this.action, function(x) { $PageLoader.handle(x); }, params);
    },

    handle_param_combo: function(action, ob, command) {
        this.action = action;
        this.mode = 'param';

        this._before(ob, command);

        var param_id = $("#param").val();
        var params = {'command':command, 'id':this.id, 'param_id':param_id};

        $Handle(this.action, function(x) { $PageLoader.update_param_combo(x); }, params);
    },

    handle_item: function(action, ob, command) {
        this.action = action;
        this.mode = 'item';

        this._before(ob, command);

        var name = $("#item_name").val();
        //var vendor = getprop($("#item_vendor"), "selectedIndex");
        var vendor = getvalue($("#item_vendor"));
        var new_vendor = getvalue($("#new_item_vendor"));
        var qty = $("#item_qty").val();
        var units = $("#item_units").val();
        var total = $("#item_total").val();
        var currency = $("#item_currency").val();
        var account = $("#item_account").val();
        var no_tax = $("#item_no_tax").prop('checked') ? 1 : 0;
        var params = {'command':command, 'id':this.id, 'name':name, 'vendor':vendor, 'new_vendor':new_vendor, 'qty':qty, 'units':units, 'total':total, 'no_tax':no_tax, 'currency':currency, 'account':account};

        $Handle(this.action, function(x) { $PageLoader.handle(x); }, params);
    },

    handle_payment: function(action, ob, command) {
        this.action = action;
        this.mode = 'payment';

        this._before(ob, command);

        var payment_id = $("#payment").val();
        var new_payment = $("#new_payment").val();
        var date = $("#payment_date").val();
        var total = $("#payment_total").val();
        var currency = $("#payment_currency").val();
        var rate = $("#payment_rate").val();
        var exchange_rate = $("#payment_exchange_rate").val();
        var status = $("#payment_status").val();
        var comment = $("#payment_comment").val();
        var params = {'command':command, 'id':this.id, 'payment_id':payment_id, 'new_payment':new_payment, 'date':date, 'total':total, 'currency':currency, 'rate':rate, 'exchange_rate':exchange_rate, 'status':status, 'comment':comment};

        $Handle(this.action, function(x) { $PageLoader.handle(x); }, params);
    },

    handle_refer: function(action, ob, command) {
        this.action = action;
        this.mode = 'refer';

        this._before(ob, command);

        var refer_id = $("#refer").val();
        var new_refer = $("#new_refer").val();
        var value = $("#refer_value").val();
        var note = $("#refer_note").val();
        var refers = {'command':command, 'id':this.id, 'refer_id':refer_id, 'new_refer':new_refer, 'value':value, 'note':note};

        $Handle(this.action, function(x) { $PageLoader.handle(x); }, refers);
    },

    handle_comment: function(action, ob, command) {
        this.action = action;
        this.mode = 'comment';

        this._before(ob, command);

        var comment_id = $("#comment").val();
        var new_comment = $("#new_comment").val();
        var note = $("#comment_value").val();
        var params = {'command':command, 'id':this.id, 'comment_id':comment_id, 'new_comment':new_comment, 'note':note};

        $Handle(this.action, function(x) { $PageLoader.handle(x); }, params);
    },

    handle_document: function(action, ob, command, data) {
        this.action = action;
        this.mode = 'document';

        if (this.IsTrace)
            alert('handle_document, action:'+action+', command:'+command);

        this._before(ob, command);

        var params = {'command':command, 'id':this.id};

        if (command == 'DEL_DOCUMENT')
            params['document_id'] = $TablineSelector.get_id();

        $Handle(this.action, function(x) { $PageLoader.handle(x); }, params);
    },

    handle_status: function(action, ob, command) {
        this.action = action;
        this.mode = 'set-status';

        this._before(ob);

        var params = {'command':command};

        $Handle(this.action, function(x) { $PageLoader.handle(x); }, params);
    },

    handle_refresh: function(action, ob, command) {
        this.action = action;
        this.mode = 'refresh';

        var params = {'command':command};

        $Handle(this.action, function(x) { $PageLoader.refresh_after_review(x); }, params);
    },

    select_item: function(action, ob, command) {
        this.action = action;
        this.mode = 'barcode';

        var item_id = $TablineSelector.get_id();

        //alert(item_id);

        var params = {'command':command, 'item_id':item_id};

        $Handle(this.action, function(x) { $PageLoader.handle(x); }, params);
    },

    disable_edit: function(props) {
        var prop_disabled = getObjectValueByKey(props, 'disabled_edit');

        if (!prop_disabled)
            return;

        var obs = $(".edit-box");

        obs.each(function(index) {
            $(this).prop("disabled", prop_disabled).hide();
        });
    },

    disable_review: function(props) {
        var disabled_review = getObjectValueByKey(props, 'disabled_review');
        var disabled_accept = getObjectValueByKey(props, 'disabled_accept');
        var disabled_paid = getObjectValueByKey(props, 'disabled_paid');
        var disabled_validated = getObjectValueByKey(props, 'disabled_validated');
        var disabled_delivered = getObjectValueByKey(props, 'disabled_delivered');

        $("#info-container").addClass(disabled_review ? 'frozen' : 'editable');

        var hidden = 0;
        var is_hide_confirmation= false;
        var obs = $("#review-data-buttons").children();

        obs.each(function(index) {
            var ob = $(this);
            var id = ob.attr('id');

            if (['REVIEW_CONFIRM', 'REVIEW_REJECT'].indexOf(id) > -1) {
                if (disabled_review) {
                    ob.prop("disabled", true).addClass('invisible');
                    ++hidden;
                }
            }
            else if (['REVIEW_ACCEPT'].indexOf(id) > -1) {
                if (disabled_accept) {
                    ob.prop("disabled", true).addClass('invisible');
                    ++hidden;
                }
            }
            else if (['REVIEW_PAID'].indexOf(id) > -1) {
                if (disabled_paid) {
                    ob.prop("disabled", true).addClass('invisible');
                    ++hidden;
                }
            }
            else if (['REVIEW_FAILURE', 'REVIEW_VALIDATED'].indexOf(id) > -1) {
                if (disabled_validated) {
                    ob.prop("disabled", true).addClass('invisible');
                    ++hidden;
                }
            }
            else if (['REVIEW_DELIVERED'].indexOf(id) > -1) {
                if (disabled_delivered) {
                    ob.prop("disabled", true).addClass('invisible');
                    ++hidden;
                }
                else {
                    is_hide_confirmation = true;
                }
            }
        });

        if (IsHideConfirmation) {
            var ob = $("#REVIEW_CONFIRMATION");

            if (is_exist(ob) && is_hide_confirmation) {
                ob.prop("disabled", true).addClass('invisible');
                ++hidden;
            }
        }

        if (hidden == obs.length)
            $("#review-info-data").addClass('hidden');
    },

    disable_statuses: function(props) {
        var disabled_statuses = getObjectValueByKey(props, 'disabled_statuses');
        
        if (is_empty(disabled_statuses))
            return;

        var hidden = 0;
        var obs = $("#statuses-data-buttons").children();

        obs.each(function(index) {
            var ob = $(this);
            var id = ob.attr('id');

            if (index < disabled_statuses.length && disabled_statuses[index]) {
                ob.prop("disabled", true).addClass('invisible');
                ++hidden;
            }
        });

        if (hidden == obs.length)
            $("#statuses-info-data").addClass('invisible');
    },

    _register: function() {
        this.container = $("#"+selected_review_id);
        
        this.line['id'] = $LineSelector.get_id();

        if (is_no_line_open)
            this.container.addClass('closed');

        this.line['state_is_open'] = is_no_line_open ? 0 : 1;

        is_no_line_open = 0;
    },

    is_activated: function() {
        return this.line['state_is_open'] == -1 ? true : false;
    },

    activate: function(ob) {
        var line_id = $_get_item_id(ob);

        if (this.IsDeepDebug)
            alert(['activate', this.line['id'], line_id, this.container.attr('id'), ob.position().top].join(':'));

        if (this.line['id'] == line_id) {
            if (this.line['state_is_open'] == 1) {
                this.container.addClass('closed');
                this.line['state_is_open'] = 0;
            }
            else if (this.line['state_is_open'] == 0) {
                this.container.removeClass('closed');
                this.line['state_is_open'] = 1;
            }
            return;
        }

        this.scroll_mode = default_scroll_mode;

        this._lock();

        $LineSelector.onRefresh(ob);
    },

    refresh_line: function(response, line) {
        var data = response['data'];
        var columns = response['columns'];
        var props = response['props'];

        if (is_null(line))
            line = $LineSelector.get_current();

        if (!is_empty(data)) {
            $("td[class~='column']", line).each(function(index) { 
                var column = columns[index];
                if (column in props['css']) {
                    for (n=0; n < props['css'][column].length; n++) {
                        var css = props['css'][column][n];
                        if (css.length == 2) {
                            var c = css[0];
                            var a = css[1];
                            if (a == 'add')
                                $(this).addClass(c);
                            else if (a == 'remove')
                                $(this).removeClass(c);
                        }
                    }
                }
                $(this).html(data[column]); 
            });
        }
    },

    refresh_status: function(response) {
        var currentfile = response['currentfile'];
        var info = currentfile[1];

        if (!is_empty(info)) {
            this.update_tab_count(info);

            this.check_paid(info);

            var status = info['status'];

            this.set_status(status);
        }
    },

    refresh_after_review: function(response) {
        if (this.IsTrace)
            alert('$PageLoader.refresh_after_review');

        if (this.IsLog)
            console.log('$PageLoader.refresh_after_review', response);

        if (!is_null(response)) {
            var props = response['props'];
            var total = parseInt(response['total'] || 0);
            var status = response['status'];
            var path = response['path'];

            $updateSublineData(default_action, response, props, total, status, path);

            this.refresh_line(response);

            this.disable_review(props);

            this.disable_edit(props);

            this.disable_statuses(props);

            this.refresh_status(response);
        }
    },

    refresh: function(response) {
        /***
         *  Called by default_handler, action:default_log_action
         */
        if (this.IsTrace)
            alert('$PageLoader.refresh');

        this.reset();

        var current_action = default_action;

        this.init();

        this.remove_current();

        var columns = response['columns'];
        var colspan = columns.length || 10;

        var line = $LineSelector.get_current();
        var content = $("#provision_container_template").html().replace(/__/g, '');

        line.after(
            '<tr class="line" id="'+selected_review_id+'"><td colspan="'+colspan.toString()+'">'+content+'</td></tr>'
            );

        this.refresh_after_review(response);

        var tabs = response['currentfile'][1]['tabs'];

        if (!is_empty(tabs)) {
            this.update_tab(this.actions['param'], tabs['params']);
            this.update_tab(this.actions['item'], tabs['items']);
            this.update_tab(this.actions['payment'], tabs['payments']);
            this.update_tab(this.actions['refer'], tabs['refers']);
            this.update_tab(this.actions['comment'], tabs['comments']);

            if (is_show_documents) {
                this.update_tab(this.actions['document'], tabs['documents']);
                var ob = $("#document-actions");

                if (is_exist(ob)) {
                    if (is_empty(getattr(tabs['documents'], 'data')))
                        ob.hide();
                    else
                        ob.show();
                }
            }
        }

        if (this.IsLog)
            console.log('$PageLoader.refresh, selected_data_menu_id:', selected_data_menu_id);

        $TabSelector.init();

        if (!is_empty(selected_data_menu_id))
            $TabSelector.set_current_by_id(selected_data_menu_id);
        else {
            $ShowMenu(default_menu_item);
            $TabSelector.onMove(selected_data_menu_id);
        }

        $onInfoContainerChanged('refresh');

        this.set_barcode(response['props']);

        if (!is_full_container)
            this.scroll();

        this._unlock();

        this._after();

        this._register();

        if (!search_is_empty())
            return;

        $ProvisionReviewDialog.set_read(null, '', 1);
    },

    _after: function() {
        selected_menu_action = default_log_action;
        isCallback = false;
    }
};

var $SidebarDialog = {
    documents_container : null,
    decrees_container   : null,
    pointer             : null,
    ob                  : null,

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    active        : null,
    size          : {'height' : 140, 'width' : 250, 'row_height' : 50, 'row_width' : 70},
    top           : null,
    screen_height : null,

    is_shown      : 0,

    init: function() {
        this.documents_container = $("#documents-schedule-container");
        this.decrees_container = $("#decrees-schedule-container");
        this.pointer = $("#sidebarPointer");
    },

    activate: function(ob, done_action) {
        this.ob = ob;

        if (this.IsTrace)
            alert(this.ob.attr('id'));

        if (this.is_shown)
            this.hide(done_action);
        else if (is_null(done_action))
            this.show();
    },

    clear: function() {
        $("div[class^='value']", this.documents_container).each(function() { $(this).html('<div class="no-value">0</div>') });
        $("div[class^='value']", this.decrees_container).each(function() { $(this).html('<div class="no-value">0</div>') });
    },

    refreshed: function(x) {
        var self = $SidebarDialog; 

        if (this.IsTrace)
            alert('$SidebarDialog.refreshed');

        this.active = getattr(x['props'], 'active', null);

        var data = x['data']['documents'];
        var columns = x['columns']['documents'];

        columns.forEach(function(id, index) {
            $("#"+id, self.documents_container).html(data[id]);
        });

        var data = x['data']['decrees'];
        var columns = x['columns']['decrees'];

        columns.forEach(function(id, index) {
            $("#"+id, self.decrees_container).html(data[id]);
        });
    },

    done: function(done_action) {
        this.top = this.documents_container.position().top;
        this.screen_height = document.documentElement.clientHeight;
    },

    update: function() {
        this.clear();

        var action = '863';
        var params = {'command':'schedule', 'per_page':$LineSelector.per_page};

        $web_logging(action, function(x) { $SidebarDialog.refreshed(x); }, params);
    },

    show: function() {
        this.update();

        var height = this.size.height + schedule_documents[0] * this.size.row_height;
        var width = this.size.width + schedule_documents[1] * this.size.row_width;

        this.pointer = $("#sidebarPointer");

        var pointer_height = this.pointer.height();
        var bottom = this.pointer.position().top + pointer_height - 30;
        var min_height = $_height('min')-30;

        if (bottom < min_height)
            //alert(bottom+':'+min_height);
            bottom = min_height;

        var top = bottom - height;
        var left = this.pointer.position().left + this.pointer.width() + 24;
        var margin_top = [height, 0];

        if (getattr(this.active, 'documents', documents_dialog_active)) {
            this.documents_container.css({top:top, left:left, marginTop:margin_top[0]}).show()
                .animate({height:$_get_css_size(height), width:$_get_css_size(width), marginTop:margin_top[1]}, 
                    800, "easeInQuad", function() {});
        }

        var left = left + width + 20;
        var h = this.size.height + schedule_decrees[0] * this.size.row_height - 50;
        var w = this.size.width + schedule_decrees[1] * this.size.row_width - 80;

        if (getattr(this.active, 'decrees', decrees_dialog_active)) {
            this.decrees_container.css({top:top, left:left, marginTop:margin_top[0]}).show()
                .animate({height:$_get_css_size(h), width:$_get_css_size(w), marginTop:margin_top[1]}, 
                    800, "easeInQuad", function() { $SidebarDialog.done(); });
        }

        this.is_shown = 1;
    },

    hide: function(done_action) {
        this.documents_container.css({height:0, width:0}).hide();
        this.decrees_container.css({height:0, width:0}).hide();

        this.is_shown = 0;

        if (!is_null(done_action))
            done_action.callback(done_action.force);
    },

    resize: function() {
        if (!this.is_shown || is_null(this.top))
            return;

        var top = this.top + (document.documentElement.clientHeight - this.screen_height);

        this.documents_container.css({top:top});
        this.decrees_container.css({top:top});

        this.done();
    }
};

var $ReviewerDialog = {
    container   : null,
    box         : null,

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    action      : null,
    mode        : '',
    login       : null,

    is_shown    : false,
    is_error    : false,

    init: function() {
        this.box = $("#reviewer-box");
        this.container = this.box.parent().parent();

        if (this.IsTrace)
            alert('$ReviewerDialog.init: id='+this.container.attr('id'));
    },

    show: function() {
        this.container.show();
        this.is_shown = true;
    },

    hide: function() {
        this.container.hide();
        this.is_shown = false;
    },

    check: function(x) {
        var errors = x['errors'];

        if (this.IsLog)
            console.log('$ReviewerDialog.check, errors:', errors);

        if (!is_null(errors) && errors.length > 0) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
            this.is_error = true;

            this.hide();
        }
    },

    handle: function(x) {
        this.check(x);

        if (this.is_error)
            return;

        var data = getObjectValueByKey(x, 'data');

        switch (this.mode) {
            case 'refresh':
                this.refresh(data);
        }
    },

    reset: function() {
        this.box.html('');
        this.hide();
    },

    refresh: function(data) {
        if (is_null(data)) {
            this.hide();
            return;
        }

        if (this.IsLog)
            console.log('$ReviewerDialog.refresh, data:', data);
        
        this.box.html('');

        var content = '';

        content += 
            '<div class="box reviewer-photo"><img id="reviewer-photo" src="'+ data['avatar']+'" title="" alt=""></div>'+
            '<div class="box reviewer-info"> '+
              '<div class="fio">'+
                '<span>'+data['full_name']+'</span>';
        
        //if ($_mobile())
            content += 
                '<div class="close"><img class="close-icon" id="close-icon" src="'+root+'static/img/close-32.png" title="close" alt="close"></div>';

        content += 
              '</div>'+
              '<div class="profile">'+
                '<table border="0">'+
                  '<tr><td class="reviewer-caption">??????????????????????????:</td><td class="reviewer-value">'+data['subdivision']+'</td></tr>'+
                  '<tr><td class="reviewer-caption">??????????????????:</td><td class="reviewer-value">'+data['post']+'</td></tr>'+
                  '<tr><td class="reviewer-caption">???????????????????????????? ????????:</td><td class="reviewer-value">'+data['app_role_name']+'</td></tr>'+
                  '<tr><td class="reviewer-caption">????????:</td><td class="reviewer-value">'+data['role_name']+'</td></tr>'+
                  '<tr><td class="reviewer-caption">????????????????????:</td><td class="reviewer-value">'+data['privileges']+'</td></tr>'+
                  '<tr><td class="reviewer-caption">??????????:</td><td class="reviewer-value">'+data['login']+'</td></tr>'+
                '</table>'+
              '</div>'+
            '</div>'+
            '<div class="reviewer-data"> '+
              '<div class="data">'+
                '<table border="0">'+
                '<tr>'+
                  '<td class="reviewer-order">?????????? '+data['ob_types']+': '+data['orders']+'</td>'+
                  '<td class="reviewer-decree">?????????????????? ????????????: '+data['decrees_out']+'</td>'+
                  '<td class="reviewer-decree">?????????????????? ????????????????: '+data['decrees_in']+'</td>'+
                '</tr>'+
                '</table>'+
              '</div>'+
            '</div>';

        this.box.append(content);
        this.show();

        resize();
    },

    render: function(login) {
        if (this.IsTrace)
            alert('$ReviewerDialog.render:['+login+']');

        this.action = '860';
        this.mode = 'refresh';
        this.login = login;

        var params = {'command':'render', 'login':login};

        $Handle(this.action, function(x) { $ReviewerDialog.handle(x); }, params);
    }
};
