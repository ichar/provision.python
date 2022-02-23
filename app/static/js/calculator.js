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

function showActiveTab(ob) {
    var oid = ob.attr("id");

    function get_id(id) { return id ? id.split(':')[1] : ''; }

    var id = get_id(oid);
    var parent = $("#calculator-tabs");
    var selected_tab = $("li[class~='selected']", parent);
    var tab = $("a", selected_tab);
    var sid = get_id(tab.attr('id'));

    selected_tab.removeClass('selected');
    ob.parent().addClass('selected');

    $("#box_"+sid).addClass('hidden');
    $("#box_"+id).removeClass('hidden');
}

// --------------
// Page Functions
// --------------

IsTrace = 0;

function $Init() {
    $("#sidebarFrame").hide();
}

// =========================
// Custom routine assigments
// =========================

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

var checked_item = new Object();

function $onCalculatorSubmit(ob) {
    var id = ob.attr('id');
    var name = ob.attr('name');
    var parent = ob.parent();
    var params = new Object();
    var action = default_action;
    var is_radio = ob.prop('type') == 'radio';
    var items = '';

    //alert(ob.val());

    if (is_radio && !is_null(checked_item[name]))
        checked_item[name].removeClass('checked');

    if ((ob.val() > '0' && ob.prop('type') == 'number') || ob.prop('checked') ? true : false) {
        parent.addClass('checked');
        if (is_radio)
            checked_item[name] = parent;
    } else {
        parent.removeClass('checked');
        if (is_radio)
            checked_item[name] = null;
    }

    $("input[id^='item_']").each(function(index) {
        var item = $(this);
        var name = item.attr('name');
        var value = item.val();
        if (item.prop('checked')) {
            if (items) 
                items += '|';
            items += name+':'+value;
        }
    });

    $("#sign").prop("src", root+'static/img/sign-off.png');

    params['bound'] = $("#bound").val();
    params['items'] = items;

    $web_logging(action, function(x) { $onRefresh(x); }, params);
}

// ====================
// Page Event Listeners
// ====================

jQuery(function($) 
{
    // ---------------
    // Register's Form
    // ---------------

    $("input", "#calculator").on('change', function(e) { //  keyup paste
        $onCalculatorSubmit($(this));
    });

    $("div.value", "#calculator").on('click', function(e) { //  keyup paste
        var tag = e.target.tagName;
        var ob = $("input", tag == 'SPAN' ? $(this).parent() : (tag == 'INPUT' ? e.target : $(this)));
        var checked = ob.prop("checked");
        
        //console.log(ob, parent, ob, e.target.tagName);
        
        ob.prop("checked", checked ? false : true);
        $onCalculatorSubmit(ob);
    });

    $("select").on('change', function(e) {
        $onCalculatorSubmit($(this));
    });

    $("#loc_export").click(function(e) {
        $onLocalExportClick();
        e.preventDefault();
    });

    // ------------------------
    // Calculator Tab selection
    // ------------------------

    $("a.common-tab", this).click(function(e) {
        showActiveTab($(this));
        e.preventDefault();
        return false;
    });

    $(".item").on("mouseleave", function(e) {
        $(this).removeClass('lineshown');
    }).on("mouseenter", function(e) {
        $(this).addClass('lineshown');
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
