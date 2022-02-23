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

var $image = null;

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
    $onCalculatorSubmit(null);
    
    $DraggableImage.init({ 'width_padding' : 20, 'height_padding' : 20});
    $PageScroller.reset(true);
}

// =========================
// Custom routine assigments
// =========================

function $onRefresh(x) {
    var data = x['data'];
    var controls = x['controls'];
    var errors = x['errors'];

    $("#price").html(data['price']);
    $("#tax").html(data['tax']);
    $("#charge").html(data['charge']);
    $("#euro").html(data['euro']);
    $("#usd").html(data['usd']);
    $("#rub").html(data['rub']);

    //console.log('controls', typeof(controls), objectKeyValues(controls));

    function set_enabled_option(id, container) {
        var index = 0;
        var is_selected = false;

        $("option", container).each(function() {
            var ob = $(this);
            var disabled = ob.is(':disabled');
            
            //console.log(ob.attr('id'), index, disabled, is_selected);

            if (is_selected)
                return;
            else if (disabled) {
                ob.prop("selected", false);
                index += 1;
            }
            else {
                ob.prop("selected", true);
                is_selected = true;
            }
        });
        container.prop("selectedIndex", index);

        //console.log('id:', id, index);
    }

    for (i=0; i < controls.length; i++) {
        var id = controls[i][0];
        var state = controls[i][1];
        var is_disabled = state == 1 ? true : false;
        var is_check = state == -1 ? true : false;
        var ob = $("#"+id);
        var tag = ob.prop("tagName");
        var selected = ob.prop("selected");
        var selected_index = ob.prop("selectedIndex");

        if (is_disabled && selected)
            ob.prop("selected", false);
        else if (is_check)
            set_enabled_option(id, ob);

        //console.log('id:', id, tag, is_disabled, selected, selected_index);

        if (is_check)
            continue;

        ob.prop("disabled", is_disabled);

        var parent = ob.parent();
        if (parent.hasClass("value")) {
            var input = $("input", parent);
            if (is_disabled) {
                parent.addClass("disabled").removeClass("checked");
                input.addClass("disabled").prop("checked", false);
            } else {
                parent.removeClass("disabled");
                input.removeClass("disabled");
            }
        }
    }

    $("#sign").prop("src", root+'static/img/sign-on.png')
}

function $onLocalExportClick() {
    $("#command").val('export');
    $onParentFormSubmit('calculator');
}

var checked_item = new Object();

function $onCalculatorSubmit(ob) {
    var params = new Object();
    var action = default_action;

    if (!is_null(ob)) {
        var id = ob.attr('id');
        var name = ob.attr('name');
        var parent = ob.parent();
        var is_radio = ob.prop('type') == 'radio' ? true : false;

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
    }

    var items = '';

    $("*[id^='item_']").each(function(index) {
        var item = $(this);
        var name = item.attr('name');
        var value = item.val();
        var is_check = ['checkbox','radio'].indexOf(item.prop('type')) > -1 ? true : false;
        var is_disabled = item.prop("disabled") ? true : false;
        if (((!is_check && int(value) > 0) || item.prop('checked')) && !is_disabled) {
            if (items) 
                items += '|';
            items += name+':'+value;
        }
    });

    //console.log('items:', items);

    var options = '';

    $("input[id^='option_']").each(function(index) {
        var option = $(this);
        var name = option.attr('name');
        var value = option.val();
        var is_check = ['checkbox','radio'].indexOf(option.prop('type')) > -1 ? true : false;
        if ((!is_check && int(value) > 0) || option.prop('checked')) {
            if (options) 
                options += '|';
            options += name+':'+value;
        }
    });

    //console.log('options:', options);

    $("#sign").prop("src", root+'static/img/sign-off.png');

    params['bound'] = $("#bound").val();
    params['items'] = items;
    params['options'] = options;

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

    $("input", "#calculator").on('change', function(e) {
        var ob = $(this);
        var value  = ob.val();
        var is_check = ['checkbox','radio'].indexOf(ob.prop('type')) > -1 ? true : false;

        if (!is_check) {
            if (value != ob.attr("value"))
                ob.attr("value", value);
        }
        
        //console.log(ob.attr('id'), value, ob.attr('value'));
        
        $onCalculatorSubmit(ob);
    });

    $("div.value", "#calculator").on('click', function(e) {
        var tag = e.target.tagName;
        var ob = $("input", tag == 'SPAN' ? $(this).parent() : (tag == 'INPUT' ? e.target : $(this)));
        var is_checked = ob.prop("checked") ? true : false;
        var is_blocked = ob.hasClass("blocked") ? true : false;
        
        //console.log(ob, tag, is_checked, is_blocked);
        
        if (is_null(ob) || tag == 'SELECT' || is_blocked) 
            return;

        ob.prop("checked", is_checked ? false : true);
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
        $PageScroller.reset(false);
        e.preventDefault();
        return false;
    });

    // ---------------
    // Draggable Image
    // ---------------

    $("img.screenshot").on("mouseleave", function(e) {
        $DraggableImage.onLeave(e);
    }).on("mouseenter", function(e) {
        var ob = $(this);
        var id = 'image_' + (ob.attr('id').split('_')[1] || '0');

        $DraggableImage.onEnter(ob, id, e);
    });

    $("img.screenshot").on("mousemove", function(e) {
        $DraggableImage.onMove(e);
        e.preventDefault();
        return false;
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
