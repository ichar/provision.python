// **********************************************
// PERSOSTATION PAGE DECLARATION: /provision.html
// ----------------------------------------------
// Version: 1.00
// Date: 10-06-2019

default_submit_mode  = 2;
default_action       = '830';
default_log_action   = '831';
default_print_action = '850';
default_input_name   = 'order_id';
default_menu_item    = 'data-menu-reviews';
default_handler      = function(x) { $PageLoader.refresh(x); };
default_params       = { 'max-width': $_width('client') };

IsDebug = 0;
IsTrace = 0;
IsLog = 0;

LINE = 'order';
SUBLINE = 'review';

// Change info container size
var IsOptionContainerChanged = 0;
// Hide Confirmation if review disabled
var IsHideConfirmation = 0;

var default_screen_max = 0;

// Animated resizing of 'sizable-container'
var line_base_size = [0, 0];

// Sidebar callback timeout
var sidebar_timeout = 500;
var timer = null;

// Flag for 'input' keyboards
var is_input_focused = false;

// List of modes to arrange size of page
var default_startups = []; //, 'resize', 'sidebar'

// List of review classes
var review_classes = ['accepted', 'rejected', 'confirm', 'execute'];

// List of Seller Order form items
var seller_items = ['Code', 'Title', 'Address', 'Contact'];

// Action/Command for StockList reference
var stocklist_action = '861';
var stocklist_command = 'service:stocklist';

// Pyaments total rest value
var payment_total = '';

// Type of `param` control: 1-input, 2-combo
var param_value_mode = 1;

// ----------------------
// Dialog Action Handlers
// ----------------------

function subline_refresh(info, is_print) {
/***
 *  Callback of SUBLINE refresher.
 *  Used for update `.filename` area after loading of SUBLINE container.
 *
 *  Action:         default_action
 *  Page Handler:   default_handler
 *
 *  Track: 
 *      log.default:$updateSublineData
 *      provision.default:$PageLoader.refresh
 *      db.controller: -> handler
 *      db.controller:$web_logging
 *      db.controller:$LineSelector.onRefresh
 *      local:Line selection
 *          or
 *      common:$ShowOnStartup
 *      local:$Init
 *
 *  Hard link.
 */
    var dates = info['dates'];
    var review_date = !is_null(dates) ? dates[1][2] : '';
    var params = info['params'];

    var refers_info = getObjectValueByKey(info, 'refers_info');

    var html = '' +
        '<table id="x5_box" border="0"><tr><td>' +
        (getObjectValueByKey(info, 'order') ? '<h3><span id="subline_name">'+info['order']+'</span></h3>' : '') +
        '<div class="x5">' +
        '<div class="x5_left">' +
            '<div class="purpose">' +
                (getObjectValueByKey(info, 'purpose', null) ? '<h4>'+params['purpose']+':</h4><div class="info">'+info['purpose']+'</div>' : '') +
            '</div>' +
            '<div class="equipment">' +
                (getObjectValueByKey(info, 'equipment_title') ? '<div class="equipment_title"><h4>'+params['equipment_title']+':</h4><div class="info">'+info['equipment_title']+'</div></div>' : '') +
                (getObjectValueByKey(info, 'equipment_name') ? '<br><div class="equipment_name"><h4>'+params['equipment_name']+':</h4><div class="info">'+info['equipment_name']+'</div></div>' : '') +
                (getObjectValueByKey(info, 'sector') ? '<br><div class="sector"><h4>Участок:</h4><div class="info">'+info['sector']+'</div></div>' : '') +
                (getObjectValueByKey(info, 'stocklist') ? '<br><div class="stocklist_name"><h4>'+info['stocklist']['title']+':</h4><div class="stockitem" '
                     + 'oid="'+info['stocklist']['id']+'" ocode="'+info['stocklist']['parent_code']+'" olevel="'+info['stocklist']['level']+'">'
                     + info['stocklist']['name']+'</div></div>' : '') + 
            '</div>' +
            '<div class="seller">' +
                (getObjectValueByKey(info, 'seller_name') ? '<div class="seller_name"><h4>'+params['seller_name']+':</h4><div class="info">'+info['seller_link']+'</div></div>' : '') +
                (getObjectValueByKey(info, 'seller_title') ? '<br><div class="seller_title"><h4>'+params['seller_title']+':</h4><div class="info">'+info['seller_title']+'</div></div>' : '') +
                (getObjectValueByKey(info, 'url') ? '<br><div class="seller_url"><h4>'+params['seller_url']+':</h4><div class="info">'+info['url']+'</div></div>' : '') +
            '</div>' +
        '</div>' +
        '<div class="x5_right">' +
            (getObjectValueByKey(info, 'category') ? '<div class="category '+info['category']['class']+'"><div class="category_name" title="'+info['category']['title']+'">'+info['category']['code']+'</div></div>' : '') +
        '</div>' +
        '</div>';

    if (params['with_cross']) html += 

        '<div class="x5_middle">' +
            '<table border="0"><tr>' +
            (getObjectValueByKey(info, 'EUR') ? '<td><div class="EUR" id="paid-base"><span>EUR[€]&nbsp;'+
                info['EUR']+'&nbsp;=&nbsp;CROSS:&nbsp;'+
                info['cross']+'&nbsp;=&nbsp;TAX:&nbsp;'+
                info['tax']+'&nbsp;RUB[₽]&nbsp;=&nbsp;RATE:&nbsp;'+
                info['rate']+'</span></div></td>' : '') +
            '<td><div id="paid-panel" title="'+getObjectValueByKey(info, 'paid_total_title', '')+'" style="display:none;"><div>ОПЛАЧЕНО (РУБ)</div><span id="paid-panel-value">0.0</span></div></td></tr>' +
            '<tr><td><div class="refers_info" id="refers-info"'+(refers_info ? '' : ' style="display:none;"')+'><h3>'+
                '<span id="refers-info-title">'+getObjectValueByKey(refers_info, 'title', '')+'</span>&nbsp;'+
                '<span id="refers-info-value">'+getObjectValueByKey(refers_info, 'value', '')+'</span></h3></div></td></tr>' +
            (review_date && review_date != '**.**.****' ? '<tr><td><div class="review_date"><h3>ВНИМАНИЕ! Заказу назначен срок обоснования:'+'&nbsp;<span>'+review_date+'</span></h3></div></td></tr>' : '') +
            '</table></div>';

    html += 
        (getObjectValueByKey(info, 'edited_by') ? '<div class="author">'+info['edited_by']+'</div>' : '');

    html += 
        '</td></tr></table>';

    if (is_print)
        return html;

    var container = $("#subline-content");

    $(".filename", container).each(function() { 
        $(this).html(html);
    });

    refresh_subline_documents(info);

    refresh_subline_images(info);

    refresh_subline_dates(info);

    toggle_subline_area();
}

