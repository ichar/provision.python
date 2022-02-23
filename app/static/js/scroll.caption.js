// ****************************************************
// PROVISION/DECREES PAGE DECLARATION: ext/decrees.html
// ----------------------------------------------------
// Version: 1.00
// Date: 18-11-2021

// Caption scroll state
var caption_state = 0;

// Caption params
var caption_top = 0;
var caption_height = 0;
var caption_offside = 40;

// Caption hiding behavior, disabled if this value equals 0, otherwise >= 8
var caption_fixed = 8;

// Animate timeout
var is_animate = 1;
var animate_timeout = 300;
var timer = null;

// Scroller values (current, previous)
var scroll = [0, 0];
var is_move_forward = true;
var is_move_back = false;

// ----------------------
// Dialog Action Handlers
// ----------------------

function $animate() {
    if (caption_state == -1) {
        clearTimeout(timer);
        timer = null;

        $("#caption").removeClass('hidden').css({ top: -caption_height, transform: 'translateY(100%)' });

        caption_state = 1;
    }
}

function $freeze() {
    if (caption_state == -1) {
        clearTimeout(timer);
        timer = null;

        $("#caption").removeClass('fixed').css({ top:0, transform: 'none' });
        
        caption_state = 0;
    }

    $("#line-content").css({ marginTop: 0 });
}

function $scroll() {
    scroll[0] = $(window).scrollTop();
    is_move_forward = scroll[0] >= scroll[1] ? true : false;
    is_move_back = !is_move_forward;
    scroll[1] = scroll[0];
}

function $check_state() {
    if (caption_fixed > 0) {
        var x = caption_top + caption_height - caption_fixed;
        var is_over = scroll[0] > x ? true : false;
        if (is_over) {
            if (is_move_forward) {
                if (is_null(timer)) {
                    $("#line-content").css({ marginTop: caption_height + caption_offside });
                    $("#caption").addClass('fixed').css({ top: caption_fixed - caption_height, transform: 'none' });
                }
                caption_state = -1;
            }
            else if (caption_state == -1) 
                caption_state = 0;
        }
    }
    return caption_state == 0 ? 1 : 0;
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

    // -------------
    // Resize window
    // -------------

    $(window).on("resize", function(e) {
        resize(e);
    });

    $(window).scroll(function(e) {
        if (!is_animate)
            return;

        $scroll();

        //alert(caption_state);

        if (scroll[0] > caption_top + caption_height - caption_fixed) {
            if ($check_state()) {
                $("#line-content").css({ marginTop: caption_height + caption_offside });
                $("#caption").addClass('hidden').addClass('fixed');
                timer = setTimeout($animate, animate_timeout);
                caption_state = -1;
            }
        } else if (scroll[0] == 0) {
            if (caption_state != 0) {
                timer = setTimeout($freeze, animate_timeout);
                caption_state = -1;
            }
        }
    });
});

function resize(e) {
    var ob = $("#caption");
    var line = $("#line-content");
    var m = $_width('client')-40;
    //var w = $("#line-content").width();
    var width = $_get_css_size(m);

    //alert(m+':'+w+':'+width);

    ob.css({ "width":width });
    line.css({ "width":width });

    caption_top = ob.position().top;
    caption_height = ob.height() + 15;

    //alert(caption_top+':'+caption_height);

    if ($_mobile())
        return ob;

    if (!is_null(e))
        ob.css({ top: -caption_height });
    else
        return ob;
}
