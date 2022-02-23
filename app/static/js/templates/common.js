// *******************
// COMMON DECLARATIONS
// -------------------
// Version: 1.50
// Date: 08-12-2017

var keywords = new Object();
var script_version = 1;
var default_timeout = 100;
var default_loader_timeout = 300;

var IsDebug = 0;                  // Turn on/off Debug-mode  
var IsDeepDebug = 0;              // Turn on/off DeepDebug-mode  
var IsTrace = 0;                  // Turn on/off Trace-mode
var IsLog = 0;                    // Turn on/off console log
var IsTraceCommit = 0;            // Alert Field's state controller Commit-errors
var IsTraceRollback = 0;          // Alert Field's state controller Rollback-errors
var IsTraceErrorException = 0;    // Alert(show) error exception
var IsForcedRefresh = 0;          // Forced refresh any images in filesystem-cache (load with timestamp-link)
var IsAdmin = 0;                  // User Admin permissions
var IsAssumeExchangeError = 0;    // Exchange errors allowed or not (for localhost debug reasons)
var IsXMLDump = 0;                // For 'internal' only - dump request/response or not
var IsCleanBefore = 1;            // For 'internal' only - how to referesh items (clean before or not)
var IsCheckImageTimeout = 0;      // Wait images will be refreshed before init a new state
var IsTriggeredSubmit = 0;        // Show/Hide startup page
var IsShowLoader = 0;             // Apply submit image

// ---------------------------------------------------------
//  Line Page Submit Type:
//  0 - page submit, 1 - startup action, 2 - selected action
// ---------------------------------------------------------
var default_submit_mode = 0;
var default_action = null;        // Action for submit mode > 0
var default_log_action = null;    // Action for Log Tab
var default_input_name = '';      // Name of LINE input tag

var current_context = '';         // Current context name

var selected_menu_action = null;  // Selected DataMenu Action
var selected_control = null;      // Selected form's control

var semaphore_state = null;
var treeview_state = null;

// ==========================================================================================================

// ----------------
// Global Constants
// ----------------

var TID = new Array();

var LINE = '';
var SUBLINE = '';
var TABLINE = 'tabline';
var REFERENCE = 'reference';

var isWebServiceExecute = false;
var isSubmitted = false;
var isKeyboardDisabled = false;
var isConfirmation = false;
var isDropdownActive = false;
var isCallback = false;

var confirm_action = '';
var confirm_response = null;

var DEFAULT_HTML_SPLITTER = ':';

var CSS_INVISIBLE = 'invisible';

// ------------
// Module items
// ------------

var root = '';
var baseURI = '';
var loaderURI = '';

var page_state = -1;

var is_loaded_success = false;
var is_show_error = false;
var is_link = false;
var is_scroll_top = false;

// --------------
// HAPPY NEW YEAR
// --------------

var $HappyNewYear = {
    count   : 5,
    current : 0,
    box     : null,
    image   : null,
    src     : '',
    timer   : null,

    init: function() {
        this.box = $("#newyear_box");
        this.image = $("#newyear_image");
        this.src = root + 'static/images/new-year-';
        //this.current = getRandomInt(0, this.count);
    },

    preload: function() {
        this.init();
        var items = [];
        for (i=0; i <= this.count; i++) 
            items.push(this.src+i.toString()+'.gif');
        preloadImages(items, function(){});
    },

    wait: function(ob) {
        this.timer = setTimeout(function() { $HappyNewYear.show(ob); }, 800);
    },

    clear: function() {
        if (!is_null(this.timer)) clearTimeout(this.timer);
    },

    show: function(ob) {
        this.clear();

        var src = this.src+this.current.toString()+'.gif';

        this.image.attr("src", src);

        var w = $_width('min');
        var offset = [2,4].indexOf(this.current) > -1 ? 1060 : 980;
        var top = ob.offset().top+50;
        var left = int((w-ob.offset().left)/2);
        var margin_left = [w, Math.max(w-offset, 0)];

        this.box.css({top:top, left:left, marginLeft:margin_left[0]}).animate({height:'toggle', width:'toggle', marginLeft:margin_left[1]}, 
            1000, "easeInQuad", function() {});

        this.next(1);
    },

    next: function(mode) {
        if (is_empty(mode))
            this.current = this.current < this.count ? this.current+1 : 0;
        else {
            while (true) {
                var x = getRandomInt(0, this.count);
                if (x != this.current) {
                    this.current = x;
                    break;
                }
            }
        }
    },

    hide: function() {
        this.box.hide();
        this.clear();
    }
};