function refresh_subline_documents(info) {
    var actions = {
        'download' : ['download_all_documents', 'documents', 'download_all'], 
        'blank' : ['make_blank','blank','blank']
    };

    for (var key in actions) {
        var action = actions[key];
        var control_id = action[0];
        var param = action[1];
        var path = action[2];
        var ob = $("#"+control_id);

        if (is_exist(ob)) {
            var parent = ob.parent();

            if (!getattr(info, param, null))
                parent.hide();
            else
                parent.show();

            ob.attr("href", "/"+current_context+"/"+path+"/"+info['order_id']);
        }
    }
}

function refresh_subline_images(info) {
    var images = getObjectValueByKey(info, 'images');

    if (is_null(images))
        return;

    var html = '';

    if (images && images.length > 0) {
        html += '<div class="image">';
        images.forEach(function(image) {
            html += '<img class="product_image" src="'+image+'" title="Product Image" alt>';
        });
        html += '</div>';
    }

    $("#images-box").html(html);
}

function refresh_subline_dates(info) {
    var dates = info['dates'];

    if (is_null(dates))
        return;

    html = '';

    for (var i=0; i < dates.length; i++) {
        var key = dates[i][0];
        var title = dates[i][1];
        var value = dates[i][2] || '**.**.****';
        html += '<div class="order_date '+key+'"><h4>'+title+'</h4><dd><nobr>'+value+'</nobr></dd></div>';
    }

    $("#dates-box").html(html);
}

function toggle_subline_area() {
    var is_toggle = ($TabSelector.count > 0 && $TabSelector.number == $TabSelector.count) ? true : false;
    var images = $("#images-area");
    var box = $("#dates-area");

    if (is_exist(images)) {
        if (is_toggle)
            images.hide();
        else
            images.show();
    }

    if (is_exist(box)) {
        if (is_toggle)
            box.show();
        else
            box.hide();
    }

    var paid = $("#paid-panel");

    if (is_exist(paid) && IsOptionCheckBigScreen) {
        if (is_toggle)
            paid.hide();
        else
            paid.show();
    }
}

function sidebar_callback() {
/***
 *  Callback of $SidebarControl.
 *  Used for arange main page after Sidebar screen changed.
 *
 *  Track: 
 *      controls:$SidebarControl.checkShown
 *
 *  Sets by local:$Init.
 */
    if (!is_null(timer)) {
        clearTimeout(timer);
        timer = null;
    }

    if ($SidebarControl.isDueAnimated())
        timer = setTimeout(function() { sidebar_callback(); }, sidebar_timeout);

    $onInfoContainerChanged('sidebar');
}

function sidebar_toggle() {
/***
 *  Callback of $SidebarControl.
 *
 *  Track: 
 *      controls:$SidebarControl.onToggle
 *
 *  Hard link.
 */
    default_startups.remove('sidebar');
}

function clean_order_item(id) {
    if (!is_empty(id)) {
        var parent = $("#order-form");

        switch (id) {
            case 'new_order_seller':
                seller_items.forEach(function(name) { 
                    $("#order_seller_"+name.toLowerCase(), parent).each(function() { 
                        $(this).val(''); 
                    });
                });
                $("#order_seller").val(0);
                break;
        }
    }
}

function reviewer_toggle(show, ob) {
    if (show) {
        var login = ob.attr("alt");
        $ReviewerDialog.render(login);
    }
    else
        $ReviewerDialog.hide();
}

function sidebar_submit() {
/***
 *  Callback of $SidebarControl.
 *  Used for handle before submit of form $SidebarControl
 *
 *  Track: 
 *      controls:$SidebarControl.onBeforeSubmit
 *
 *  Hard link.
 */
    //var container = $("#pagination-form");
    //$("#reset").each(function() { $(this).val(1); });
    //container.find("#reset").each(function(index, x) { $x.val(1); });
}

function log_callback_error(action, errors) {
/***
 *  Callback of check loader errors.
 *  Used for handle after respond (response is loaded) by $web_logging before process handler.
 *
 *  Track: 
 *      db.controller:$web_logging
 *
 *  Hard link.
 */
   //alert('log_callback_error');

   if (!is_null(errors) && errors.length > 0) {
        var msg = errors.join('<br>');
        $ShowError(msg, true, true, false);
        should_be_updated = false;
    }
}

