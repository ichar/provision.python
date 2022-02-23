// *****************************************
// BANKPERSO PAGE DECLARATION: /bankperso.js
// -----------------------------------------
// Version: 1.50
// Date: 08-12-2017

default_submit_mode = 2;
default_action      = '300';
default_log_action  = '301';
default_input_name  = 'file_id';
default_menu_item   = 'data-menu-batches';

LINE    = 'order';
SUBLINE = 'batch';

var batch_can_be_activated = 0;
var postonline_path = null;

// ----------------------
// Dialog Action Handlers
// ----------------------

function sidebar_callback() {
    $onInfoContainerChanged();
}

function subline_refresh(filename) {
    $(".filename").each(function() { 
        $(this).html(filename);
    });
}

function log_callback(current_action, data, props) {
    batch_can_be_activated = 'activate' in props ? props['activate'] : 0;
}

function indigo(s) {
    $NotificationDialog.open('<img class="indigo_image" src="'+s+'" title="Indigo Design" alt>', 800, 620, keywords['Image view']);
}

// --------------
// Page Functions
// --------------

function $Init() {
    $SidebarControl.init(sidebar_callback, ['type', 'status', 'batchtype']);

    page_sort_title = $("#sort_icon").attr('title');

    SelectedReset();

    $LineSelector.init();
    //$SublineSelector.init();
    $ShowMenu(default_menu_item);
    $TabSelector.init();

    // ------------------------
    // Start default log action
    // ------------------------

    interrupt(true, 1);
}

function $Confirm(mode, ob) {
    $ConfirmDialog.close();

    function _check(x) { 
        var errors = x['errors']; 

        //alert(errors.length);

        if (errors.length > 0) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
        }
        else {
            $NotificationDialog.open(keywords['Message:Request sent successfully']);
        }
    }

    switch (mode) {
        case 0:
            break;
        case 1:
            if (confirm_action == 'activate') {
                var ids = SelectedGetItem(SUBLINE, 'id');

                $("input[name='selected_batch_ids']").each(function() { $(this).val(ids); });
                $("#command").val('admin:'+confirm_action);

                $onParentFormSubmit();
            }
            else if (confirm_action == 'materials') {
                $Handle('310', _check);
            }
            else if (confirm_action == 'data-menu-exchangelog') {
                var ob = $("#"+confirm_action);

                $TabSelector.onClick(ob);
            }
            else if (confirm_action == 'print_postonline') {
                var left = 80;
                var top = 80;
                var height = 800;

                for (var i=0; i < postonline_path.length; i++) {
                    var params = 'left='+left.toString()+',top='+top.toString()+',width=800,height='+height.toString()+',resizable,scrollbars=yes'; //fullscreen=yes,
                    
                    window.open(postonline_path[i], '_blank', params);

                    left += 40;
                    top += 20;
                    height -= 60;
                }
            }
    }
}

function $Notification(mode, ob) {
    $NotificationDialog.close();

    if (confirm_action == 'materials') {
        var ob = $LineSelector.get_current();
        $onToggleSelectedClass(LINE, ob, 'submit', null);
    }
}

function $ShowMenu(id, status, path) {

    // -----------------------------------------
    // Show (open) selected DataMenu item (Tabs)
    // -----------------------------------------

    var batches = $("#subline-content");
    var logs = $("#logs-content");
    var cardholders = $("#cardholders-content");
    var body = $("#body-content");
    var processerrmsg = $("#processerrmsg-content");
    var persolog = $("#persolog-content");
    var sdclog = $("#sdclog-content");
    var exchangelog = $("#exchangelog-content");
    var indigo = $("#indigo-content");

    var tab = $("#"+id);

    if (selected_data_menu)
        selected_data_menu.removeClass('selected');

    selected_data_menu = tab;
    //$("#data-content").scrollTop(0);

    batches.hide();
    logs.hide();
    cardholders.hide();
    body.hide();
    processerrmsg.hide();
    persolog.hide();
    sdclog.hide();
    exchangelog.hide();
    indigo.hide();

    if (id == 'data-menu-batches')
        batches.show();
    else if (id == 'data-menu-logs')
        logs.show();
    else if (id == 'data-menu-cardholders')
        cardholders.show();
    else if (id == 'data-menu-body')
        body.show();
    else if (id == 'data-menu-processerrmsg')
        processerrmsg.show();
    else if (id == 'data-menu-persolog')
        persolog.show();
    else if (id == 'data-menu-sdclog')
        sdclog.show();
    else if (id == 'data-menu-exchangelog')
        exchangelog.show();
    else if (id == 'data-menu-indigo')
        indigo.show();

    if (id == default_menu_item)
        $SublineSelector.init();
    else
        $TablineSelector.init(tab);

    if (id == default_menu_item && SelectedGetItem(SUBLINE, 'id'))
        $ActivateInfoData(1);
    else
        $ActivateInfoData(0);

    selected_data_menu.addClass('selected');
    selected_data_menu_id = id;
}

