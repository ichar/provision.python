// *************************************************
// PERSOSTATION PAGE DECLARATION: /calculator.html
// -------------------------------------------------
// Version: 1.00
// Date: 23-01-2019

default_submit_mode = 2;
default_action      = '810';
default_log_action  = '811';

// ----------------------
// Dialog Action Handlers
// ----------------------

function log_callback(current_action, data, props) {
}

// --------------
// Page Functions
// --------------

IsTrace = 0;

// --------------
// Page Functions
// --------------

IsTrace = 0;

function $Init() {
    $("#sidebarFrame").hide();
}

function $onRefresh(x) {
    var data = x['data'];

    $("#price").html(data['price']);
    $("#tax").html(data['tax']);
    $("#charge").html(data['charge']);
    $("#euro").html(data['euro']);
    $("#usd").html(data['usd']);
    $("#rub").html(data['rub']);

    $("#sign").prop("src", root+'static/img/sign-on.png')
}

function $onLocalExportClick() {
    $("#command").val('export');
    $onParentFormSubmit('calculator');
}

// ====================
// Page Event Listeners
// ====================

jQuery(function($) 
{
    // ---------------
    // Register's Form
    // ---------------

    function $onCalculatorSubmit(id) {
        var params = new Object();
        var action = default_action;
        var items = '';

        $("input[id^='item_']").each(function(index) {
            var item = $(this);
            var id = item.attr('id');
            if (item.prop('checked')) {
                if (items) items += ':';
                items += id;
            }
        });

        $("#sign").prop("src", root+'static/img/sign-off.png');

        params['bound'] = $("#bound").val();
        params['items'] = items;
        params['chip'] = $("#chipbox").val();

        $web_logging(action, function(x) { $onRefresh(x); }, params);
    }

    $("input", "#calculator").on('change', function(e) { //  keyup paste
    	var id = $(this).attr('id');
        $onCalculatorSubmit(id);
    });

    $("select").on('change', function(e) {
        var id = $(this).attr('id');
        if (id != 'batches') $onCalculatorSubmit(id);
    });

    $("#loc_export").click(function(e) {
        $onLocalExportClick();
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
        }

        if (is_search_focused)
            return;

        var exit = false;

        //alert(e.ctrlKey+':'+e.shiftKey+':'+e.altKey+':'+e.keyCode);

        if (exit) {
            e.preventDefault();
            return false;
        }
    });
});

function page_is_focused(e) {
    return false;
}

function resize() {
}

// =======
// STARTER
// =======

$(function() 
{
    if (IsTrace)
        alert('Document Ready (calculator)');

    current_context = 'calculator';
    resize();

    try {
        $_init();
    }
    catch(e) {}
});