function log_callback(current_action, data, props) {
/***
 *  Callback of loader.
 *  Used for handle after respond (response is loaded) by $web_logging.
 *
 *  Track: 
 *      db.controller:$web_logging
 *
 *  Hard link.
 */
    selected_menu_action = null;

    $("#note").val('');

    if (should_be_updated) {
        should_be_updated = false;
        timer = setTimeout(function() { update_review(); }, 100);
    }
}

function update_stocklist(params) {
    //var ob = $LineSelector.get_current();
    //alert('update_stocklist:'+reprObject(params));

    $Handle('862', default_handler, params);
}

function update_group_stocklist(params) {
    var frm = $("#filter-form");

    params['query'] = {
        'search' : $("#search-context").val(),
        'subdivision' : $("#subdivision", frm).val(),
        'author' : $("#author", frm).val(),
        'stock' : $("#stock", frm).val(),
        'category' : $("#category", frm).val(),
        'seller' : $("#seller", frm).val(),
        'currency' : $("#currency", frm).val(),
        'condition' : $("#condition", frm).val(),
        'date_from' : $("#order-date-from", frm).val(),
        'date_to' : $("#order-date-to", frm).val(),
        'status' : $("#status", frm).val(),
        'paid' : $("#paid", frm).val()
    };

    //alert('update_group_stocklist:'+reprObject(params));

    $Handle('865', default_handler, params);
}

function update_review() {
    if (!is_null(timer)) {
        clearTimeout(timer);
        timer = null;
    }

    var params = {};

    $Handle('840', function(x) { update_order_status(x); }, params);
}

function update_order_status(response) {
    $PageLoader.refresh_status(response);

    var props = response['props'];
    var data = response['data'];

    //alert(reprObject(data)+':'+props.join('-'));

    if (is_empty(data))
        return;

    var ob = SelectedGetItem(LINE, 'ob');

    if (is_null(ob))
        return;

    var status = data[0];
    var title = data[1];

    function clean_class(ob) {
        review_classes.forEach(function(x, index) {
            ob.removeClass(x);
        });
    }

    clean_class(ob);

    $('td', ob).each(function(index) {
        if (props.indexOf(index) > -1) {
            clean_class($(this));
            $(this).removeClass("selected").addClass(status).addClass("noselected");
            $(this).attr('title', title);
        }
    });

    ob.removeClass("unread").addClass(status);
}

function refresh_order_item(response) {
    var data = response['data'];

    //alert(joinToPrint([data['Title'], parent, reprObject(data)]));

    if (!is_empty(data)) {
        var parent = $("#order-form");

        switch (confirm_action) {
            case 'seller':
                seller_items.forEach(function(name) { 
                    //console.log(`#order_seller_${name.toLowerCase()}`);
                    $("#order_seller_"+name.toLowerCase(), parent).each(function() { 
                        $(this).val(data[name]); 
                    });
                });
                $("#new_order_seller").val('');
                break;
        }
    }

    confirm_action = '';
}

function approval_sent(x) {
    $NotificationDialog.open(keywords['Message:Action was done successfully']);
}

function notification_sent(x) {
    $NotificationDialog.open(keywords['Message:Action was done successfully']);
}

function check_param(value, reset) {
    var container_input = $("#container_param_value", "#params-items");
    var container_combo = $("#container_param_value_combo", "#params-items");
    var item = $("#param option:selected").html().toLowerCase();
    var is_select_type = item.endswith(':[список]') ? true : false;

    var hidden_class = "hidden";

    if (is_select_type) {
        param_value_mode = 2;
        container_input.addClass(hidden_class);
        container_combo.removeClass(hidden_class);

        var box = $("#param_value_combo", "#params-items");

        if (!reset)
            if (is_exist(box))
                $PageLoader.handle_param_combo('867', box, 'ADD_PARAM_COMBO');
        else
            $PageLoader._reset();
    }
    else {
        param_value_mode = 1;
        container_combo.addClass(hidden_class);
        container_input.removeClass(hidden_class);

        var box = $("#param_value", "#params-items");
        var is_date_type = item.indexOf('дата') > -1 || item.indexOf('срок') > -1 ? true : false;

        if (is_exist(box))
            box.attr('type', is_date_type && !reset ? 'date' : 'text');
    
        if (!is_null(value))
            box.val(value);
    }
}

function check_refer(value, reset) {
    var box = $("#refer_value", "#refers-items");
    var item = value || $("#refer option:selected").html().toLowerCase();
}

function print_barcode(ob, id) {
    var box = $("#barcode_area");

    //alert(id);

    printProvisionBarcode(box);
}

// --------------
// Page Functions
// --------------

function $Init() {
    $SidebarControl.init(sidebar_callback, ['subdivision', 'stock', 'category', 'seller'], true);

    page_sort_title = $("#sort_icon").attr('title');

    SelectedReset();

    $LineSelector.init();

    $ReviewerDialog.init();
    $ProvisionReviewDialog.init();

    // ------------------------
    // Start default log action
    // ------------------------

    interrupt(true, 1);
}

