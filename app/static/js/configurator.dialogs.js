// **********************************************
// CONFIGURATOR DIALOGS: /configurator.dialogs.js
// ----------------------------------------------
// Version: 1.0
// Date: 22-06-2019

// ===========================
// Dialog windows declarations
// ===========================

var $ConfigScenarioDialog = {
    create: function() {
        $("#command", "#configscenario-form").val('admin:createscenario');
        $BaseDialog.open('configscenario');
    },

    remove: function() {
        var id = $("#file_id", "#configscenario-form").val();
        confirm_action = 'admin:removescenario';
        $ConfirmDialog.open(
            keywords['Command:Config scenario removing'] + 
            '<br><div class="removescenario">FileTypeID:&nbsp;<span>'+id+'</span></div>', 
            500);
    },

    confirmed: function(command) {
        if (command == 'removescenario') {
            $BaseDialog.init('configscenario');
            $("#command", "#configscenario-form").val('admin:'+command);
        }
        $BaseDialog.confirmed();
    }
};

var $CreateDesignDialog = {
    open: function() {
        $BaseDialog.open('createdesign');
    },
};

// =======
// Dialogs
// =======

jQuery(function($) 
{
    // --------------------------------
    // Create Scenario Generator Dialog
    // --------------------------------

    $("#configscenario-confirm-container").dialog({
        autoOpen: false,
        width:630,
        height:660,
        position:0,
        buttons: [
            {text: keywords['Run'],    click: function() { $BaseDialog.confirmed(); }},
            {text: keywords['Reject'], click: function() { $BaseDialog.cancel(); }}
        ],
        modal: false,
        draggable: true,
        resizable: false,
        position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        close: function() {
            $BaseDialog.onClose();
        }
    });

    // --------------------
    // Create Design Dialog
    // --------------------

    $("#createdesign-confirm-container").dialog({
        autoOpen: false,
        width:630,
        height:580,
        position:0,
        buttons: [
            {text: keywords['Run'],    click: function() { $BaseDialog.confirmed(); }},
            {text: keywords['Reject'], click: function() { $BaseDialog.cancel(); }}
        ],
        modal: false,
        draggable: true,
        resizable: false,
        position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        close: function() {
            $BaseDialog.onClose();
        }
    });
});
