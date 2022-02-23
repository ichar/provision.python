// *************************************
// BANKPERSO PAGE DECLARATION: /log.html
// -------------------------------------
// Version: 1.10
// Date: 28-07-2017

default_submit_mode = 2;
default_action      = '100';
default_log_action  = '101';
default_input_name  = 'user_id';

LINE    = 'admin';
SUBLINE = '';

// Flag for 'input' keyboards
var is_input_focused = false;

// ----------------------
// Dialog Action Handlers
// ----------------------

function sidebar_callback() {}

function subline_refresh(filename) {
    $(".filename").each(function() { 
        $(this).html(filename);
    });
}

function message_sent(x, errors) {
    if (!is_null(errors) && errors.length > 0) {
        var msg = errors.join('<br>');
        $ShowError(msg, true, true, false);
        return;
    }

    $NotificationDialog.open(keywords['Message:Action was done successfully']);
}

// --------------
// Page Functions
// --------------

function $Init() {
    $SidebarControl.init(sidebar_callback, []);

    SelectedReset();

    $LineSelector.init();
    $ResetPageState();
    $ShowMenu(null);

    // ------------------------
    // Start default log action
    // ------------------------

    interrupt(true, 1);
}

function $Confirm(mode, ob) {
    $ConfirmDialog.close();

    if (mode == 1)
        switch (confirm_action) {
            case 'photo:remove':
                var user_id = SelectedGetItem(LINE, 'id');
                var params = {'command':'delete_phote'};
                $web_logging('102', function(x) { $updateUserPhoto(x['photo']); }, params);
                break;
        }
    else
        switch (confirm_action) {
            case 'config:changed':
                break;
        }

    confirm_action = '';
}

function $Notification(mode, ob) {
    $NotificationDialog.close();
}

function $ResetPageState() {
    $ProfileClients.init();
    $ProfileClients.update($("#profile_clients").val());
}

function $ShowMenu(id) {
    selected_data_menu_id = id;
}

function $onRegisterFormSubmit(frm) {
    return true;
}

function $onUserFormSubmit(frm) {
    var ob = $("#item-clients-all");
    $SidebarControl.onBeforeSubmit();
    $("#profile_clients").val(!ob.prop('checked') ? $ProfileClients.getItems().join(DEFAULT_HTML_SPLITTER) : '');
    return true;
}

function $onPaginationFormSubmit(frm) {
    //alert(frm.id+':'+frm.action);
    return true;
}

function $onFilterFormSubmit(frm) {
    /*
    var action = frm.action.split('?');
    var qs = action.length > 1 ? '?'+action[1] : '';
    frm.action = (action[0].indexOf('admin') > 1 ? 'admin/' : '') + 'index' + qs;
    alert(frm.id+':'+frm.action);
    */
    return true;
}

// ===========================
// Dialog windows declarations
// ===========================

function MakeFilterSubmit(mode, page) {
    /*
    alert(baseURI);
    $("#filter-form").attr("action", baseURI);
    */
    switch (mode) {

        // -------------
        // Submit modes:
        // -------------

        case 0:
            break;

        // ---------------------------
        // LineSelector Handler submit
        // ---------------------------

        case 9:
            $("#user_id").each(function() { $(this).val(0); });
    }

    $ResetLogPage();
    
    $setPaginationFormSubmit(page);
    $onParentFormSubmit('filter-form');
}

// ====================
// Page Event Listeners
// ====================