function $Confirm(mode, ob) {
    $ConfirmDialog.close();

    if (mode == 1) {
        switch (confirm_action) {
            case 'admin:deleteorder':
                $ProvisionSelectorDialog.confirmed();
                break;
            case 'admin:download':
            case 'admin:delete-orders':
            case 'admin:clear-history':
                $ProvisionServiceDialog.confirmed();
                break;
            case 'admin:send-approval':
            case 'admin:send-review-notification':
            case 'admin:send-order-notification':
                $ProvisionServiceDialog.lived();
                break;
            case 'reference:remove':
                $ReferenceDialog.confirmed('remove');
                break;
            case 'decree:finish':
                $ProvisionDecreeDialog.finish(1);
                break;
            case 'decree:reject':
                $ProvisionDecreeDialog.reject(1);
                break;
            case 'decree:remove':
                $ProvisionDecreeDialog.remove(1);
                break;
        }
    }

    confirm_action = '';
}

function $Notification(mode, ob) {
    $NotificationDialog.close();

    if (mode == 1) {
        switch (confirm_action) {
            case 'order.checked':
            case 'decree.checked':
                $ProvisionSelectorDialog.exit();
        }
    }

    confirm_action = '';
}

function $ShowMenu(id, status, path) {

    // -----------------------------------------
    // Show (open) selected DataMenu item (Tabs)
    // -----------------------------------------

    var reviews = $("#reviews-content");
    var params = $("#params-content");
    var items = $("#items-content");
    var payments = $("#payments-content");
    var refers = $("#refers-content");
    var documents = $("#documents-content");
    var comments = $("#comments-content");
    var statuses = $("#statuses-content");

    var tab = $("#"+id);

    if (selected_data_menu)
        selected_data_menu.removeClass('selected');

    selected_data_menu = tab;

    reviews.hide();
    params.hide();
    items.hide();
    payments.hide();
    refers.hide();
    documents.hide();
    comments.hide();
    statuses.hide();

    if (id == 'data-menu-reviews')
        reviews.show();
    else if (id == 'data-menu-params')
        params.show();
    else if (id == 'data-menu-items')
        items.show();
    else if (id == 'data-menu-payments')
        payments.show();
    else if (id == 'data-menu-refers')
        refers.show();
    else if (id == 'data-menu-documents')
        documents.show();
    else if (id == 'data-menu-comments')
        comments.show();
    else if (id == 'data-menu-statuses')
        statuses.show();

    if (id == default_menu_item)
        $SublineSelector.init();
    else if (['data-menu-statuses'].indexOf(id) == -1)
        $TablineSelector.init(tab);

    selected_data_menu.addClass('selected');
    selected_data_menu_id = id;

    if (IsLog)
        console.log('$ShowMenu, selected_data_menu_id:', selected_data_menu_id);
}

// --------------------
// Page Events Handlers
// --------------------

function $onPaginationFormSubmit(frm) {
    return true;
}

function $onFilterFormSubmit(frm) {
    return true;
}

function $onInfoContainerChanged(startup) {
    if (default_startups.indexOf(startup) > -1)
        return;

    if (!is_null(timer))
        return;

    var container = $("#line-content");
    var box = $("#line-box");

    if (!is_exist(container) || !is_exist(box))
        return;

    //alert(startup);

    if (startup == 'refresh')
        removeClass(container, "hidden");

    // Flag: sidebar is open
    var s = $SidebarControl.state == 1;
    // Flag: this is mobile frame
    var f = $IS_FRAME == 0;

    //alert('W:'+[$_width('screen-max'), $_width('screen-min'), $_width('max'), $_width('min')].join(':'));
    //alert('H:'+[$_height('screen-max'), $_height('screen-min'), $_height('max'), $_height('min'), $_height('available')].join(':'));

    var mainmenu = $("#mainmenu");
    var info_container = $("#info-container");
    var pagination = $("table", "#log-pagination");

    if (!is_exist(info_container) || info_container.height() == 0)
        return;

    var content_width = $("#line-table").width();
    var sidebar_width = s ? $("#sidebarFrame").width() : 50;
    var box_width = box.width();
    var info_height = $("#tab-content").height() + mainmenu.height(); // $("#tab-content") info_container
    var pagination_width = Math.max(pagination.width() + 10, mainmenu.width());

    //alert(startup+':'+info_height+':'+$IS_FRAME+':'+is_webkit+':'+is_full_container);

    var screen_width = 0;
    var screen_height = 0;
    var W = 0;
    var H = 0;
    
    var default_min_height = 0;

    if (f) {
        screen_width = $_width('max');
        screen_height = $_height('max'); //'available'

        W = screen_width - sidebar_width - (s ? 40 : 0); //48
        H = screen_height - 215;

        info_height += 20;
        default_min_height = 216;
    }
    else {
        var mode = 'min'; //is_webkit ? 'min' : 'max';

        screen_width = $_width(mode);
        screen_height = $_height('max');

        W = screen_width - sidebar_width - (s ? 48 : 22);
        H = screen_height - 186;

        info_height += 10;
        default_min_height = 304;
    }

    if (is_full_container)
        H = H - info_height; //H = H - info_height > default_min_height ? H - info_height : default_min_height;

    if (pagination_width > W)
        W = pagination_width;

    //if ($_screen_with_scroll('height') && $IS_FRAME == 1) W = W - 20;

    if (W == line_base_size[0] && H == line_base_size[1] && startup != 'refresh')
        return;

    if (IsDebug)
        alert([startup, f, s, 'W', sidebar_width, screen_width, box_width, content_width, W, 'H', screen_height, H].join(':'));

    var width = int(W) - 6;
    var height = int(H) - 6;

    if (is_full_container) {
        container.css("height", $_get_css_size(H));
        box.css("height", $_get_css_size(height));

        if (f && s)
            return;
    }

    if (IsOptionContainerChanged) {
        container.css("width", $_get_css_size(W));
        box.css("width", $_get_css_size(width));

        if (!f && !is_full_container)
            box.css({ "overflow-y" : "hidden", "overflow-x" : width <= content_width ? "scroll" : "hidden" });
    }

    line_base_size = [W, H];
}

