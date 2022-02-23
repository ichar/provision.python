// **************************************************
// PROVISION/SELLER PAGE DECLARATION: ext/audit.html
// --------------------------------------------------
// Version: 1.00
// Date: 05-03-2020

default_submit_mode = 2;

// ----------------------
// Dialog Action Handlers
// ----------------------

function history_callback(id) {
    if (id == 'history:menu')
        window.location.replace('/provision/finance');
}

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
    // --------------
    // Line selection
    // --------------

    $("#page-container").on('click', 'a', function(e) {
        var ob = $(this);
        var href = ob.attr('href');

        if (ob.attr('class') != 'rendered_link')
            return;

        e.preventDefault();

        $AuditSelectorDialog.go(href);

        e.stopPropagation();
    });

    // -----------------------------------
    // Data Section progress & Maintenance
    // -----------------------------------

    $("#created_after").on('change', function(e) {
        $AuditSelectorDialog.go();
        e.stopPropagation();
    });

    // ------------------------
    // Control Panel Menu items
    // ------------------------

    $("button[id^='audit']", this).click(function(e) {
        var ob = $(this);
        var id = ob.attr('id');
        var href = ob.attr('href');

        if (id == 'audit:expand')
            $AuditSelectorDialog.expand();
        else if (id == 'audit:collapse')
            $AuditSelectorDialog.collapse();
        else if (href)
            $AuditSelectorDialog.go(href);
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
        alert('Document Ready (audit)');

    $("#html-container").css({ marginTop: 0, height: '100%' });

    current_context = 'audit';

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
