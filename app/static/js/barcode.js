// ****************************************************
// PROVISION/BARCODE PAGE DECLARATION: ext/barcode.html
// ----------------------------------------------------
// Version: 1.00
// Date: 31-08-2021

default_submit_mode = 2;

function history_callback(id) {
    if (id == 'history:menu')
        window.location.replace('/provision/finance');
}

// --------------
// Page Functions
// --------------

IsTrace = 0;

function $Init() {
    var box = $("#barcode");

    $BarcodeReader.init(box);
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
        e.stopPropagation();
    });

    // -----------------------------------
    // Data Section progress & Maintenance
    // -----------------------------------

    $("#barcode").on('change', function(e) {
        $BarcodeReader.render($(this).val());

        e.stopPropagation();
        e.preventDefault();
    });

    // ------------------------
    // Control Panel Menu items
    // ------------------------

    $("button[id^='barcode']", this).click(function(e) {
        var ob = $(this);
        var command = ob.attr('id');

        //alert(command);

        if (command == 'barcode:reset')
            $BarcodeReader.reset();
        else if (command == 'barcode:expand')
            $BarcodeSelectorDialog.expand();
        else if (command == 'barcode:collapse')
            $BarcodeSelectorDialog.collapse();
    });

    $("#line-content").on('click', '.showbar', function(e) {
        $BarcodeSelectorDialog.showbar($(this));
    });

    // -------------
    // Resize window
    // -------------

    $(window).focus(function() {
        $BarcodeReader.focus();
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

    $(window).scannerDetection();
    $(window)
        .bind('scannerDetectionComplete',function(e, data) {
            var barcode = data.string;
            var box = $("#barcode");

            //alert('complete ['+barcode+']');

            if (barcode.length) {
                box.val(barcode);
                $BarcodeReader.render(barcode);
            }
        });
        /*
        .bind('scannerDetectionError',function(e, data) {
            alert('detection error ['+data.string+']');
        })
        .bind('scannerDetectionReceive',function(e, data) {
            alert('Recieve:'+data.evt.which);
        })
        */
});

function page_is_focused(e) {
    return false;
}

function resize() {
    if ($_mobile())
        return;

    $("#caption").css({ "width": $_get_css_size($("#page-container").width()) });
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
    resize();

    var ob = $("#caption");
    
    caption_top = ob.position().top;
    caption_height = ob.height() + 15; // padding+border

    ob.css({ width: $_get_css_size($("#page-container").width()) });

    try {
        $_init();
    }
    catch(e) {
        alert('error');
    }
});