function $onTabSelect(ob) {
    var id = ob.attr("id");

    $ShowMenu(id);

    var tab = $("#selected_data_menu_id");

    if (is_exist(tab))
        tab.val(selected_data_menu_id);

    toggle_subline_area();

    return true;
}

function $onSublineSelect(ob) {
    //alert(ob.attr('id'));
    //alert($SublineSelector.current.attr('id'));
    //alert($SublineSelector.get_id());
}

function $onTablineSelect() {
    var tabline_mode = $TablineSelector.get_mode();
    var tabline_id = $TablineSelector.get_id();
    
    //alert(tabline_mode+'::'+tabline_id);

    switch (tabline_mode) {
        case 'items':
            //alert(tabline_id);
            $PageLoader.select_item('868', null, 'GENERATE');
    }
}

// ===========================
// Dialog windows declarations
// ===========================

function MakeFilterSubmit(mode, page) {
    $("#filter-form").attr("action", baseURI);

    switch (mode) {

        // -------------
        // Submit modes:
        // -------------
        //  0 - changed subdivision
        //  1 - changed author
        //  2 - changed seller
        //  3 - changed currency
        //  4 - changed condition
        //  5 - changed date from
        //  5 - changed date to
        //  6 - changed status
        //  7 - changed paid
        //  8 - changed category
        //  9 - changed stock

        case 0:
            //$("#reviewtype").each(function() { $(this).val(0); });
        case 1:
        case 2:
        case 3:
        case 4:
        case 5:
        case 6:
        case 7:
            $("#window_scroll").each(function() { $(this).val(0); });
            no_window_scroll = true;
            break;

        // ---------------------------
        // LineSelector Handler submit
        // ---------------------------

        case 9:
            $("#order_id").each(function() { $(this).val(0); });
            $("#review_id").each(function() { $(this).val(0); });
    }

    $ResetLogPage();

    $setPaginationFormSubmit(page);
    $onParentFormSubmit('filter-form');
}

function MakeAction(ob) {
    var id = ob.attr("id");
    var action = 
        (id == 'REVIEW_ACCEPT' ? '832' : 
        (id == 'REVIEW_REJECT' ? '833' : 
        (id == 'REVIEW_CONFIRM' ? '834' : 
        (id == 'REVIEW_CONFIRMATION' ? '835' : 
        (id == 'REVIEW_VALIDATED' ? '859' :
        (id == 'ADD_PARAM'   || id == 'DEL_PARAM'   || id == 'SAVE_PARAM'   ? '836' : 
        (id == 'ADD_ITEM'    || id == 'DEL_ITEM'    || id == 'SAVE_ITEM'    ? '837' : 
        (id == 'ADD_PAYMENT' || id == 'DEL_PAYMENT' || id == 'SAVE_PAYMENT' ? '838' : 
        (id == 'ADD_REFER'   || id == 'DEL_REFER'   || id == 'SAVE_REFER'   ? '856' : 
        (id == 'ADD_COMMENT' || id == 'DEL_COMMENT' || id == 'SAVE_COMMENT' ? '839' : 
        (id == 'DEL_DOCUMENT' ? '847' : 
        (['EDIT_PARAM', 'EDIT_ITEM', 'EDIT_PAYMENT', 'EDIT_REFER', 'EDIT_COMMENT'].indexOf(id) > -1 ? '841' : 
        (['CANCEL_PARAM', 'CANCEL_ITEM', 'CANCEL_PAYMENT', 'CANCEL_REFER', 'CANCEL_COMMENT'].indexOf(id) > -1 ? '000' : 
        (id.startswith('STATUS_') ? '842' :
        null))))))))))))));

    if (is_null(action) || is_show_error)
        return false;

    else if (action == '000')
        $PageLoader.cancel(action, ob, id);

    else if (action == '836')
        $PageLoader.handle_param(action, ob, id);

    else if (action == '837')
        $PageLoader.handle_item(action, ob, id);

    else if (action == '838')
        $PageLoader.handle_payment(action, ob, id);

    else if (action == '856')
        $PageLoader.handle_refer(action, ob, id);

    else if (action == '839')
        $PageLoader.handle_comment(action, ob, id);

    else if (action == '841')
        $PageLoader.get(action, ob, id);

    else if (action == '842')
        $PageLoader.handle_status(action, ob, id);

    else if (action == '847')
        $PageLoader.handle_document(action, ob, id);

    else if (action == '859')
        $PageLoader.handle_refresh(action, ob, id);

    else {
        should_be_updated = true;
        selected_menu_action = action;
        $InProgress(ob, 1);
        $Go(action);
    }

    return true;
}

// ====================
// Page Event Listeners
// ====================