function $onPaginationFormSubmit(frm) {
    return true;
}

function $onFilterFormSubmit(frm) {
    return true;
}

function $onInfoContainerChanged() {
    //alert($_width('screen-min')-$("#sidebarFrame").width()+':'+$("#line-table").width());
}

function $onTabSelect(ob) {
    var id = ob.attr("id");
    var action = 
        id == 'data-menu-logs' ? '302' : (
        id == 'data-menu-cardholders' ? '303' : (
        id == 'data-menu-body' ? '304' : (
        id == 'data-menu-processerrmsg' ? '305' : (
        id == 'data-menu-persolog' ? '306' : (
        id == 'data-menu-sdclog' ? '307' : (
        id == 'data-menu-exchangelog' ? '308' : (
        id == 'data-menu-indigo' ? '313' : null
        )))))));

    selected_menu_action = action;

    if (action != null) {
        $InProgress(ob, 1);
        $Go(action);
    }
    else if (default_submit_mode > 1) {
        selected_menu_action = default_log_action;
        $InProgress(ob, 1);
        $Go(default_action);
    }
    else
        $ShowMenu(id);

    return true;
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
        //  0 - changed client
        //  1 - changed file type
        //  2 - changed status
        //  3 - changed batchtype
        //  4 - changed date from
        //  5 - changed date to
        //  6 - changed state

        case 0:
            $("#batch_id").each(function() { $(this).val(0); });
            $("#type").val(0);
        case 1:
            $("#status_file_id").each(function() { $(this).val(0); });
            $("#status_batch_id").each(function() { $(this).val(0); });
            //$("#status").val(0);
            //$("#batchtype").val(0);
        case 2:
        case 3:
        case 4:
        case 5:
            break;

        // ---------------------------
        // LineSelector Handler submit
        // ---------------------------

        case 9:
            $("#file_id").each(function() { $(this).val(0); });
            $("#batch_id").each(function() { $(this).val(0); });
            $("#status_file_id").each(function() { $(this).val(0); });
            $("#status_batch_id").each(function() { $(this).val(0); });
    }

    $ResetLogPage();

    $setPaginationFormSubmit(page);
    $onParentFormSubmit('filter-form');
}

function makeTodayRequest() {
    var date = new Date();
    var now = date.getToday();

    $_set_body_value('order-date-from', now);
    $onParentFormSubmit('filter-form');
}

// =========================
// Custom routine assigments
// =========================

function showActiveBatches(ob) {
    var id = ob.attr("id");
    var action = default_action;
    var status = '';

    switch (id) {
        case 'batches-tab-active':
            status = 1;
            break;
        case 'batches-tab-all':
            break;
        default:
            return;
    }

    var parent = $("#batches-tabs");
    var selected_tab = $("li[class~='selected']", parent);

    selected_tab.removeClass('selected');
    ob.parent().addClass('selected');

    $_set_body_value('batchstatus', status);

    $InProgress(ob, 1);
    $Go(action);
}

function activateBatch() {
    var area = $("#ex_printable_area");

    confirm_action = 'activate';
    
    printBankpersoTZ(area);

    $InProgress(null);

    if (batch_can_be_activated !== 1)
        return;

    $ConfirmDialog.open(keywords['Command:Activate selected batch']);
}