// ----------------
// Global Functions
// ----------------

function interrupt(start, mode, timeout, callback, index, type) {
    //
    //  start [true, false] - фаза исполнения: true-старт, false-финиш
    //  mode - индекс алгоритма
    //  timeout - длительность таймаута
    //  callback - функция обратного вызова[9] (строка) или строковый параметр[-1]
    //  index - индекс таймаута
    //  type - тип функции: setTimeout/setInterval
    //
    if (start) {
        var i = !is_null(index) ? index : TID.length;
        //var s = "interrupt(false, "+mode+", 0, "+(callback ? "'"+callback+"'" : 'null')+", "+i+")";
        var delay = timeout ? timeout : default_timeout;
        var func = function() { interrupt(false, mode, 0, callback, i, type); };
        if (i == TID.length) TID.push(null);
        //TID[i] = (type === 1) ? window.setInterval(func, delay) : window.setTimeout(func, delay);
        if (type == 1)
            TID[i] = window.setInterval(func, delay);
        else
            TID[i] = window.setTimeout(func, delay);

        if (IsLog)
            console.log('start:'+mode+', index:'+i+', len:'+TID.length);

    } else if (mode) {
        if (IsLog)
            console.log('interrupt:'+mode+', TID:'+TID.join('-'));

        if (mode == -1) {
            if (!callback) callback = '';
            window.location.replace(callback);
        } else if (mode == 1) {
            interrupt(false, 0, 0, null, index);
            $ShowOnStartup();
        } else if (mode == 2) {
            interrupt(false, 0, 0, null, index);
            $ReferenceDialog.submit('refresh');
        } else if (mode == 3) {
            interrupt(false, 0, 0, null, index);
            $LineSelector.onReset();
        } else if (mode == 4) {
            interrupt(false, 0, 0, null, index);
            $onClickTreeView();
        } else if (mode == 9)
            $Semaphore.run(index);

    } else if (TID.length > index && TID[index] != null) {
        if (type == 1)
            window.clearInterval(TID[index]);
        else 
            window.clearTimeout(TID[index]);

        if (index == TID.length-1)
            TID.splice(index, 1);
        else
            TID[index] = null;

        if (IsLog)
            console.log('stop index:'+index+', len:'+TID.length);
    }
}

function $_screen_center(mode) {
    var f = !$IS_FRAME ? true : false;
    var m = mode || (f ? 'screen-max' : 'screen-min');
    return { 'W':$_width(m), 'H':$_height(m) };
}

function $_height(m) {
    //var ob = $(window);
    if (m == 'screen-max')
        return Math.max(window.screen.availHeight, verge.viewportH());
    if (m == 'screen-min')
        return Math.min(window.screen.availHeight, verge.viewportH());
    if (m == 'max')
        return Math.max(
            window.screen.height, 
            window.screen.availHeight, 
            document.body.clientHeight, 
            document.documentElement.clientHeight
            //ob.height()
        );
    else
        return Math.min(
            window.screen.height,
            window.screen.availHeight, 
            document.body.clientHeight, 
            document.documentElement.clientHeight
            //ob.height()
        );
}

function $_width(m) {
    //var ob = $(window);
    var f = !$IS_FRAME ? true : false;
    if (m == 'screen-max')
        return Math.max(window.screen.availWidth, verge.viewportW());
    if (m == 'screen-min')
        return Math.min(window.screen.availWidth, verge.viewportW());
    if (m == 'max')
        return Math.max(
            window.screen.width,                    // S
            window.screen.availWidth,               // W
            document.body.clientWidth,              // B
            document.documentElement.clientWidth    // H
            //ob.width()
        );
    else
        return Math.min(
            window.screen.width, 
            window.screen.availWidth, 
            document.body.clientWidth, 
            document.documentElement.clientWidth
            //ob.width()
        );
}

function $_get_item_id(ob, index) {
    var x = ob.attr('id') || 0;
    var id = (x && x.indexOf(DEFAULT_HTML_SPLITTER) > -1 && x.startswith('row')) ? x.split(DEFAULT_HTML_SPLITTER)[index || 1] : x;
    return id;
}