jQuery(function($) 
{
    $("td.column").click(function(e) {
        var tag = e.target.tagName;
        if (tag.toUpperCase() != 'A' && $_mobile())
            e.preventDefault();
    });

    // ----------------
    // Reference events
    // ----------------

    $("#reference-container").on('click', '.reference-button', function(e) {
        $ReferenceDialog.onButtonClick($(this));
        e.stopPropagation();
    });

    $("#reference-container").on('click', '.reference-item', function(e) {
        var id = getObjectValueByKey(e.target, 'id');

        if (id.startswith('level'))
            $ReferenceDialog.openNode($(this), stocklist_command, stocklist_action);
        else {
            $DblClickAction.click(
                function(ob) {
                    $ReferenceDialog.toggle(ob);
                },
                function(ob) {
                    $ReferenceDialog.openNode(ob, stocklist_command, stocklist_action);
                },
                $(this), 300
            );
        }
        e.stopPropagation();
    })
    .on("dblclick", function(e){
        e.preventDefault();
    });

    $(".level-icon").on('click', '.reference-item', function(e) {
        $ReferenceDialog.openNode($(this), stocklist_command, stocklist_action);
        e.stopPropagation();
    });

    $("#reference-container").on('click', '.reference-icon', function(e) {
        $ReferenceDialog.onIconClick($(this));
        e.stopPropagation();
    });

    $("#data-section").on('click', '.stockitem', function(e) {
        var ob = $(e.target);

        //console.log(ob, e.target);

        var id = ob.attr('oid') || '';
        var code = ob.attr('ocode');
        var level = ob.attr('olevel');

        //alert(id+':'+code+':'+level);

        var query = new Array();

        if (!is_empty(code)) {
            query.push(['Direction', 'down']);
            query.push(['NodeLevel', level]);
            query.push(['NodeCode', code]);
        }

        $ReferenceDialog.openReferenceItem(stocklist_command, update_stocklist, stocklist_action, query, id);
    });

    $("#data-section").on('click', '#payment_total', function(e) {
        $(this).val(payment_total);
    });

    $("#data-section").on('change', '.popup', function(e) {
        var ob = $(this);
        var id = ob.attr('id');

        if (id == 'param')
            check_param(null);
    });

    // ---------------
    // Register review
    // ---------------

    $("#data-section").on('click', '.btn', function(e) {
        var ob = $(this);
        var id = ob.attr('id');

        if (is_null(id) || is_show_error)
            return;

        //alert(['btn:', e.target, $(this), id].join(':'));

        if (id == 'REVIEW_CONFIRM') {
            $ProvisionReviewDialog.open(ob, 'review');
            return;
        }
        if (id == 'REVIEW_PAID') {
            $ProvisionReviewDialog.open(ob, 'paid');
            return;
        }
        if (id == 'REVIEW_DELIVERED') {
            $ProvisionReviewDialog.open(ob, 'delivered');
            return;
        }
        if (id == 'REVIEW_FAILURE') {
            $ProvisionReviewDialog.open(ob, 'failure');
            return;
        }
        if (id == 'REVIEW_DECREE') {
            $ProvisionDecreeDialog.open(ob, 'decree');
            return;
        }
        if (id == 'ADD_DOCUMENT') {
            $ProvisionImageLoader.add_document(ob, id);
            return;
        }
        if (id == 'PRINT_BARCODE') {
            print_barcode(ob, id);
            return;
        }

        MakeAction(ob);
    });

    $("#data-section").on('change', '#uploadDocument', function(e) {
        var value = $(this).val().split("\\");
        if (!is_null(value) && value.length > 0) {
            value = value[value.length-1];
            $("#document_filename").val(value);
        }
    });

    // -------------
    // Tab selection
    // -------------

    $("#data-section").on('click', '.menu', function(e) {
        $TabSelector.onClick($(this));

        $onTablineSelect($(this));
    });

    // --------------
    // Line selection
    // --------------

    $("#data-section").on('click', 'a', function(e) {
        e.stopPropagation();
    });

    $(".line").click(function(e) {
        //console.log(e.target, $(this).has(e.target).length, e.target.tagName);

        if (is_show_error || isWebServiceExecute || $PageLoader.locked() || e.target.tagName == 'A')
            return;

        $PageLoader.activate($(this));
        /*
        $PageLoader.reset();

        $LineSelector.onRefresh($(this));
        */
    });

    // -----------------
    // SubLine selection
    // -----------------

    $("#reviewer-dialog").on('click', '.close-icon', function(e) {
        reviewer_toggle(0, $(this));
    });

    $("#data-section").on('click', '.avatar', function(e) {
        reviewer_toggle(1, $(this));
        e.stopPropagation();
    });

    $("#data-section").on('click', '.decree', function(e) {
        $ProvisionDecreeDialog.update_decree($(this));
        e.stopPropagation();
    });

    $("#data-section").on('click', '.subline', function(e) {
        if (is_show_error)
            return;

        $SublineSelector.onRefresh($(this));

        $onSublineSelect($(this));
    });

    // -----------------
    // Tabline selection
    // -----------------

    $("#data-section").on('click', '.tabline', function(e) {
        if ($PageLoader.is_shown)
            return;

        $TablineSelector.onRefresh($(this));

        $onTablineSelect($(this));
    });

    $("#history-box").on('click', '.history', function(e) {
        $TablineSelector.onRefresh($(this));
    });

    // -----------------------------------
    // Data Section progress & Maintenance
    // -----------------------------------

    $("#data-section").on('click', '.column', function(e) {
        var ob = $(this);
        var parent = ob.parents("*[class*='line']").first();
        if (is_exist(parent) && !parent.hasClass("tabline") && !ob.hasClass("header") && $PageLoader.is_activated())
            $InProgress(ob, 1);
    });

    $("#data-section").on('focusin', 'textarea', function(e) {
        is_input_focused = true;
    }).on('focusout', function(e) {
        is_input_focused = false;
    });

    $("#data-section").on('focusin', 'input', function(e) {
        is_input_focused = true;
    }).on('focusout', function(e) {
        is_input_focused = false;
    });

    $("#order-form").on('change', '.popup', function(e) {
        $ProvisionSelectorDialog.refreshItem($(this));
        e.stopPropagation();
    });

    $("#order-form").on('change', '.string', function(e) {
        clean_order_item($(this).attr('id'));
    });

    // ------------------------
    // Control Panel Menu items
    // ------------------------

    $("#uploadButton").on('change', function(e) {
        var value = $(this).val().split("\\");
        if (!is_null(value) && value.length > 0) {
            value = value[value.length-1];
            $("#filename").val(value);
        }
    });

    $("button[id^='admin']", this).click(function(e) {
        var ob = $(this);
        var command = ob.attr('id');

        $onControlPanelClick($("#admin-panel-dropdown"));

        if (command == 'admin:create')
            $ProvisionSelectorDialog.create('order');

        else if (command == 'admin:update')
            $ProvisionSelectorDialog.update('order');

        else if (command == 'admin:delete')
            $ProvisionSelectorDialog.delete('order');

        else if (command == 'admin:clone')
            $ProvisionSelectorDialog.clone('order');

        else if (command == 'admin:history')
            $ProvisionOrderHistoryDialog.open(ob, 'order');
    });

    $("button[id^='service']", this).click(function(e) {
        var command = $(this).attr('id');

        $onControlPanelClick($("#services-dropdown"));

        if (IsAdmin && command == 'service:upload')
            $ProvisionServiceDialog.upload();

        else if (IsAdmin && command == 'service:download')
            $ProvisionServiceDialog.download();

        else if (IsAdmin && command == 'service:delete-orders')
            $ProvisionServiceDialog.deleteOrders();

        else if (command == 'service:send-approval')
            $ProvisionServiceDialog.sendApproval();

        else if (command == 'service:send-review-notification')
            $ProvisionServiceDialog.sendReviewNotification();

        else if (command == 'service:send-order-notification')
            $ProvisionServiceDialog.sendOrderNotification();

        else if (command == 'service:checked-reviewers')
            $ProvisionCheckedReviewersDialog.open($(this), 'order');

        else if (command == 'service:decree')
            $ProvisionDecreeDialog.open($(this), 'decree');

        else if (IsAdmin && command == 'service:clear-history')
            $ProvisionServiceDialog.clearHistory();

        else if (command == stocklist_command)
            $ReferenceDialog.confirmation(stocklist_command, update_stocklist, stocklist_action);

        else if (command == 'service:groupstocklist')
            $ReferenceDialog.confirmation(stocklist_command, update_group_stocklist, stocklist_action, null, null, keywords['group stocklist']);
    });

    $("button[id^='action']", this).click(function(e) {
        var ob = $(this);
        var command = ob.attr('id');

        $onControlPanelClick($("#actions-dropdown"));

        if (command == 'action:set-unread')
            $ProvisionReviewDialog.set_unread(ob, 1);

        else if (command == 'action:set-read')
            $ProvisionReviewDialog.set_read(ob, '', 1);

        else if (command == 'action:set-all-read')
            $ProvisionReviewDialog.set_read(ob, 'all', 1);

        else if (command == 'action:print-order')
            $ProvisionReviewDialog.print_order(ob);
    });

    $("button[id^='with-links-button']", this).click(function(e) {
        var ob = $(this);
        var id = ob.attr('id').split(':')[1];
        var parent = ob.parent();

        //alert(id);

        var control = $("#"+id, parent.parent());

        if (is_exist(control)) {
            var x = $("input[id='with-links-input:"+id+"']", parent);

            if (is_exist(x)) {
                var v = x.val();
                var pages = $("select[id='with-links-pages:"+id+"']", parent);

                if (!is_empty(v)) {
                    var page = pages.val() || 'provision';
                    var link = '<a class=with-links-link target=_blank href=/'+page+'?_id='+v+'>'+v+'</a>';
                    var value = control.val()+' '+link;
                    control.val(value);
                }
            }
        }

        //console.log(id, parent, control, x);

        e.stopPropagation();
    });

    // ------------------------
    // Checked Reviwers actions
    // ------------------------

    $("input[id^='reviewers-check-all']").on('change', function(e) {
        var checked = $(this).prop('checked') ? true : false;
        $ProvisionCheckedReviewersDialog.activate(checked);
    });

    $("li[name^='cid:']").on('click', $("#checked-reviewers-left"), function(e) {
        $ProvisionCheckedReviewersDialog.left($(this), false);
    });

    $("li[name^='cid:']").on('click', $("#checked-reviewers-right"), function(e) {
        $ProvisionCheckedReviewersDialog.right($(this), false);
    });

    $("#checked-reviewers-include").click(function(e) {
        $ProvisionCheckedReviewersDialog.insert($(this));
    });

    $("#checked-reviewers-exclude").click(function(e) {
        $ProvisionCheckedReviewersDialog.remove($(this));
    });

    // -------------
    // Resize window
    // -------------

    $(window).on("resize", function(e) {
        resize(e);
    });

    $(window).scroll(function(e){});

    // --------
    // Keyboard
    // --------

    $(window).keydown(function(e) {
        if ($ConfirmDialog.is_focused() || $NotificationDialog.is_focused())
            return;

        if ($ProvisionSelectorDialog.is_focused() || is_search_focused || is_input_focused)
            return;

        if (is_show_error)
            return;

        // REFERENCE ACTIONS

        if (e.keyCode==13) {                                     // Enter
            if ($ReferenceDialog.is_focused())
                $ReferenceDialog.onEnter();
            else
                $PageLoader.activate($LineSelector.get_current());
        }

        if (e.keyCode==27) {                                     // Esc
            $_escape();
        }

        if ($BaseDialog.is_focused() || $ReferenceDialog.is_focused()) {
            //alert('$BaseDialog.is_focused'+':'+$BaseDialog.is_focused());
            return;
        }

        var exit = false;

        if (e.shiftKey && e.keyCode==76) {                       // Shift-L
            $ProvisionServiceDialog.upload();
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==73) {                  // Shift-I
            $ProvisionSelectorDialog.create('order');
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==85) {                  // Shift-U
            $ProvisionSelectorDialog.update('order');
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==68) {                  // Shift-D
            $ProvisionSelectorDialog.delete('order');
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==84) {                  // Shift-T
            $ProvisionSelectorDialog.clone('order');
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==70) {                  // Shift-F
            if (IsAdmin) $ProvisionServiceDialog.download();
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==71) {                  // Shift-G
            if (IsAdmin) $ProvisionServiceDialog.deleteOrders();
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==72) {                  // Shift-H
            $ProvisionServiceDialog.sendApproval();
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==74) {                  // Shift-J
            if (IsAdmin) $ProvisionServiceDialog.clearHistory();
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==81) {                  // Shift-Q
            MakeAction($("#REVIEW_CONFIRM"));
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==87) {                  // Shift-W
            MakeAction($("#REVIEW_ACCEPT"));
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==69) {                  // Shift-E
            MakeAction($("#REVIEW_REJECT"));
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==188) {                 // Shift-<
            $ProvisionReviewDialog.set_unread(null, 1);
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==190) {                 // Shift->
            $ProvisionReviewDialog.set_read(null, '', 1);
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==191) {                 // Shift-/
            $ProvisionReviewDialog.set_read(null, 'all', 1);
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==80) {                  // Shift-P
            $ProvisionReviewDialog.print_order();
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==77) {                  // Shift-M
            $ProvisionOrderHistoryDialog.open(null, 'order');
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==78) {                  // Shift-N
            $ProvisionCheckedReviewersDialog.open(null, 'order');
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==66) {                  // Shift-B
            $ProvisionDecreeDialog.open(null, 'decree');
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==79) {                  // Shift-O
            $SidebarDialog.activate($(this),
                {'callback':$SidebarControl.onNavigatorClick, 'force':0});
            exit = true;
        }

        // REFERENCEs

        else if (e.shiftKey && e.keyCode==49)                    // Shift-1
            $ReferenceDialog.confirmation(stocklist_command, update_stocklist, stocklist_action);

        else if (e.shiftKey && e.keyCode==50) {                  // Shift-2
            $SidebarControl.onActivatePointer($(this), 
                {'callback':$SidebarControl.onNavigatorClick, 'force':0});
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==51)                    // Shift-3
            $ReferenceDialog.confirmation(stocklist_command, update_group_stocklist, stocklist_action, null, null, keywords['group stocklist']);

        //alert(e.ctrlKey+':'+e.shiftKey+':'+e.altKey+':'+e.keyCode);

        if (exit) {
            e.preventDefault();
            return false;
        }
    });
});

