// ********************************************
// PERSOSTATION PAGE DECLARATION: /catalog.html
// --------------------------------------------
// Version: 1.00
// Date: 14-03-2019

default_submit_mode = 2;
default_action      = '820';
default_log_action  = '821';

// ----------------------
// Dialog Action Handlers
// ----------------------

var $image = null;

function log_callback(current_action, data, props) {
}

// --------------
// Page Functions
// --------------

IsTrace = 0;

function $Init() {
    $DraggableImage.init({ 'width_padding' : 20, 'height_padding' : 20});
    $PageScroller.reset(true);
}

// =========================
// Custom routine assigments
// =========================

function $onRefresh(x) {
}

function $onLocalExportClick() {
    $("#command").val('export');
    $onParentFormSubmit('catalog');
}

function $onCatalogSubmit(ob) {
    var params = new Object();
    var action = default_action;

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

    $("input", "#catalog").on('change', function(e) {
        var ob = $(this);
        $onCatalogSubmit(ob);
    });

    $("div.value", "#catalog").on('click', function(e) {
        $onCatalogSubmit(ob);
    });

    $("select").on('change', function(e) {
        $onCatalogSubmit($(this));
    });

    $("#loc_export").click(function(e) {
        $onLocalExportClick();
        e.preventDefault();
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
        alert('Document Ready (catalog)');

    current_context = 'catalog';
    resize();

    try {
        $_init();
    }
    catch(e) {}
});
