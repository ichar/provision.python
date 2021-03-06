// *************************************************
// CONFIGURATOR PAGE DECLARATION: /configurator.html
// -------------------------------------------------
// Version: 1.40
// Date: 05-09-2017

default_submit_mode = 2;
default_action      = '600';
default_log_action  = '601';
default_input_name  = 'file_id';
default_menu_item   = 'data-menu-batches';

LINE    = 'file';
SUBLINE = 'batch';

// ----------------------
// Dialog Action Handlers
// ----------------------

function sidebar_callback() {
    $onInfoContainerChanged();
}

function sidebar_toggle() {
    $onClickTreeView(1);
}

function subline_refresh(filename) {
    $(".filename").each(function() { 
        $(this).html(filename);
    });
}

function log_callback(action, data, props) {
    // ---------------------------------------------------------
    // Set callback to handle add-ons such as LogPage refreshing
    // ---------------------------------------------------------
    // Used for sublines.

    if (action == default_action)
        $ConfigSelector.reset();

    $ConfigSelector.toggle($ActiveSelector.get_current());
}

function config_callback_setup(id) {
    // ----------------------------------------------------
    // Set current control to manage inside $ConfigSelector
    // Set callback to activate current object
    // ----------------------------------------------------
    // Used for current object setup given from the $ActiveSelector.
    // Depends on selected Tab item.

    //$ConfigSelector.reset();
    $ConfigSelector.set_current($ActiveSelector.get_current());
    $ConfigSelector.set_callback(function(x) { $ActiveSelector.onRefresh(x); });
}

// --------------
// Page Functions
// --------------

function $Init() {
    $SidebarControl.init(sidebar_callback, ['filetype', 'batchtype']);

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

    if (mode == 1)
        switch (confirm_action) {
            case 'admin:removescenario':
                $ConfigScenarioDialog.confirmed('removescenario');
                break;
            case 'reference:remove':
                $ReferenceDialog.confirmed('remove');
                break;
            case 'config:changed':
                $ConfigSelector.confirmed('continue');
                break;
            case 'config:remove':
                $ConfigSelector.confirmed('remove');
                break;
        }
    else
        switch (confirm_action) {
            case 'config:changed':
                //$ConfigSelector.reset();
                break;
        }

    confirm_action = '';
}

function $Notification(mode, ob) {
    $NotificationDialog.close();

    switch (confirm_action) {
        case 'reference:refresh':
            interrupt(true, 2, $ReferenceDialog.timeout, null, null, 0);
            break;
        case 'config:refresh':
            //$ShowOnStartup();
            break;
        case 'config:remove':
            //interrupt(true, 3, $ConfigSelector.timeout, null, null, 0);
            //$LineSelector.onReset();
            break;
    }
}