function page_is_focused(e) {
    if (e.shiftKey)
        return is_input_focused || $ReferenceDialog.is_focused();
    return false;
}

function search_is_empty() {
    return is_empty($("#searched").val()) ? true : false;
}

function resize(e) {
    //alert('resize');

    if (is_null(e) || e.target === window) {
        $onInfoContainerChanged('resize');
        $ProvisionSelectorDialog.resize();
        $ReferenceDialog.resize();
    }
}

function $_activate(check) {
    if (!is_webkit)
        return null;

    var id = 'selected_data_menu_id';
    var tab = $("#"+id);
    var exists = is_exist(tab) && tab.attr('id') == id ? 1 : 0;
    if (check) {
        $("#window_scroll").each(function() { $(this).val(page_scroll_top); });
        return exists;
    }
    return exists ? tab : null;
}

function $_escape() {
    //alert('27');
    reviewer_toggle(0, null);
}

function $_show_page(mode) {
    $ShowPage(mode);
}

// =======
// STARTER
// =======

$(function() 
{
    if (IsTrace)
        alert('Document Ready (provision)');

    IsShowLoader = 0;
    //
    // IsActiveScroller=1 works together with ::-webkit-scrollbar { width:0px; } in style.web.css
    // Look settings at: base.html
    //
    // IsActiveScroller = (IsMSIE || isIE || isFirefox) ? 0 : 1; 

    if (IsTrace)
        alert('IsActiveScroller:'+IsActiveScroller+', BrowserDetect.browser:'+BrowserDetect.browser);

    default_screen_max = $_width('screen-max');

    $("#search-context").attr('placeholder', placeholder);

    IsOptionRowspan = 0;
    IsOptionContainerChanged = default_screen_max <= 800 && !$_mobile() ? 1 : 0;
    IsOptionCheckBigScreen = default_screen_max > 1600 ? 0 : 1;

    var tab = $_activate(0);
    selected_data_menu_id = !is_null(tab) ? tab.val() : '';

    window_scroll = int($("#window_scroll").val() || 0);

    resize();

    $SidebarDialog.init();

    try {
        $_init();
    }
    catch(e) {}
});