function $_maximize() {
    window.moveTo(0, 0);
    window.resizeTo($_width('max'), $_height('max'));
}

function $_set_body_value(id, value) {
    $("#"+id).each(function() { $(this).val(value); });
}

function $_init() {
    $HappyNewYear.preload();
    
    $ShowPageSubmitMessages();
    $Init();
    $ShowPage(0);
}

// ===============
// Action Handlers
// ===============

function $CurrentContext() {
    return current_context || 'default';
}

function $ShowPage(disable) {
    if (is_null(disable))
        return;
    var startup_page_container = $("#html-container");
    if (disable)
        startup_page_container.hide();
    else
        startup_page_container.show();
}

function $ShowOnStartup() {
    selected_menu_action = default_log_action;
    $Go(
        selected_menu_action
    );
}

function $ShowPageSubmitMessages() {
    function _get_object(id) {
        var ob = $("#"+id);
        return !is_null(ob) ? ob.val() : null;
    }

    var errors = _get_object('errors');
    var OK = _get_object('OK');

    if (!is_empty(errors))
        $ShowError(errors, true, true, false);

    else if (!is_empty(OK))
        $NotificationDialog.open(OK);
}

function $ShowSystemMessages(reset, error) {}

function $TriggerActions(disable) {
    if (IsTriggeredSubmit && default_submit_mode == 0)
        $ShowPage(disable);
}

function $ShowError(msg, is_ok, is_err, is_session_close) {
    if (is_show_error || !msg)
        return;
    var container = $("#error-container");

    $("#error-text").html(msg);

    if (is_ok) {
        $("#error-button").append(
            '<button id="error-button-ok" class="ui-button-text" onclick="javascript:$HideError();">'+keywords['OK']+'</button>'
        );
    }
    if (is_err)
        container.removeClass("warning").addClass("error");
    else
        container.removeClass("error").addClass("warning");

    var f = !$IS_FRAME ? true : false;
    var c = $_screen_center('min');
    var top = (int((c.H-container.height())/2)-(f?20:0)).toString()+'px';
    var left = (int((c.W-container.width())/2)).toString()+'px';

    container
        .css('top', top).css('left', left)
        .show();
    is_show_error = true;

    $("#error-button-ok").focus();

    if (is_session_close && !$IS_DEMO) interrupt(true, -1, 5000, '', 0);
}

function $HideError() {
    $("#error-container").hide();
    $("#error-button").html('');
    is_show_error = false;

    $SetFocus();
}

function $ShowLoader(start) {
    //alert('loader:'+start+':'+isWebServiceExecute);

    if (start) {
        var loader = $("#page-loader");
        var container = $("#html-container");
        if (start == -1) { 
            isWebServiceExecute = false;
            if (IsShowLoader)
                loader.hide();
            else {
                container.removeClass("inprogress");
                $InProgress(null);
            }
        } else {
            isWebServiceExecute = true;
            if (IsShowLoader)
                loader.show();
            else
                container.addClass("inprogress");
        }
    }
}

function $ActivateInfoData(show) {
    var container = $("#info-data");

    if (show)
        container.show();
    else {
        container.hide();
        return;
    }

    $PageScroller.reset(true);
}

function $RemoveInfoData() {
    var container = $("#info-data");
    container.empty().hide();
}

function $InProgress(ob, mode) {
    if (!is_null(ob) && mode == 1) {
        ob.addClass("inprogress");
        selected_control = ob;
    }
    else if (!is_null(selected_control)) {
        selected_control.removeClass("inprogress");
        selected_control = null;
    }
}

function $SetFocus(ob) {}

function $ResetSearch(deactivate) {
    //
    // Set Search icon and clean search context box
    //
    if (deactivate)
        $_deactivate_search();

    var search = $("#search-context");

    if (search.val()) {
        var src = $SCRIPT_ROOT+'/static/img/';

        if (is_search_activated) {
            $("#search-icon")
                .attr('title', keywords['Cancel search'])
                .attr('src', src+'db-close.png');
        } else {
            $("#search-icon")
                .attr('title', keywords['Search'])
                .attr('src', src+'db-search.png');
            search.val('');
        }
    }
}

function $HideLogPage() {
    var ob = SelectedGetItem(SUBLINE, 'ob');
    
    if (IsLog)
        console.log('$HideLogPage:'+is_null(ob));
    
    if (!is_null(ob))
        $onToggleSelectedClass(SUBLINE, ob, 'remove', null);
}