function $ShowMenu(id) {
    //
    // Show (open) selected DataMenu item (Tabs)
    //
    var batches = $("#subline-content");
    var processes = $("#processes-content");
    var opers = $("#opers-content");
    var operparams = $("#operparams-content");
    var filters = $("#filters-content");
    var tags = $("#tags-content");
    var tagvalues = $("#tagvalues-content");
    var tzs = $("#tzs-content");
    var erpcodes = $("#erpcodes-content");
    var materials = $("#materials-content");
    var posts = $("#posts-content");
    var tagopers = $("#tagopers-content");
    var tagoperparams = $("#tagoperparams-content");
    var processparams = $("#processparams-content");

    var tab = $("#"+id);

    if (selected_data_menu)
        selected_data_menu.removeClass('selected');

    selected_data_menu = tab;

    batches.hide();
    processes.hide();
    opers.hide();
    operparams.hide();
    filters.hide();
    tags.hide();
    tagvalues.hide();
    tzs.hide();
    erpcodes.hide();
    materials.hide();
    posts.hide();
    tagopers.hide();
    tagoperparams.hide();
    processparams.hide();

    if (id == 'data-menu-batches')
        batches.show();
    else if (id == 'data-menu-processes')
        processes.show();
    else if (id == 'data-menu-opers')
        opers.show();
    else if (id == 'data-menu-operparams')
        operparams.show();
    else if (id == 'data-menu-filters')
        filters.show();
    else if (id == 'data-menu-tags')
        tags.show();
    else if (id == 'data-menu-tagvalues')
        tagvalues.show();
    else if (id == 'data-menu-tzs')
        tzs.show();
    else if (id == 'data-menu-erpcodes')
        erpcodes.show();
    else if (id == 'data-menu-materials')
        materials.show();
    else if (id == 'data-menu-posts')
        posts.show();
    else if (id == 'data-menu-tagopers')
        tagopers.show();
    else if (id == 'data-menu-tagoperparams')
        tagoperparams.show();
    else if (id == 'data-menu-processparams')
        processparams.show();

    $ConfigSelector.init(tab);

    if (id == default_menu_item)
        $SublineSelector.init();
    else
        $TablineSelector.init(tab);

    config_callback_setup(id);

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
    var id = ob.attr('id');
    var action = 
        id == 'data-menu-processes' ? '602' : (
        id == 'data-menu-opers' ? '603' : (
        id == 'data-menu-operparams' ? '604' : (
        id == 'data-menu-filters' ? '605' : (
        id == 'data-menu-tags' ? '606' : (
        id == 'data-menu-tagvalues' ? '607' : (
        id == 'data-menu-tzs' ? '608' : (
        id == 'data-menu-erpcodes' ? '609' : (
        id == 'data-menu-materials' ? '610' : (
        id == 'data-menu-posts' ? '611' : (
        id == 'data-menu-processparams' ? '612' : (
        id == 'data-menu-tagopers' ? '613' : (
        id == 'data-menu-tagoperparams' ? '614' : null
        ))))))))))));

    selected_menu_action = action;

    //config_callback_setup(id);

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

function $onClickTreeView(force) {
    if (force && !treeview_state)
        return;

    var parent = $("#tab-content");
    var obs = [$("#data-menu-processes"), 
               $("#data-menu-opers"), 
               $("#data-menu-operparams"), 
               $("#data-menu-posts"), 
               $("#data-menu-tags"), 
               $("#data-menu-tagvalues"),
               $("#data-menu-tzs"),
               $("#data-menu-erpcodes"),
               $("#data-menu-materials"),
               $("#data-menu-tagopers"),
               $("#data-menu-tagoperparams"),
               $("#data-menu-processparams"),
               $("#data-menu-filters")
               ];
    var duration = 500;

    var processes = {
        ob       : obs[0],
        width    : obs[0].width(),
        position : {top: "+=34"}
    };
    var opers = {
        ob       : obs[1],
        width    : obs[1].width(),
        position : {top: "+=68", left: "-="+(processes.width+22).toString()}
    };
    var operparams = {
        ob       : obs[2],
        width    : obs[2].width(),
        position : {top: "+=102", left: "-="+(processes.width+22).toString()}
    };
    var posts = {
        ob       : obs[3],
        width    : obs[3].width(),
        position : {top: "+=68"}
    };
    var tags = {
        ob       : obs[4],
        width    : obs[4].width(),
        position : {top: "0", left: "0"}
    };
    var tagvalues = {
        ob       : obs[5],
        width    : obs[5].width(),
        position : {top: "+=34"}
    };
    var tzs = {
        ob       : obs[6],
        width    : obs[6].width(),
        position : {top: "+=68"}
    };
    var erpcodes = {
        ob       : obs[7],
        width    : obs[7].width(),
        position : {top: "+=68"}
    };
    var materials = {
        ob       : obs[8],
        width    : obs[8].width(),
        position : {top: "+=68"}
    };
    var tagopers = {
        ob       : obs[9],
        width    : obs[9].width(),
        position : {top: "+=68"}
    };
    var tagoperparams = {
        ob       : obs[10],
        width    : obs[10].width(),
        position : {top: "+=102"}
    };
    var processparams = {
        ob       : obs[11],
        width    : obs[11].width(),
        position : {top: "+=68"}
    };

    if (treeview_state || force == 1) {
        var x = {top: "0", left: "0"};

        $(".menu").css({"position" : ""}).removeClass('embossed');

        processparams.ob.animate(x, duration, function() {});
        tagoperparams.ob.animate(x, duration, function() {});
        tagopers.ob.animate(x, duration, function() {});
        materials.ob.animate(x, duration, function() {});
        erpcodes.ob.animate(x, duration, function() {});
        tzs.ob.animate(x, duration, function() {});
        tagvalues.ob.animate(x, duration, function() {});
        tags.ob.animate(x, duration, function() {});
        posts.ob.animate(x, duration, function() {});
        operparams.ob.animate(x, duration, function() {});
        opers.ob.animate(x, duration, function() {});
        processes.ob.animate(x, duration, function() {});
        
        //parent.animate({height: "-=102"}, duration, function() {});
        parent.animate({height: "100%"}, duration, function() {});

        treeview_state = 0;
    }
    else if (xround(obs.slice(-1)[0].position().top) > xround(obs[0].position().top))
        return;

    else {
        treeview_state = 1;

        $(".menu").css({"position" : "relative"}).addClass('embossed');

        parent.animate({height: "+=102"}, duration, function() {});

        processes.ob.animate(processes.position, duration, function() {});
        opers.ob.animate(opers.position, duration, function() {});
        operparams.ob.animate(operparams.position, duration, function() {});
        posts.ob.animate(posts.position, duration, function() {});
        tags.ob.animate(tags.position, duration, function() {});
        tagvalues.ob.animate(tagvalues.position, duration, function() {});
        tzs.ob.animate(tzs.position, duration, function() {});
        erpcodes.ob.animate(erpcodes.position, duration, function() {});
        materials.ob.animate(materials.position, duration, function() {});
        tagopers.ob.animate(tagopers.position, duration, function() {});
        tagoperparams.ob.animate(tagoperparams.position, duration, function() {});
        processparams.ob.animate(processparams.position, duration, function() {});
    }
}

// ===========================
// Dialog windows declarations
// ===========================

function MakeFilterSubmit(mode, page) {
    $("#filter-form").attr("action", baseURI);

    //alert('MakeFilterSubmit:'+mode);

    switch (mode) {

        // -------------
        // Submit modes:
        // -------------
        //  0 - changed client
        //  1 - changed file type
        //  2 - changed batch type
        //  3 - changed tag
        //  4 - changed tag value

        case 0:
            $("#batch_id").each(function() { $(this).val(0); });
            $("#filetype").val(0);
        case 1:
            $("#batchtype").val(0);
        case 2:
            $("#tag").val(0);
        case 3:
            $("#tagvalue").val('');
        case 4:
            break;

        // ---------------------------
        // LineSelector Handler submit
        // ---------------------------

        case 9:
            $("#file_id").each(function() { $(this).val(0); });
            $("#batch_id").each(function() { $(this).val(0); });
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

    // ---------------------
    // ConfigSelector events
    // ---------------------

    $("#info-container").on('click', '.config-button', function(e) {
        $ConfigSelector.onButtonClick($(this));
        e.stopPropagation();
    });

    $("#info-container").on('click', '.config-icon', function(e) {
        $ConfigSelector.onIconClick($(this));
        e.stopPropagation();
    });

    $("#reference-container").on('click', '.reference-button', function(e) {
        $ReferenceDialog.onButtonClick($(this));
        e.stopPropagation();
    });

    $("#reference-container").on('click', '.reference-item', function(e) {
        //$ReferenceDialog.toggle($TablineSelector.onRefresh($(this)));
        $ReferenceDialog.toggle($(this));
        e.stopPropagation();
    });

    $("#reference-container").on('click', '.reference-icon', function(e) {
        $ReferenceDialog.onIconClick($(this));
        e.stopPropagation();
    });

    // --------------
    // Line selection
    // --------------

    $(".line").click(function(e) {
        $LineSelector.onRefresh($(this));
    });

    // -----------------
    // SubLine selection
    // -----------------

    $("#subline-content").on('click', '.subline', function(e) {
        $ConfigSelector.move($(this));
    });

    // ---------------------
    // Data Section progress
    // ---------------------

    $("#data-section").on('click', '.column', function(e) {
        var ob = $(this);
        var parent = ob.parents("*[class*='line']").first();
        if (!is_null(parent) && !parent.hasClass("tabline") && !ob.hasClass("header") && $ActiveSelector.onProgress())
            $InProgress(ob, 1);
    });

    // -----------------
    // Tabline selection
    // -----------------

    $(".view-lines").on('click', '.tabline', function(e) {
        $ConfigSelector.move($(this));
        $ConfigSelector.toggle($ActiveSelector.get_current());
    });

    // ------------------------
    // Control Panel Menu items
    // ------------------------

    $("button[id^='admin']", this).click(function(e) {
        var command = $(this).attr('id');

        $onControlPanelClick($("#admin-panel-dropdown"));

        if (IsAdmin && command.startswith('admin:'))
            $ConfigSelector.confirmation(command);
    });

    $("button[id^='service']", this).click(function(e) {
        var command = $(this).attr('id');

        $onControlPanelClick($("#services-dropdown"));
        
        if (command.startswith('service:'))
            $ReferenceDialog.confirmation(command);
    });

    $("button[id^='action']", this).click(function(e) {
        var command = $(this).attr('id');

        $onControlPanelClick($("#actions-dropdown"));
        
        if (command == 'action:configscenario') {
            $ConfigScenarioDialog.create();
            return;
        }
        
        if (command == 'action:removescenario') {
            $ConfigScenarioDialog.remove();
            return;
        }

        if (command == 'action:createdesign') {
            $CreateDesignDialog.open();
            return;
        }
    });

    // --------------
    // Tabs Data menu
    // --------------

    $("div[id^='data-menu']", this).click(function(e) {
        $TabSelector.onClick($(this));
    });

    // --------------
    // Tabs Data menu
    // --------------

    $("#tree-view-icon").click(function(e) {
        $SidebarControl.hide();

        interrupt(true, 4, 300, null, null, 0);
    });

    // -------------
    // Resize window
    // -------------

    $(window).on("resize", function() {
        $onClickTreeView(1);
    });

    // ---------------
    // Keyboard Events
    // ---------------

    $(window).keydown(function(e) {
        if ($ConfirmDialog.is_focused() || $NotificationDialog.is_focused())
            return;

        var exit = false;

        // CONFIGURATOR ACTIONS
        
        if (e.keyCode==13) {                                     // Enter
            if ($ReferenceDialog.is_focused())
                $ReferenceDialog.onEnter()
        }
        
        if (e.keyCode==27) {                                     // Esc
            if ($ConfigSelector.is_open && !$ReferenceDialog.is_open) {
                $ConfigSelector.onButtonClick(null, 'back');
                exit = true;
            }
        }

        if ($ReferenceDialog.is_focused() || $BaseDialog.is_focused() || is_search_focused)
            return true;
        
        else if (e.shiftKey && e.keyCode==73)                    // Shift-I
            $ConfigSelector.confirmation('admin:add');

        else if (e.shiftKey && e.keyCode==85)                    // Shift-U
            $ConfigSelector.confirmation('admin:update');

        else if (e.shiftKey && e.keyCode==68)                    // Shift-D
            $ConfigSelector.confirmation('admin:remove');

        else if ($ConfigSelector.is_focused())                   // STOP ConfigSelector forms
            return true;

        else if (e.shiftKey && e.keyCode==70) {                  // Shift-F
            $ConfigScenarioDialog.create();
            return false;
        }

        else if (e.shiftKey && e.keyCode==71) {                  // Shift-G
            $CreateDesignDialog.open();
            return false;
        }

        // REFERENCEs

        else if (e.shiftKey && e.keyCode==49)                    // Shift-1
            $ReferenceDialog.confirmation('service:file-type');

        else if (e.shiftKey && e.keyCode==50)                    // Shift-2
            $ReferenceDialog.confirmation('service:batch-type');

        else if (e.shiftKey && e.keyCode==51)                    // Shift-3
            $ReferenceDialog.confirmation('service:oper-type');

        else if (e.shiftKey && e.keyCode==52)                    // Shift-4
            $ReferenceDialog.confirmation('service:clients');

        else if (e.shiftKey && e.keyCode==53)                    // Shift-5
            $ReferenceDialog.confirmation('service:file-status');

        else if (e.shiftKey && e.keyCode==54)                    // Shift-6
            $ReferenceDialog.confirmation('service:batch-status');

        else if (e.shiftKey && e.keyCode==55)                    // Shift-7
            $ReferenceDialog.confirmation('service:oper-list');

        else if (e.shiftKey && e.keyCode==56)                    // Shift-8
            $ReferenceDialog.confirmation('service:tag-params');

        else if (e.shiftKey && e.keyCode==57)                    // Shift-9
            $ReferenceDialog.confirmation('service:ftv-oper-params');

        else if (e.shiftKey && e.keyCode==48)                    // Shift-0
            $ReferenceDialog.confirmation('service:ftb-post');

        if (exit) {
            e.preventDefault();
            return false;
        }
    });
});

function is_moving_keycode(keyCode) {
    return [33,34,35,36,38,40].indexOf(keyCode) > -1;
}

function keyboard_alt_before(keyCode) {
    if (is_moving_keycode(keyCode))
        return $ConfigSelector.move(null);
}
function keyboard_alt_after(keyCode) {
    if (is_moving_keycode(keyCode) && $ActiveSelector.is_movable())
        $ConfigSelector.toggle($ActiveSelector.get_current());
}

function page_is_focused(e) {
    if (e.shiftKey && [67,79].indexOf(e.keyCode) > -1)
        return $ConfigSelector.is_focused() || $ReferenceDialog.is_focused();
    if ((e.ctrlKey && [37,39].indexOf(e.keyCode) > -1) || (e.shiftKey && e.keyCode==9)) {
        $ConfigSelector.move(null, 1);
        $ConfigSelector.reset();
        return false;
    }
    if (e.altKey && is_moving_keycode(e.keyCode))
        return $ReferenceDialog.is_focused();
    return $ConfigSelector.is_focused() || $ReferenceDialog.is_focused();
}

// =======
// STARTER
// =======

$(function() 
{
    if (IsTrace)
        alert('Document Ready (configurator)');

    IsActiveScroller = 0;

    current_context = 'configurator';

    $("#search-context").attr('placeholder', 'Найти (тип файла)...');

    $_init();
});
