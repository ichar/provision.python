// ************************************************
// PROVISION/STOCK PAGE DECLARATION: ext/stock.html
// ------------------------------------------------
// Version: 1.00
// Date: 30-11-2019

default_submit_mode = 2;

// --------------
// Page Functions
// --------------

IsTrace = 0;

function $Init() {
    
}

// =========================
// Custom routine assigments
// =========================

function $Confirm(mode, ob) {
    $ConfirmDialog.close();

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
    // ------------------------
    // Control Panel Menu items
    // ------------------------

    $("button[id^='stock']", this).click(function(e) {
        var ob = $(this);
        var command = ob.attr('id');

        //alert(command);

        if (command == 'stock:update')
            $StockSelectorDialog.open(ob, 'update');
        else if (command == 'stock:read')
            $StockSelectorDialog.open(ob, 'read');
        else if (command == 'stock:print')
            $StockSelectorDialog.print(ob);
        else if (command == 'stock:sort')
            $StockSubmitDialog.sort(ob);
        else if (command == 'stock:expand')
            $StockSelectorDialog.expand();
        else if (command == 'stock:collapse')
            $StockSelectorDialog.collapse();
    });

    $("#line-content").on('click', '.showbar', function(e) {
        $StockSelectorDialog.showbar($(this));
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

// =======
// STARTER
// =======

$(function() 
{
    if (IsTrace)
        alert('Document Ready (stock)');

    $("#html-container").css({ marginTop: 0, height: '100%' });

    current_context = 'stock';

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
