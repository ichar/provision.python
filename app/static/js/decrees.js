// ****************************************************
// PROVISION/DECREES PAGE DECLARATION: ext/decrees.html
// ----------------------------------------------------
// Version: 1.00
// Date: 18-10-2021

default_submit_mode = 2;

// Flag for 'input' keyboards
var is_input_focused = false;

// --------------
// Page Functions
// --------------

IsTrace = 0;

function $Init() {
    $DecreeActionDialog.init();
}

// =========================
// Custom routine assigments
// =========================

function $Confirm(mode, ob) {
    $ConfirmDialog.close();

    if (mode == 1) {
        switch (confirm_action) {
            case 'decree:finish':
            case 'decree:reject':
                $DecreeActionDialog.run(1);
                break;
        }
    }

    confirm_action = '';
}

function $Notification(mode, ob) {
    $NotificationDialog.close();
}

// ====================
// Page Event Listeners
// ====================

jQuery(function($) 
{
    // ---------------
    // Register's Form
    // ---------------

    $("#caption").one("webkitTransitionEnd otransitionend oTransitionEnd msTransitionEnd transitionend", function() {
        //alert(1);
    });

    // -----------------------------------
    // Data Section progress & Maintenance
    // -----------------------------------

    $("#refresh-form").on('change', '.popup', function(e) {
        $DecreeSubmitDialog.refresh($(this));
        e.stopPropagation();
        e.preventDefault();
    });

    $("#line-content").on('focusin', 'textarea', function(e) {
        is_input_focused = true;
    }).on('focusout', function(e) {
        is_input_focused = false;
    });

    $("textarea[id^='item']").on('keydown', function(e) {
        $DecreeActionDialog.keypress($(this));
        e.stopPropagation();
    });

    // ------------------------
    // Control Panel Menu items
    // ------------------------

    $("button[id^='decrees']", this).click(function(e) {
        var ob = $(this);
        var command = ob.attr('id');

        //alert(command);

        if (command == 'decrees:print')
            $DecreeSelectorDialog.print(ob);
        else if (command == 'decrees:sort')
            $DecreeSubmitDialog.sort(ob);
        else if (command == 'decrees:expand')
            $DecreeSelectorDialog.expand();
        else if (command == 'decrees:collapse')
            $DecreeSelectorDialog.collapse();
        else if (command == 'decrees:reset')
            $DecreeSubmitDialog.reset();

        e.preventDefault();
    });

    $("button[id^='action']", this).click(function(e) {
        $DecreeActionDialog.run(0, $(this));
        e.preventDefault();
    });

    $("#line-content").on('click', '.showbar', function(e) {
        $DecreeSelectorDialog.showbar($(this));
    });

    $("#calendar", this).on("click", function(e) {
        $DecreeSubmitDialog.open('selectdate');
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

        if (e.shiftKey && [67, 79].indexOf(e.keyCode) > -1) {    // Shift-C,Shift-O
            $DecreeSelectorDialog.toggle();
            exit = true;
        }

        if (exit) {
            e.preventDefault();
            return false;
        }
    });
});

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
        alert('Document Ready (decree)');

    $("#html-container").css({ marginTop: 0, height: '100%' });

    current_context = 'decree';

    var ob = resize();

    //alert(caption_height);

    ob.css({ width: $_get_css_size($("#line-content").width()) });

    try {
        $_init();
    }
    catch(e) {
        alert('error');
    }
});
