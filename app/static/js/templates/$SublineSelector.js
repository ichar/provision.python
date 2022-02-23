var $SublineSelector = {
    container : null,

    // ----------------------
    // Subline Selector Class
    // ----------------------

    IsTrace   : 0,
    
    // ------------------------------------------------
    // Current page: page=pages=1, per_page:rows number
    // ------------------------------------------------

    current   : null,
    number    : 0,
    oid       : '',

    page      : 0,
    pages     : 0,
    per_page  : 0,
    line      : 0,

    is_top    : false,
    is_bottom : false,

    is_end_of_data : false,

    init: function(per_page) {
        this.container = $("#subline-content");

        this.page = 1;
        this.pages = 1;
        this.per_page = per_page;
        this.line = 1;

        this.current = current_subline;

        this.reset();
    },

    reset: function() {
        this.is_top = this.is_bottom = this.is_end_of_data = false;
    },

    get_id: function() {
        return $_get_item_id(this.current);
    },

    set_current: function(ob) {
        this.current = ob;
        this.oid = ob.attr('id');
        this.number = parseInt($_get_item_id(ob, 2));

        if (this.IsTrace)
            alert(this.number);

        return this._refresh(0);
    },

    _find: function(num) {
        var ob = null;

        this.container.find(".subline").each(function(index, x) {
            if (this.IsTrace)
                alert($(x).attr('id')+':'+parseInt($_get_item_id($(x), 2)));
            if (parseInt($_get_item_id($(x), 2)) == num)
                ob = $(x);
        });

        if (this.IsTrace)
            alert('found:'+(ob ? ob.attr('id') : 'null'));

        return ob;
    },

    _refresh: function(new_page) {
        var exit = false;
        var line;

        if (this.IsTrace)
            alert('refresh:'+this.number+':'+this.is_top+':'+this.is_bottom);

        // --------------------
        // Refresh current page
        // --------------------

        if (new_page == 0 && !(this.is_top || this.is_bottom || this.is_end_of_data)) {
            $HideLogPage();

            current_subline = this.current;
            SelectedSetItem(SUBLINE, 'ob', current_subline);

            $ShowOnStartup();
            exit = true;
        }

        return exit;
    },

    _move: function(direction) {
        var ob = null;
        var is_found = false;
        var num;

        // ------------------------
        // Move inside current page
        // ------------------------

        if ((direction > 0 && this.number < this.per_page) || (direction < 0 && this.number > 1)) {
            num = this.number + (direction > 0 ? 1 : -1);
            ob = this._find(num);
            if (!is_null(ob)) {
                this.current = ob;
                this.number = num;
                is_found = true;
            }
        }

        this.reset();

        if (!is_found) {
            this.is_end_of_data = (
                (direction < 0 && this.page == 1) || 
                (direction > 0 && this.page == this.pages)
                ) ? true : false;

            this.is_top = (direction < 0 && !this.is_end_of_data) ? true : false;
            this.is_bottom = (direction > 0 && !this.is_end_of_data) ? true : false;
        }

        if (this.IsTrace)
            alert('move:'+this.number+':'+this.is_top+':'+this.is_bottom);

        return is_found || this.is_top || this.is_bottom;
    },

    home: function() {
        return this._refresh(1);
    },

    up: function() {
        return this._move(-1) === true ? this._refresh(0) : false;
    },

    down: function() {
        return this._move(1) === true ? this._refresh(0) : false;
    },

    end: function() {
        return this._refresh(1);
    }
};