function $ShowLogPage() {
    var ob = SelectedGetItem(SUBLINE, 'ob');

    if (IsLog)
        console.log('$ShowLogPage:'+is_null(ob));
    
    if (!is_null(ob))
        $onToggleSelectedClass(SUBLINE, ob, 'add', null);

    if (is_scroll_top) {
        $(window).scrollTop(0);
        is_scroll_top = false;
    }
}

function $ResetLogPage() {
    //current_subline = null;
    $("#command").val('');
}

function $Go(action) {
    $web_logging(action, null);
}

function $Handle(action, handler, params) {
    $web_logging(action, handler, params);
}

// =======================
// Event's Action Handlers
// =======================

function $onParentFormSubmit(id) {
    var frm = $("#"+(id || 'filter-form'));
    var action = frm.attr('action');

    $SidebarControl.onBeforeSubmit();

    //alert('submit');

    $("#OK", frm).val('run');
    frm.submit();
}

function $onLineFormSubmit() {
    switch (default_submit_mode) {
        case 0:
            $onParentFormSubmit();
            break;
        case 1:
        case 2:
            $Go(default_action);
            break;
    }
}

function $onPageLinkSubmit(link) {
    var x = link.split('?');
    var url = x[0];
    var qs = x.length > 1 ? strip(x[1]) : '';

    url = url+'?'+(qs > '' ? qs+'&' : '')+'sidebar='+$SidebarControl.state.toString();

    window.location.replace(url);
}

function $onToggleSelectedClass(key, ob, action, command, force) {
    // ---------------------------------------
    // Set current selected HTML control item.
    // ---------------------------------------
    //      key     : type of control: LINE, SUBLINE, TABLINE, REFERENCE
    //      ob      : selected (a new) item HTML control
    //      action  : action to perform: submit|clear|add|remove
    //      command : command to submit
    //      force   : forced flag
    //
    // It used together with db.controller classes: $LineSelector, $SublineSelector.
    // On run `SelectedGetItem` function keeps current (selected before) item. 
    // Current item and his children have CSS `selected` class.
    // Action `submit` valid for LINE key only!

    var id = !is_null(ob) ? $_get_item_id(ob) : SelectedGetItem(key, 'id');
    var mask = [LINE, SUBLINE, TABLINE, REFERENCE].indexOf(key) > -1 ? 'td' : 'dd';
    var input = "input[name^='"+default_input_name+"']";

    //alert(key+':'+id+':'+action+':'+mask+':'+input);

    if (is_empty(id))
        return;

    if (is_null(ob))
        ob = SelectedGetItem(key, 'ob');

    function make(ob, action, mode) {
        // Toggles `selected` class and updates `default_input_name` inputs 
        // with the given control `id` for:
        //      key=LINE and mode=1
        // If ob == null, current item has not been selected before.

        if (is_null(ob))
            return;

        if (IsLog)
            console.log('$onToggleSelectedClass:'+action+':'+id);

        $(mask, ob).each(function() {
            if (action == 'add') {
                $(this).addClass("selected");
                if (key == LINE && mode == 1)
                    $(input).each(function() { $(this).val(id); });
            }
            else
                $(this).removeClass("selected");
        });

        if (action == 'add') {
            ob.addClass("selected");
            SelectedSetItem(key, 'ob', ob);
        }
        else {
            ob.removeClass("selected");
            SelectedSetItem(key, 'ob', null);
        }
    }

    $("#command").val(!is_null(command) ? command : '');

    switch (action) {
        case 'submit':
            if (isWebServiceExecute || key != LINE)
                return;

            $(input).each(function() { $(this).val(id); });

            if (force) {
                $onParentFormSubmit();
                return;
            }

            if (default_submit_mode > 0) {
                make(SelectedGetItem(key, 'ob'), 'remove', 0);
                SelectedReset();
                make(ob, 'add', 0);
            }

            $onLineFormSubmit();
            break;
        case 'clean':
            $(input).each(function() { $(this).val(''); });
            SelectedSetItem(key, 'ob', null);
            break;
        default:
            make(ob, action, 1);
    }
}

function $setPaginationFormSubmit(page) {
    $("input[name='page']").each(function() { $(this).val(is_null(page) ? '1' : page.toString()); });
}