jQuery(function($) 
{
    $("td.column").click(function(e) {
        e.preventDefault();
    });

    // --------------
    // Line selection
    // --------------

    $(".line").click(function(e) {
        $LineSelector.onRefresh($(this));
        $ProfileClients.enable();
    });

    // -----------
    // User's Form
    // -----------

    $("input", "#user-form").on('change keyup paste', function(e) {
        $setUserFormSubmit(0);
    });

    $("select").on('change', function(e) {
        $setUserFormSubmit(0);
    });

    // -----------------------
    // User's Profile. Clients
    // -----------------------

    $("a[class^='profile']").on('click', function(e) {
        $ProfileClients.click($(this));
    });

    $("input[id^='item-clients-all']").on('change', function(e) {
        var checked = $(this).prop('checked') ? true : false;
        $ProfileClients.activate(checked);
    });

    $("li[name^='cid:']").on('click', $("#profile-clients-left"), function(e) {
        var ob = $(this);
        var parent = ob.parents("*[class^='profile-data-panel']").first();
        var disabled = parent.hasClass('disabled');

        if (disabled)
            return;
        
        //alert(ob.attr('id')+':'+parent.attr('id')+':'+disabled);

        $ProfileClients.setLeft(ob, false);
    });

    $("li[name^='cid:']").on('click', $("#profile-clients-right"), function(e) {
        var ob = $(this);
        var parent = ob.parents("*[class^='profile-data-panel']").first();
        var disabled = parent.hasClass('disabled');

        if (disabled)
            return;
        
        //alert(ob.attr('id')+':'+parent.attr('id')+':'+disabled);

        $ProfileClients.setRight(ob, false);
    });

    $("#profile-clients-include").click(function(e) {
        var ob = $(this);
        var disabled = ob.hasClass('disabled');

        if (disabled)
            return;
        
        //alert(ob.prop('tagName'));

        $ProfileClients.onAddClientProfileItem(ob);
    });

    $("#profile-clients-exclude").click(function(e) {
        var ob = $(this);
        var disabled = ob.hasClass('disabled');

        if (disabled)
            return;

        $ProfileClients.onRemoveClientProfileItem(ob);
    });

    // -------------
    // Photo actions
    // -------------

    $("#photo_delete").click(function(e) {
        var ob = $(this);
        confirm_action = 'photo:remove';
        $ConfirmDialog.open(keywords['Command:Photo item removing. Continue?']);
    });

    // --------
    // Settings
    // --------

    $("input.settings").on('change', $(".profile-settings-item"), function(e) {
        $setSettings();
    });

    // ----------
    // Privileges
    // ----------

    $(".privileges", "#profile-privileges").on('change', $(".profile-privileges-item"), function(e) {
        //var ob = $(this);
        //alert(ob.attr('id')+':'+ob.val());
        $setPrivileges();
    });

    // --------------------
    // Right side Data menu
    // --------------------

    $(".btn-info").click(function(e) {
        $SidebarControl.onBeforeSubmit();
    });

    $("#add").click(function(e) {
        $("input[name^='command']").val('add');
        var selected_item = SelectedGetItem(LINE, 'ob');
        if (selected_item != null)
            $onToggleSelectedClass(LINE, selected_item, 'remove');

        $onToggleSelectedClass(LINE, $(this), 'clean');
        $cleanUserForm();

        $ProfileClients.reset();
        $ProfileClients.activate(true);
    });

    $("#delete").click(function(e) {
        $("input[name^='command']").val('delete');
        $onParentFormSubmit('command-form');
    });

    // ------------------------
    // Control Panel Menu items
    // ------------------------

    $("button[id^='admin']", this).click(function(e) {
        var ob = $(this);
        var command = ob.attr('id');

        $onControlPanelClick($("#admin-panel-dropdown"));

        if (command == 'admin:message') {
            $AdminServiceDialog.open(ob, 'message');
            return;
        }
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

    // -------------
    // Resize window
    // -------------

    // --------
    // Keyboard
    // --------

    $(window).keydown(function(e) {
        if ($ConfirmDialog.is_focused() || $NotificationDialog.is_focused())
            return;

        if (is_show_error)
            return;

        if (e.keyCode==13) {                                     // Enter
        }
        
        if (e.keyCode==27) {                                     // Esc
        }

        if ($BaseDialog.is_focused() || is_search_focused || is_input_focused)
            return;

        var exit = false;

        if (e.shiftKey && e.keyCode==77) {                       // Shift-M
            $AdminServiceDialog.open(null, 'message');
            exit = true;
        }

        //alert(e.ctrlKey+':'+e.shiftKey+':'+e.altKey+':'+e.keyCode);

        if (exit) {
            e.preventDefault();
            return false;
        }
    });
});

function readFile(e) {
    $ProfileClients.updatePhoto(e);
}

function page_is_focused(e) {
    if (e.shiftKey)
        return is_input_focused;
    return false;
}

// =======
// STARTER
// =======

$(function() 
{
    if (IsTrace)
        alert('Document Ready (admin)');

    IsActiveScroller = 0;

    current_context = 'admin';
    isKeyboardDisabled = false;

    $("#search-context").attr('placeholder', keywords['Admin Find']+'...');

    //document.oncontextmenu = function() { return false; };

    $_init();
});
