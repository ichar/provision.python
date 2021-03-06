// ********************************************************************
// PROVISION/PAYMENTS REVIEW PAGE DECLARATION: ext/payments-review.html
// --------------------------------------------------------------------
// Version: 1.00
// Date: 27-07-2020

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

    switch (mode) {
        case 0:
            break;
        case 1:
            if (['accept', 'reject'].indexOf(confirm_action) > -1)
                $PaymentReviewSelectorDialog.refresh($("#page-section"));
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
    // ------------------------
    // Control Panel Menu items
    // ------------------------

    $("div[id^='go']", this).click(function(e) {
        var id = $(this).attr('id');
        if (id == 'go:forward')
            $PaymentReviewSelectorDialog.forward();
        else if (id == 'go:back')
            $PaymentReviewSelectorDialog.back();
    });

    $("button[id='selector']", this).click(function(e) {
        var ob = $(this);
        var obs = $("input[type='checkbox']", "#line-content");
        var is_checked = ob.prop("value") == '1' ? true : false;
        //alert(obs.length);
        obs.each(function() { $(this).prop("checked", is_checked); });
        ob.prop("value", is_checked ? '0' : '1');
        ob.html(is_checked ? "Сбросить все" : "Выделить все");
    });

    $("button[id^='payments']", this).click(function(e) {
        var ob = $(this);
        var command = ob.attr('id');

        //alert(command);

        if (command == 'payments:accept')
            $PaymentReviewSelectorDialog.confirmation('accept');
        else if (command == 'payments:reject')
            $PaymentReviewSelectorDialog.confirmation('reject');
        else if (command == 'payments:print')
            $PaymentReviewSelectorDialog.print(ob);
        else if (command == 'payments:sort')
            $PaymentReviewSubmitDialog.sort(ob);
        else if (command == 'payments:expand')
            $PaymentReviewSelectorDialog.expand();
        else if (command == 'payments:collapse')
            $PaymentReviewSelectorDialog.collapse();
    });

    $("div.value", "#page-container").on('click', function(e) {
        var tag = e.target.tagName;
        var ob = $("input", tag == 'SPAN' ? $(this).parent() : (tag == 'INPUT' ? e.target : $(this)));
        var is_checked = ob.prop("checked") ? true : false;
        var is_blocked = ob.hasClass("blocked") ? true : false;
        
        //console.log(ob, tag, is_checked, is_blocked);
        
        if (is_null(ob) || tag == 'SELECT' || is_blocked) 
            return;

        ob.prop("checked", is_checked ? false : true);
        //$onCalculatorSubmit(ob);
    });

    $("#line-content").on('click', '.showbar', function(e) {
        $PaymentReviewSelectorDialog.showbar($(this));
    });

    $("*[class~='Total']", "#line-content").on("mouseenter", function(e) {
        $PaymentReviewSelectorDialog._get_changes($(this));
    });

    $("#payments-changes-container").on("mouseleave", function(e) {
        if (!(isIE || IsMSIE || isFirefox) || $(this).has(e.target).length == 0)
            $PaymentReviewSelectorDialog.hideChanges();
        e.stopPropagation();
    });

    $("*[class~='Total']", "#line-content").on("click", function(e) {
        $PaymentReviewSelectorDialog.showChanges($(this));
    });

    $("#calendar", this).on("click", function(e) {
        $PaymentReviewSubmitDialog.open('selectdate');
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

// =======
// STARTER
// =======

$(function() 
{
    if (IsTrace)
        alert('Document Ready (payments-review)');

    $("#html-container").css({ marginTop: 0, height: '100%' });

    //alert($_width('screen-max'));

    current_context = 'payments';

    var ob = resize();

    //alert(caption_height);

    ob.css({ "width": $_get_css_size($("#line-content").width()) });

    try {
        $_init();
    }
    catch(e) {
        alert('error');
    }
});