function $onOpenHelp() {
    $HelpDialog.open();
    return true;
}

function $onRefreshClick() {
    $("#command").val('refresh');
    $onParentFormSubmit();
}

function $onResetClick() {
    $("#command").val('init-filter');
    $onParentFormSubmit('init-form');
}

function $onExportClick() {
    $("#command").val('export');
    $onParentFormSubmit();
}

function $onControlPanelClick(ob) {
    if (isDropdownActive)
        return;

    var id = ob.attr('id');
    var dropdown = (
        id == "admin-panel-dropdown" ? $("#admin-panel") : (
        id == "services-dropdown" ? $("#services") : (
        id == "actions-dropdown" ? $("#actions") : null
        )));

    if (is_null(dropdown))
        return;
    var dropdown_id = dropdown.attr('id');
    //
    // Was another selected item open before?
    //
    var is_selected = !(is_null(selected_dropdown) || selected_dropdown[0].attr('id') == dropdown_id);

    isDropdownActive = true;

    if (is_selected)
        selected_dropdown[0].slideToggle('slow');

    dropdown.slideToggle('slow', function() {
        isDropdownActive = false;
    });

    //
    // Is selected item closed?
    //
    var is_closed = !is_null(selected_dropdown) && selected_dropdown[1] == dropdown_id;

    selected_dropdown = is_closed ? null : new Array(dropdown, dropdown_id);
}

// =======================
// Common Event Listeners
// =======================

