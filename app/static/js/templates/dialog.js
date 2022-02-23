
var $OrderDialog = {
    container    : null,
    box          : null,
    state        : new Object(),

    init: function() {
        this.container = $("#order-confirm-container");
        this.box = $("#order-confirmation-box");
    },

    get_id: function() {
        return this.container.attr('id');
    },

    get_mode: function() {
        return this.container.attr('mode');
    },

    set_mode: function(mode) {
        this.container.attr('mode', mode);
    },

    toggle: function(ob) {

    },

    setContent: function(id, data) {

    },

    setDefaultSize: function(force) {

    },

    onResize: function(force) {
        var mode = this.get_mode();

        if (!(mode in this.actual_size))
            return false;

        //alert('resize:'+mode+':'+this.container.width()+':'+this.container.height());

        if (this.container.height() < 200 || this.container.width() < 500) {
            this.setDefaultSize(true);
            return false;
        }

        var offset = 108 + (force ? 3 : 6);
        var new_height = int(this.container.height() - offset);

        this.box.css("height", new_height.toString()+"px");

        if (force)
            this.actual_size[mode] = [
                this.container.width(), 
                this.container.height() + offset
            ];

        return true;
    },

    onOpen: function() {

    },

    onClose: function() {

    },

    confirmation: function(command) {
        this.init();
    },

    submit: function() {
        $onParentFormSubmit('filter-form');
    },

    open: function() {
        var mode = (action == '201' ? 'file' : 'batch');
        var id = SelectedGetItem(mode == 'file' ? LINE : SUBLINE, 'id');

        if (id == null)
            return;

        this.set_mode(mode);
        this.setContent(id, data);

        this.container.dialog("option", "title", keywords['Status confirmation form']);

        this.setDefaultSize(false);
        /*
        container.dialog("option", "position", "center");
        */
        this.container.dialog("open");

        //alert('open');
    },

    confirmed: function() {
        this.close();

        this.submit();
    },

    close: function() {
        this.container.dialog("close");
    }
};

// =======
// Dialogs
// =======

jQuery(function($) 
{

    // ----------------------------
    // Order Recreate/Remove Dialog
    // ----------------------------

    $("#order-confirm-container").dialog({
        autoOpen: false,
        width:540, // 640
        height:150, // 136
        position:0,
        buttons: [
            {text: keywords['Confirm'], click: function() { $_order_confirmed($(this)); }},
            {text: keywords['Reject'], click: function() { $(this).dialog("close"); }}
        ],
        modal: true,
        draggable: true,
        resizable: false
    });
});