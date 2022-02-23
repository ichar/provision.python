// ***********************************
// LOGIN PAGE DECLARATION: /login.html
// -----------------------------------
// Version: 1.00
// Date: 29-08-2017

// --------------
// Page Functions
// --------------

var $SidebarDialog = null;

function $Init() {
    $("#login").focus();
}

function page_is_focused(e) {
    return true;
}

$(document).ready(function() {
    $('.x_pass').click(function(){
        var id = $(this).attr('for');
        var ob = $('#'+id);
        var type = ob.attr('type') == "text" ? "password" : 'text';
        var s = $(this).html() == "<span class=\"glyphicon glyphicon-eye-close\" title=\"{{ _('Hide password') }}\"></span>" ? 
            "<span class=\"glyphicon glyphicon-eye-open\" title=\"{{ _('Show password') }}\"></span>" : 
            "<span class=\"glyphicon glyphicon-eye-close\" title=\"{{ _('Hide password') }}\"></span>";
        $(this).html(s);
        ob.prop('type', type);
    });
});

// =======
// STARTER
// =======

$(function() 
{
    if (IsTrace)
        alert('Document Ready (login)');

    $_init();
});