function activateMaterials(x) {
    var data = x['data'];
    var props = x['props'];
    var errors = x['errors'];

    if (errors.length > 0) {
        var msg = errors.join('<br>');
        $ShowError(msg, true, true, false);
        return;
    }

    confirm_action = 'materials';

    printBankpersoMaterials(data, props);

    if (props['send'])
        $ConfirmDialog.open(keywords['Command:Send request to the warehouse'], 500);
}

function activateContainerList(x) {
    var data = x['data'];
    var props = x['props'];
    var errors = x['errors'];

    $InProgress(null);

    if (errors.length > 0) {
        var msg = errors.join('<br>');
        $ShowError(msg, true, true, false);
        return;
    }

    if (is_empty(data)) {
        var msg = keywords['Warning:No report data'];
        $ShowError(msg, true, true, false);
        return;
    }

    printBankpersoContainerList(data, props);
}

// ====================
// Page Event Listeners
// ====================

jQuery(function($) 
{
    // --------------
    // Line selection
    // --------------

    $(".line").click(function(e) {
        if (is_show_error)
            return;

        $LineSelector.onRefresh($(this));
    });

    // -----------------
    // SubLine selection
    // -----------------

    $("#subline-content").on('click', '.subline', function(e) {
        if (is_show_error)
            return;

        $SublineSelector.onRefresh($(this));
    });

    // ---------------------
    // Data Section progress
    // ---------------------

    $("#data-section").on('click', '.column', function(e) {
        var ob = $(this);
        var parent = ob.parents("*[class*='line']").first();
        if (!is_null(parent) && !parent.hasClass("tabline") && !ob.hasClass("header"))
            $InProgress(ob, 1);
    });

    // -----------------
    // Tabline selection
    // -----------------

    function $openRecordNode(ob) {
        is_scroll_top = true;
        $Handle('304', null, ob.attr('id'));
    }

    $(".view-lines").on('click', '.tabline', function(e) {
        is_noprogress = true;

        $DblClickAction.click(
            function(ob) {
                is_noprogress = false;
                $TablineSelector.onRefresh(ob);
            },
            function(ob) {
                var parent = ob.parents("*[class^='view-container']").first();
                if (parent.attr('id') == 'cardholders-container' && !is_null($("#data-menu-body").html())) {
                    $openRecordNode(ob);
                }
            },
            $(this)
        );
    })
    .on("dblclick", function(e){
        e.preventDefault();
    });

    // ------------------------
    // Control Panel Menu items
    // ------------------------

    $("#status-confirm-container").on('click', '.change-status-item', function(e) {
        $StatusChangeDialog.toggle($(this));
    });

    $("button[id^='admin']", this).click(function(e) {
        var ob = $(this);
        var command = ob.attr('id');

        $onControlPanelClick($("#admin-panel-dropdown"));

        if (['admin:create','admin:delete'].indexOf(command) > -1) {
            $OrderDialog.open(command);
            return;
        }
        if (['admin:change-filestatus','admin:change-batchstatus'].indexOf(command) > -1) {
            $StatusChangeDialog.confirmation(command);
            return;
        }
        if (['admin:logsearch'].indexOf(command) > -1) {
            $BankpersoSubmitDialog.open('logsearch');
            return;
        }
        if (['admin:tagsearch'].indexOf(command) > -1) {
            $BankpersoSubmitDialog.open('tagsearch');
            return;
        }

        $onToggleSelectedClass(LINE, null, 'submit', command, true);
    });

    $("button[id^='service']", this).click(function(e) {
        var ob = $(this);
        var command = ob.attr('id');

        $onControlPanelClick($("#services-dropdown"));
        
        if (command == 'service:group-container') {
            $PersoButton(ob);
            return;
        }

        $("#command").val(command);
        $onParentFormSubmit('filter-form');
        e.preventDefault();
    });

    $("button[id^='action']", this).click(function(e) {
        var ob = $(this);
        var command = ob.attr('id');

        $onControlPanelClick($("#actions-dropdown"));
        
        if (command == 'action:changedate') {
            $BankpersoSubmitDialog.open('changedate');
            return;
        }
        if (command == 'action:changeaddress') {
            $BankpersoSubmitDialog.open('changeaddress');
            return;
        }
        if (command == 'action:repeatunloadedreport') {
            $OrderDialog.open('report of');
            return;
        }
    });

    // --------------------------
    // Bankperso Operator Buttons
    // --------------------------

    function $PersoButton(ob) {
        var x = ob.attr("id").split('_');
        var id = x.length >= 2 ? x[1] : x[0];

        $InProgress(ob, 1);

        switch (id) {
            case 'TZ':
                activateBatch();
                break;
            case 'MATERIALS':
                $calculateMaterials();
                break;
            case 'CONTAINERLIST':
                $calculateContainerList();
                break;
            case 'DOCUMENTS':
                $ShowProcessInfo.refresh(ob);
                break;
            case 'service:group-container':
                $calculateGroupContainerList();
                break;
        }
    }

    function $calculateMaterials() {
        $Handle('309', function(x) { activateMaterials(x); });
    }

    function $calculateContainerList() {
        $Handle('311', function(x) { activateContainerList(x); });
    }

    function $calculateGroupContainerList() {
        var params = $LineSelector.getSelectedItems(1).join(':');
        $Handle('312', function(x) { activateContainerList(x); }, params);
    }

    $("button[id^='PERSO']", this).click(function(e) {
        $PersoButton($(this));
    });

    // --------------
    // Tabs Data menu
    // --------------

    $("div[id^='data-menu']", this).click(function(e) {
        var ob = $(this);
        var id = ob.attr('id');

        if (id == 'data-menu-exchangelog') {
            confirm_action = id;
            $ConfirmDialog.open(keywords['Warning:This operation may take a long time'], 600);
            return;
        }

        $TabSelector.onClick(ob);
    });

    // -------------
    // Resize window
    // -------------

    $(window).on("resize", function() {
        $PageScroller.reset(false);
    });

    $(window).scroll(function(e){
        $PageScroller.checkPosition(0);
    });

    // ---------------------
    // Batches Tab selection
    // ---------------------

    $("a.batches-tab", this).click(function(e) {
        showActiveBatches($(this));
        e.preventDefault();
    });

    // --------
    // Keyboard
    // --------

    $(window).keydown(function(e) {
        if ($ConfirmDialog.is_focused() || $NotificationDialog.is_focused())
            return;

        if (is_show_error)
            return;

        if (e.keyCode==13) {                                     // Enter
            // ------------------------------------
            // Bankpesro Submit Dialog Class Events
            // ------------------------------------
            if ($BankpersoSubmitDialog.is_focused()) {
                $BankpersoSubmitDialog.confirmed();
                e.preventDefault();
                return false;
            }
        }

        if ($BankpersoSubmitDialog.is_focused() || is_search_focused)
            return;

        var exit = false;

        //alert(e.ctrlKey+':'+e.shiftKey+':'+e.altKey+':'+e.keyCode);

        if (e.shiftKey && e.keyCode==80) {                       // Shift-P
            activateBatch();
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==76) {                  // Shift-L
            $BankpersoSubmitDialog.open('logsearch');
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==81) {                  // Shift-Q
            $BankpersoSubmitDialog.open('tagsearch');
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==87) {                  // Shift-W
            $BankpersoSubmitDialog.open('changedate');
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==65) {                  // Shift-A
            $BankpersoSubmitDialog.open('changeaddress');
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==84) {                  // Shift-T
            makeTodayRequest();
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==68) {                  // Shift-D
            $OrderDialog.open('admin:delete');
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==70) {                  // Shift-F
            $StatusChangeDialog.confirmation('admin:change-filestatus');
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==66) {                  // Shift-B
            $StatusChangeDialog.confirmation('admin:change-batchstatus'); 
            exit = true;
        }

        if (exit) {
            e.preventDefault();
            return false;
        }
    });
});

function page_is_focused(e) {
    return $BankpersoSubmitDialog.is_focused();
}

// =======
// STARTER
// =======

$(function() 
{
    if (IsTrace)
        alert('Document Ready (bankperso)');

    current_context = 'bankperso';

    $("#search-context").attr("placeholder", "Найти (имя файла, ТЗ)...");
    //$("#batchtype").css("width", $("#status").width()+"px");
    //$("#batchtype").width($("#status").width());

    IsActiveScroller = 0;

    $_init();
});