jQuery(function($) 
{
    $("#sidebar-navigator").click(function(e) {
        $SidebarControl.onNavigatorClick(false);
    });

    $("#sidebarFrame").on("mouseleave", function(e) {
        if ($(this).has(e.target).length > 0) { //(isIE || isFirefox) && 
            e.stopPropagation();
            return;
        }
        $SidebarControl.onFrameMouseOut();
        e.stopPropagation();
    }).on("mouseenter", function(e) {
        $SidebarControl.onFrameMouseOver();
        e.stopPropagation();
    });

    // ---------
    // Main Menu
    // ---------

    $("a.mainmenu").click(function(e) {
        var link = $(this).prop('href');
        $onPageLinkSubmit(link);
        e.preventDefault();
        return false;
    });

    // -----------------
    // Top Command Panel
    // -----------------

    $("#refresh").click(function(e) {
        $onRefreshClick();
        e.preventDefault();
    });

    $("#init-filter").click(function(e) {
        $onResetClick();
        e.preventDefault();
    });

    $("#export").click(function(e) {
        $onExportClick();
        e.preventDefault();
    });

    // ---------------------
    // Search context events
    // ---------------------

    function $onSearchSubmit(e) {
        var s = strip($("#search-context").val());
        if (s.length > 0) {
            search_context = s;
            $("#search-context").val(s);
            $("input[id='searched']").each(function() { $(this).val(s); });
            $LineSelector.onFormSubmit();
            $setPaginationFormSubmit(1);
            $onParentFormSubmit('filter-form');
        }
    }

    $("#search-context").focusin(function(e) {
        is_search_focused = true;
    }).focusout(function(e) {
        is_search_focused = false;
    });

    $("#search-icon").click(function(e) {
        $onSearchSubmit(null);
        $onParentFormSubmit('filter-form');
    });

    $("#search-form").submit(function(e) {
        $onSearchSubmit(e);
    });

    // -------------------
    // Dropdown Containers
    // -------------------

    $(".dropdown-link").click(function(e) {
        $onControlPanelClick($(this));
        e.preventDefault();
    });

    // --------------
    // HAPPY NEW YEAR
    // --------------

    $(".visitor").on("mouseleave", function(e) {
        $HappyNewYear.hide();
        e.stopPropagation();
    }).on("mouseenter", function(e) {
        $HappyNewYear.wait($(this));
        e.stopPropagation();
    });

    // ---------------
    // Activate window
    // ---------------

    $(window).focus(function() {
        $Semaphore.start(true);
    }).blur(function() {
        $Semaphore.stop(false);
    });

    // -------------
    // Resize window
    // -------------

    $(window).on("resize", function() {
        $SidebarControl.initState();
    });

    // ---------------
    // Navigator links
    // ---------------

    $("a.page").click(function(e) {
        var link = $(this).prop('href');
        $onPageLinkSubmit(link);
        e.preventDefault();
        return false;
    });

    // ---------------
    // Keyboard Events
    // ---------------

    $(window).keydown(function(e) {
        var exit = false;

        if (!e.ctrlKey && e.keyCode==116) {                      // F5 !!! IMPORTANT
            $onRefreshClick();
            exit = true;
        }

        if (e.shiftKey && e.keyCode==112)                        // Shift-F1
            exit = $onOpenHelp();

        if ($ConfirmDialog.is_focused() || $NotificationDialog.is_focused() || page_is_focused(e) || isKeyboardDisabled)
            return;

        try {
            if ($BaseDialog.is_focused() || is_search_focused)
                return;
        } 
        catch (err) {}

        if (e.shiftKey && [67, 79].indexOf(e.keyCode) > -1) {    // Shift-C,Shift-O
            $SidebarControl.onNavigatorClick(false);
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==82) {                  // Shift-R
            $onResetClick();
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==83) {                  // Shift-S
            var focused = $("#search-context");
            $SidebarControl.onFrameMouseOver(focused);
            focused.focus();
            exit = true;
        }

        else if (e.ctrlKey || e.shiftKey) {
            if (isWebServiceExecute)
                return;
            /*
            if (e.keyCode > 0)
                alert(e.ctrlKey+':'+e.keyCode);

            else if (e.keyCode==13)                             // Ctrl-Enter
            */

            // -----------------------
            // Tabline Selector moving
            // -----------------------

            if (e.keyCode==38)                                  // Ctrl-Up
                exit = $LineSelector.up();
            else if (e.keyCode==40)                             // Ctrl-Down
                exit = $LineSelector.down();
            else if (e.ctrlKey && e.keyCode==36)                // Ctrl-Home
                exit = $LineSelector.home();
            else if (e.shiftKey && e.keyCode==33)               // Shift-PgUp
                exit = $LineSelector.pgup();
            else if (e.shiftKey && e.keyCode==34)               // Shift-PgDown
                exit = $LineSelector.pgdown();
            else if (e.ctrlKey && e.keyCode==35)                // Ctrl-End
                exit = $LineSelector.end();

            // -------------
            // Tab Switching
            // -------------

            else if (e.shiftKey && e.keyCode==9)                // Shift-Tab
                exit = $TabSelector.tab();
            else if (e.ctrlKey && e.keyCode==37)                // Ctrl-Left
                exit = $TabSelector.left();
            else if (e.ctrlKey && e.keyCode==39)                // Ctrl-Right
                exit = $TabSelector.right();
        }

        else if (e.altKey) {
            if (isWebServiceExecute)
                return;
            /*
            if (e.keyCode > 0)
                alert(e.altKey+':'+e.keyCode);
            */

            var before = true;

            // -------------------
            // Before move handler
            // -------------------

            if (typeof keyboard_alt_before === 'function')
                before = keyboard_alt_before(e.keyCode);

            if (before) {
                if (e.keyCode==38)                              // Alt-Up
                    exit = $ActiveSelector.up();
                else if (e.keyCode==40)                         // Alt-Down
                    exit = $ActiveSelector.down();
                else if ([33, 36].indexOf(e.keyCode) > -1)      // Alt-Home:Alt-PgUp
                    exit = $ActiveSelector.home();
                else if ([34, 35].indexOf(e.keyCode) > -1)      // Alt-End:Alt-PgDown
                    exit = $ActiveSelector.end();
            }
            else
                exit = true;

            // ------------------
            // After move handler
            // ------------------

            if (typeof keyboard_alt_after === 'function' && before)
                keyboard_alt_after(e.keyCode);
        }

        if (exit) {
            e.preventDefault();
            return false;
        }
    });
});

// ============
// WEB-SERVICES
// ============

function $web_semaphore(action) {
    if (isWebServiceExecute || !$Semaphore.isEnabled())
        return;

    if (IsLog)
        console.log('web_semaphore:', action);

    $Semaphore.running();

    var args = {
        'action'   : action,
        'template' : $Semaphore.template,
        'lid'      : $Semaphore.lid,
    };

    //alert(args.lid);

    $.post($SCRIPT_ROOT + '/semaphore/loader', args, function(x) {
        var state = x['state'];

        $Semaphore.refresh(state);

    }, 'json')
    .fail(function() {

        $Semaphore.error();

    })
    .always(function() {

    });
}


