// ***********************
// BANKPERSO DB CONTROLLER
// -----------------------
// Version: 2.00
// Date: 12-11-2021

var current_order_type = -1;            // Order type (otype) code value
var current_order_code = '';            // Current Order code value: C-000-0000

var LOG_SORT = new Array('', 'TOTAL-DESC', 'TOTAL-ASC', 'DATE-DESC', 'DATE-ASC', 'CUSTOM-CODE-DESC', 'CUSTOM-CODE-ASC');

var current_sort = 0;                   // Sorting index
var page_sort_title = '';               // Sorting title tag value

var current_line = null;                // Current (selected on Data section) line row
var current_subline = null;             // Current (selected on LogData section) subline row
var current_tabline = null;             // Current (selected on TabData section) line row

var current_row_id = null;              // ID of current (selected on Data section) row

var selected_data_menu_id = '';         // Selected Data menu item (Parameters/Products)
var selected_data_menu = null;          // Selected Data menu Object
var selected_dropdown = null;           // Selected Dropdown menu Object

var is_search_activated = false;        // Search is active
var is_search_focused = false;          // Search input in focus

var search_context = '';                // Current search context value

// ****************************************************

var default_row_item = {'num':0, 'id':null, 'ob':null};
var selected_row = 
{
    'admin'         : new Object(),
    'article'       : new Object(),
    'batch'         : new Object(),
    'change-status' : new Object(),
    'reference'     : new Object(),
    'event'         : new Object(),
    'file'          : new Object(),
    'order'         : new Object(),
    'preload'       : new Object(),
    'pers'          : new Object(),
    'oper'          : new Object(),
    'review'        : new Object(),
    'history'       : new Object(),

//  ---  Default Tab Line ---

    'tabline'       : new Object(),
};

function SelectedReset() {
    for(var key in selected_row) {
        selected_row[key] = new Object();
        for(var item in default_row_item)
            selected_row[key][item] = default_row_item[item];
    }
}

function SelectedSetItem(key, item, ob) {
    if (IsLog)
        console.log('SelectedSetItem:'+key+':'+item+', id:['+(ob && ob.attr('id'))+']');

    selected_row[key][item] = ob;
    if (item == 'ob')
        selected_row[key]['id'] = !is_null(ob) ? $_get_item_id(ob) : null;
}

function SelectedGetItem(key, item) {
    return !is_null(selected_row[key]) && (item in selected_row[key]) ? selected_row[key][item] : null;
}

// =======================
// Selected Items Handlers
// =======================

var $ActiveSelector = {
/***
 * Auxiliary class to manage selection between Subline and Tabline areas.
 * Used for instance by `configurator.js` only.
 */

    selector : null,

    release: function() {
        if (is_null(this.selector))
            return;

        this.selector.release();
    },

    reset: function(ob) {
        this.selector = ob;

        if (IsLog)
            console.log('$ActiveSelector.reset:'+this.selector.alias);
    },

    is_movable: function() {
        return this.selector.is_movable();
    },

    get_current: function() {
        return this.selector.get_current();
    },

    onRefresh: function(ob) {
        return this.selector.onRefresh(ob);
    },

    onProgress: function(ob) {
        return this.selector.onProgress(ob);
    },

    up: function() {
        return this.selector.up();
    },
    
    down: function() {
        return this.selector.down();
    },

    home: function() {
        return this.selector.home();
    },
    
    pgup: function() {
        return this.selector.pgup();
    },
    
    pgdown: function() {
        return this.selector.pgdown();
    },
    
    end: function() {
        return this.selector.end();
    }
};

var $LineSelector = {
/***
 * Basic class to manage selection of Line area: moving inside control (up|down|pgup|pgdown|begin|end).
 * 
 * Controls:
 *    $("#position"): pointer of current state inside area: page|pages|per_page|line
 * 
 * Protected methods:
 *    _find:
 *    _move:
 *    _refresh:     push $onToggleSelectedClass submit action
 * 
 * Public methods:
 *    init:
 *    reset:
 *    set_current:  
 *    set_position: 
 *    get_id:
 *    get_current:
 *    onRefresh:
 * 
 */
    container : null,

    // ===================
    // Line Selector Class
    // ===================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    // ----------------------------------------------------------
    // Current page (position): [0]:page, [1]:pages, [2]:per_page
    // ----------------------------------------------------------

    position  : new Array(),
    current   : null,
    oid       : '',
    number    : 0,

    page      : 0,
    pages     : 0,
    per_page  : 0,
    line      : 0,

    is_top    : false,
    is_bottom : false,

    is_end_of_data : false,

    init: function() {
        this.container = $("#line-content");
        $("#position").val().split(':').forEach(function(x) { this.push(parseInt(x)); }, this.position);

        this.page = this.position[0];
        this.pages = this.position[1];
        this.per_page = this.position[2];
        this.line = this.position[3];

        if (this.IsTrace)
            alert(this.position);

        this.current = null;
        this.oid = '';
        this.number = 0;

        var ob = $("tr[class~='selected']", this.container);
        $onToggleSelectedClass(LINE, ob, 'add', null);

        this.set_current(ob);

        this.reset();
    },

    reset: function() {
        this.is_top = this.is_bottom = this.is_end_of_data = false;
    },

    get_id: function() {
        return $_get_item_id(this.current);
    },

    get_current: function() {
        return this.current;
    },

    set_current: function(ob) {
        if (is_null(ob))
            return;

        this.current = ob;
        this.oid = ob.attr('id');
        this.number = parseInt($_get_item_id(ob, 2));

        this.set_position(this.page, this.number);

        if (this.IsTrace)
            alert(this.number);
    },

    set_position: function(page, line) {
        $("#position").val(page+':::'+line);
    },

    onReset: function() {
        this.reset();
        return this._refresh(0);
    },

    onRefresh: function(ob) {
        this.set_current(ob);
        return this._refresh(0);
    },

    onFormSubmit: function() {
        this.set_position(1, 1);
    },

    get_items: function() {
        return this.container.find(".line");
    },

    getSelectedItems: function(position) {
        var items = new Array();

        this.container.find(".line").each(function(index, x) {
            if (this.IsTrace)
                alert($(x).attr('id')+':'+parseInt($_get_item_id($(x), 2)));

            items.push(is_null(position) ? $(x) : parseInt($_get_item_id($(x), position)));
        });

        return items;
    },

    _find: function(num) {
        var ob = null;

        this.container.find(".line").each(function(index, x) {
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
        var page, line;

        if (this.IsLog)
            console.log('$LineSelector._refresh:'+this.number+':'+this.is_top+':'+this.is_bottom+':'+new_page);

        // --------------------
        // Refresh current page
        // --------------------

        if (new_page == 0 && !(this.is_top || this.is_bottom || this.is_end_of_data)) {
            $onToggleSelectedClass(LINE, this.current, 'submit', null);
            exit = true;
        }

        // ---------------
        // Open a new page
        // ---------------

        else {        
            if (new_page == 1) {
                page = new_page;
                line = 1;
            }
            else if (new_page > 0) {
                page = new_page;
                line = this.number;
            }
            else if (this.is_top) {
                page = this.page - 1;
                line = this.per_page;
            }
            else if (this.is_bottom) {
                page = this.page + 1;
                line = 1;
            }
            else
                return true;

            this.set_position(page, line);

            MakeFilterSubmit(9, page);

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
                //this.set_current(ob);
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

    pgup: function() {
        return this.page > 1 ? this._refresh(this.page-1) : false;
    },

    pgdown: function() {
        return this.page < this.pages ? this._refresh(this.page+1) : false;
    },

    end: function() {
        return this._refresh(this.pages);
    }
};

var $SublineSelector = {
    container : null,

    // ======================
    // Subline Selector Class
    // ======================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    // ----------------
    // Config Object ID
    // ----------------

    alias     : '',         // Subline Object name
    mode      : '',

    current   : null,
    oid       : '',
    number    : 0,

    page      : 0,
    pages     : 0,
    per_page  : 0,
    line      : 0,

    is_top    : false,
    is_bottom : false,

    is_end_of_data : false,

    init: function() {
        this.container = $("#subline-content");

        if (this.IsLog)
            console.log('$SublineSelector.init');

        this.alias = SUBLINE;

        this.page = 1;
        this.pages = 1;
        this.line = 1;

        this.release();

        var ob = $("tr[class~='selected']", this.container);
        SelectedSetItem(this.alias, 'ob', ob, null);

        this.set_current(ob);

        this.reset();
    },

    release: function() {
        this.current = null;
        this.oid = '';
        this.number = 0;

        SelectedSetItem(this.alias, 'ob', null);
    },

    reset: function() {
        this.is_top = this.is_bottom = this.is_end_of_data = false;

        var size = this.container.find(".subline").length || 0;
        this.per_page = size;

        if (this.number > this.per_page)
            this.number = this.per_page;
    },

    get_id: function() {
        return $_get_item_id(this.current);
    },

    get_current: function() {
        return this.current;
    },

    set_current: function(ob) {
        if (is_null(ob))
            return;

        this.current = ob;
        this.oid = ob.attr('id');
        this.number = parseInt($_get_item_id(ob, 2));

        if (this.IsLog)
            console.log('$SublineSelector.set_current:'+is_null(this.current)+':'+this.oid+':'+this.number);

        $ActiveSelector.reset(this);
    },

    onRefresh: function(ob) {
        if (ob === null) {
            SelectedSetItem(this.alias, 'ob', null);
            this.is_end_of_data = true;

            $ActivateInfoData(0);
        }

        this.set_current(ob);
        return this._refresh(0);
    },

    onProgress: function(ob) {
        return isWebServiceExecute;
    },

    _find: function(num) {
        var ob = null;

        if (is_null(num) || num <= 0)
            return null;

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
        var exit = true;
        var line;

        if (this.IsLog)
            console.log('$SublineSelector._refresh:'+new_page+':'+this.is_top+':'+this.is_bottom+':'+this.is_end_of_data);

        // --------------------
        // Refresh current page
        // --------------------

        if (new_page == 0 && !(this.is_top || this.is_bottom || this.is_end_of_data)) {
            $HideLogPage();

            SelectedSetItem(this.alias, 'ob', this.current);
            //$onToggleSelectedClass(SUBLINE, this.current, 'submit', null);

            $ShowSubline();
        } 
        else
            exit = false;

        return exit;
    },

    _move: function(direction, number) {
        var is_found = false;
        var num = 0;

        // ------------------------
        // Move inside current page
        // ------------------------

        if ((direction > 0 && this.number < this.per_page) || (direction < 0 && this.number > 1))
            num = this.number + (direction > 0 ? 1 : -1);
        else if (direction == 0 && !is_null(number))
            num = number;
        
        var ob = this._find(num);

        if (!is_null(ob)) {
            this.set_current(ob);
            is_found = true;
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
            alert('move:'+this.number+':'+this.is_top+':'+this.is_bottom+':'+this.is_end_of_data);

        return is_found || this.is_top || this.is_bottom;
    },

    is_movable: function() {
        return !this.is_end_of_data && this.per_page > 0 ? true : false;
    },

    home: function() {
        return this._move(0, 1) === true ? this._refresh(0) : false;
    },

    up: function() {
        return this._move(-1) === true ? this._refresh(0) : false;
    },

    down: function() {
        return this._move(1) === true ? this._refresh(0) : false;
    },

    end: function() {
        return this._move(0, this.per_page) === true ? this._refresh(0) : false;
    }
};

var $TablineSelector = {
    container : null,

    // ======================
    // Tabline Selector Class
    // ======================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    // ----------------
    // Config Object ID
    // ----------------

    alias     : '',         // Tabline Object name
    mode      : '',
    
    // ------------------------------------------------
    // Current page: page=pages=1, per_page:rows number
    // ------------------------------------------------

    current   : null,
    oid       : '',
    number    : 0,

    page      : 0,
    pages     : 0,
    per_page  : 0,
    line      : 0,

    is_top    : false,
    is_bottom : false,

    is_end_of_data : false,

    init: function(tab) {
        this.set_mode(tab);

        this.alias = TABLINE;

        if (this.IsLog)
            console.log('$TablineSelector.init, mode:'+this.get_mode(), 'alias:'+this.alias);

        this.container = $("#"+this.get_mode()+"-container");

        this.page = 1;
        this.pages = 1;
        this.line = 1;

        this.release();

        var ob = $("tr[class~='selected']", this.container);
        if (is_null(ob) || is_empty(ob.attr('id')))
            //ob = this.container.find("tr[class~='tabline']").first();
            ob = $("tr[class~='tabline']", this.container).first();

        SelectedSetItem(this.alias, 'ob', ob);

        this.reset();

        this.onRefresh(ob);
    },

    release: function() {
        this.current = null;
        this.oid = '';
        this.number = 0;

        SelectedSetItem(this.alias, 'ob', null);
    },

    reset: function() {
        this.is_top = this.is_bottom = this.is_end_of_data = false;

        var size = this.container.find(".tabline").length || 0;
        this.per_page = size;

        if (this.number > this.per_page)
            this.number = this.per_page;
    },

    get_id: function() {
        return $_get_item_id(this.current);
    },

    get_current: function() {
        return this.current;
    },

    get_mode: function() {
        return this.mode;
    },

    set_mode: function(ob) {
        this.mode = ob && ob.attr('id').split('-').slice(-1)[0];
    },

    set_current: function(ob) {
        if (is_null(ob))
            return;

        this.current = ob;
        this.oid = ob.attr('id');
        this.number = parseInt($_get_item_id(ob, 2));

        if (this.IsLog)
            console.log('$TablineSelector.set_current:'+is_null(this.current)+':'+this.oid+':'+this.number);

        $ActiveSelector.reset(this);
    },

    set_current_by_id: function(id) {
        var ob = $("tr[id^='row-"+this.alias+":"+id+"']", this.container);

        if (this.IsLog)
            console.log('$TablineSelector.set_current_by_id:'+id, ob);

        this.onRefresh(ob);
    },

    onRefresh: function(ob) {
        if (ob === null) {
            SelectedSetItem(this.alias, 'ob', null);
            this.is_end_of_data = true;
        }

        this.set_current(ob);
        return this._refresh(0);
    },

    onProgress: function(ob) {
        return false;
    },

    _find: function(num) {
        var ob = null;

        if (is_null(num) || num <= 0)
            return null;

        this.container.find(".tabline").each(function(index, x) {
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
        var exit = true;
        var line;

        if (this.IsLog)
            console.log('$TablineSelector._refresh:'+this.alias+':'+new_page+':'+this.is_top+':'+this.is_bottom+':'+this.is_end_of_data);

        // --------------------
        // Refresh current page
        // --------------------

        if (new_page == 0 && !(this.is_top || this.is_bottom || this.is_end_of_data)) {
            var ob = SelectedGetItem(this.alias, 'ob');
            if (!is_null(ob))
                $onToggleSelectedClass(this.alias, ob, 'remove', null);
            //$onToggleSelectedClass(this.alias, null, 'remove');
            $onToggleSelectedClass(this.alias, this.current, 'add', null);
        } 
        else
            exit = false;

        if (typeof $onTablineSelect === 'function')
            $onTablineSelect();

        return exit;
    },

    _move: function(direction, number) {
        var is_found = false;
        var num = 0;

        // ------------------------
        // Move inside current page
        // ------------------------

        if ((direction > 0 && this.number < this.per_page) || (direction < 0 && this.number > 1))
            num = this.number + (direction > 0 ? 1 : -1);
        else if (direction == 0 && !is_null(number))
            num = number;
        
        var ob = this._find(num);

        if (!is_null(ob)) {
            this.set_current(ob);
            is_found = true;
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
            alert('move:'+this.number+':'+this.is_top+':'+this.is_bottom+':'+this.is_end_of_data);

        return is_found || this.is_top || this.is_bottom;
    },

    is_movable: function() {
        return !this.is_end_of_data && this.per_page > 0 ? true : false;
    },

    home: function() {
        return this._move(0, 1) === true ? this._refresh(0) : false;
    },

    up: function() {
        return this._move(-1) === true ? this._refresh(0) : false;
    },

    down: function() {
        return this._move(1) === true ? this._refresh(0) : false;
    },

    end: function() {
        return this._move(0, this.per_page) === true ? this._refresh(0) : false;
    }
};

var $TabSelector = {
    container : null,

    // ===================
    // Tabs Selector Class
    // ===================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    current   : null,
    number    : 0,
    count     : 0,

    init: function() {
        this.container = $("#tab-content");
        this.count = this.container.children().length;

        if (this.IsTrace)
            alert('$TabSelector.count:'+this.count);

        this.reset();
    },

    reset: function() {
        this.set_current(1);
    },

    set_current: function(num) {
        this.number = num;
    },

    get_current: function() {
        return this.current;
    },

    set_current_by_id: function(id) {
        var ob = $("#"+id, this.container);

        if (this.IsLog)
            console.log('$TabSelector.set_current_by_id:'+id, ob);

        this.onClick(ob);
    },

    onClick: function(ob) {
        var id = ob.attr('id');

        this.onMove(id);

        if (id != default_menu_item)
            $SublineSelector.release();

        if (typeof $onTabSelect === 'function')
            $onTabSelect(ob);
    },

    onMove: function(id) {
        this._move(id);
    },

    _move: function(id) {
        var is_found = false;
        var number = 1;

        this.container.find(".menu").each(function(index, x) {
            if ($(x).attr('id') == id)
                is_found = true;
            if (!is_found)
                ++number;
        });

        this.number = number;

        if (this.IsLog)
            console.log('$TabSelector._move:'+id+':'+this.number);
    },

    _find: function(direction) {
        var num = this.number + direction;
        var number = num > this.count ? 1 : (num == 0 ? this.count : num);
        var found_ob = null;
        var last_ob = null;

        this.container.find(".menu").each(function(index, x) {
            var ob = $(x);
            var i = index + 1;
            var is_invisible = ob.hasClass(CSS_INVISIBLE);
            /*
            if ($TabSelector.IsTrace)
                alert(ob.attr('id')+':'+index+':'+number);
            */
            if (found_ob == null) {
                if (i > number && direction == 1) {
                    if (!is_invisible)
                        found_ob = ob;
                }
                else if (i == number) {
                    if (!is_invisible)
                        found_ob = ob;
                    else if (direction == -1 && last_ob != null)
                        found_ob = last_ob;
                }
                else {
                    if (!is_invisible)
                        last_ob = ob;
                }
            }
        });

        this.number = number;

        if (this.IsTrace)
            alert('found:'+(found_ob ? found_ob.attr('id') : 'null'));

        return found_ob;
    },

    _refresh: function(direction) {
        var ob = this._find(direction);
        if (!is_null(ob)) {
            if (typeof $onTabSelect === 'function')
                return $onTabSelect(ob);
        }
        return false;
    },

    left: function() {
        return this._refresh(-1);
    },

    right: function() {
        return this._refresh(1);
    },

    tab: function() {
        return this.right();
    }
};

function controller_menu_item(ob) {
    return $("a", ob);
}

var $MenuSelector = {
    container : null,

    // ==============================
    // Menu Selector Class (mainmunu)
    // ==============================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    current   : null,
    number    : 0,
    count     : 0,
    items     : null,
    id        : null,

    init: function(id) {
        this.container = $("#mainmenu ul");
        this.items = $("li", this.container);
        this.count = this.items.length;

        if (this.IsTrace)
            alert('$MenuSelector.count:'+this.count);

        this.set_current('mainmenu-'+id);
    },

    set_current: function(id) {
        var current = null;
        var num = 0;
        this.items.each(function() {
            var ob = controller_menu_item($(this));
            if (is_null(current)) {
                if (ob.prop("id") == id)
                    current = ob;
                ++num;
            }
        });
        this.current = current;
        this.number = num;
        this.id = id;

        if (this.IsDebug)
            alert('$MenuSelector.set_current:'+this.id+':'+this.number);
    },

    get_current: function() {
        return this.current;
    },

    set_current_by_id: function(id) {
        var ob = $("#"+id, this.container);

        if (this.IsLog)
            console.log('$MenuSelector.set_current_by_id:'+id, ob);

        this.onClick(ob);
    },

    onClick: function(ob) {
        var id = ob.attr('id');

        this.onMove(id);

        if (typeof $onMenuSelect === 'function')
            $onMenuSelect(ob);
    },

    onMove: function(id) {
        this._move(id);
    },

    _move: function(id) {
        var is_found = false;
        var number = 1;

        this.items.each(function(index, x) {
            if ($(x).attr('id') == id)
                is_found = true;
            if (!is_found)
                ++number;
        });

        this.number = number;

        if (this.IsLog)
            console.log('$MenuSelector._move:'+id+':'+this.number);
    },

    _find: function(direction) {
        var num = this.number + direction;
        var number = num > this.count ? 1 : (num == 0 ? this.count : num);
        var found_ob = null;
        var last_ob = null;

        this.items.each(function(index, x) {
            var ob = $(x);
            var i = index + 1;
            var is_invisible = ob.hasClass(CSS_INVISIBLE);
            /*
            if ($MenuSelector.IsDebug)
                alert(ob.attr('id')+':'+index+':'+number);
            */
            if (found_ob == null) {
                if (i > number && direction == 1) {
                    if (!is_invisible)
                        found_ob = ob;
                }
                else if (i == number) {
                    if (!is_invisible)
                        found_ob = ob;
                    else if (direction == -1 && last_ob != null)
                        found_ob = last_ob;
                }
                else {
                    if (!is_invisible)
                        last_ob = ob;
                }
            }
        });

        this.number = number;

        if (this.IsTrace)
            alert('$MenuSelector.found:'+this.number);

        return found_ob;
    },

    _refresh: function(direction) {
        var ob = this._find(direction);
        if (!is_null(ob)) {
            if (typeof $onMenuSelect === 'function')
                return $onMenuSelect(controller_menu_item(ob));
        }
        return false;
    },

    left: function() {
        return this._refresh(-1);
    },

    right: function() {
        return this._refresh(1);
    },
};

var $DblClickAction = {
    control   : null,

    // =========================
    // DoubleClick Handler Class
    // =========================

    clicks    : 0,
    timeout   : 300,
    timer     : null,

    single    : null,
    double    : null,

    reset: function() {
        this.control = null;
        this.clicks = 0;
        this.timer = null;
        this.single = null;
        this.double = null;
    },

    click: function(single, double, control, timeout) {
        this.control = control;
        this.single = single;
        this.double = double;

        this.clicks++;

        if (this.clicks === 1) {

            this.timer = setTimeout(function() {
                var self = $DblClickAction;

                // -------------------
                // Single-click action
                // -------------------

                self.single && self.single(self.control);
                self.reset();

            }, timeout || this.timeout);

        } else if (!is_null(this.timer)) {

            // -------------------
            // Double-click action
            // -------------------

            clearTimeout(this.timer);

            this.single && this.single(this.control);
            this.double && this.double(this.control);
            this.reset();

        }
    }
};

var $DraggableImage = {
    image     : null,
    params    : new Object(),

    // =======================
    // Draggable Image Handler
    // =======================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    set_param: function(params, key, value) {
        this.params[key] = getObjectValueByKey(params, key) || value;
    },

    get_param: function(key) {
        return this.params[key];
    },

    init: function(params) {
        this.set_param(params, 'width_padding', 0);
        this.set_param(params, 'height_padding', 0);

        if (this.IsLog)
            console.log('init', this.params);

        this.image = null;
    },

    onEnter: function(ob, id, e) {
        if (is_null(ob))
            ob = $(e.target);

        if (is_null(this.image)) {
            var control = $("#"+id);

            if (is_null(control))
                return;

            this.image = {
                'ob'        : ob, 
                'id'        : id,
                'control'   : control, 
                'width'     : control.width() + this.get_param('width_padding'), 
                'height'    : control.height() + this.get_param('height_padding')
            }; 

            this.image.ob.css({ 'cursor':'pointer' });
            this.image.control.removeClass('hidden');
        }

        if (this.IsDebug)
            console.log('enter', (!is_null(this.image) ? this.image.id : null), e.pageX, e.pageY);

        if (this.IsDebug)
            console.log('screen', $_height('screen-max'), $_width('screen-max'));
    },

    onLeave: function(e) {
        if (this.IsLog)
            console.log('leave', e.pageX, e.pageY);

        if (!is_null(this.image)) {
            this.image.control.addClass('hidden');
            this.image.ob.css({ 'cursor':'default' });

            this.image = null;
        }
    },

    onMove: function(e) {
        if (is_null(this.image)) 
            return;

        var scrolltop = int($(window).scrollTop());
        var x = e.pageX;
        var y = e.pageY;
        var top = 0;
        var left = 0;
        var height_limit = int($_height('screen-max') / 2.5);
        //var ob_left = this.image.ob.position().left;
        //var size_width = int(($_width('max') - this.image.width) / 2);

        if (y - scrolltop > height_limit) {
            top = y - this.image.height - 10;
            left = x - this.image.width - 10;
        }
        else {
            top = y + 20;
            left = x - this.image.width - 10;
        }

        var screen_width = $_width('screen-max');

        if (x - this.image.width < 0 || x + this.image.width > screen_width - 20)
            //left = x - int((screen_width - this.image.width) / 2);
            left = x - int(this.image.width / 2);

        //console.log(left + this.image.width, screen_width);

        if (left + this.image.width > screen_width - 20)
            left = screen_width - this.image.width - 20;

        if (this.IsLog)
            console.log('move', x, y, top, left, scrolltop, this.image.control.attr('id'));

        this.image.control.offset({ top: top, left: left });
    }
};

// ===============
// Action handlers
// ===============

function $GetLog(action, callback) {
}

function $GetLogItem(source) {
}

// ============
// WEB-SERVICES
// ============

function $web_free() {
/***
 *  Semaphore: is controller busy or not true|false.
 */
    return !isWebServiceExecute ? true : false;
}

function $is_shown_error() {
/***
 *  Semaphore: is error shown on the screen true|false.
 */
    return is_show_error ? true : false;
}

function $web_busy() {
/***
 *  Semaphore: is controller busy true|false.
 */
    return (isWebServiceExecute || is_show_error) ? true : false;
}

function $web_uploader(action, data, handler) {
/***
 *  Storage Data Uploader AJAX-backside handler.
 *  Used to download/upload files.
 *
 *  Action:        action number (000-999)
 *  Data:          data of file to upload
 *  Handler:       handler (to process the returned data)
 *
 *  Hard link.
 */
    if (!$web_free())
        return;

    if (IsLog)
        console.log('$web_uploader:', action);

    // ------------
    // START ACTION
    // ------------

    is_loaded_success = false;

    $ShowSystemMessages(true, true);
    $ShowLoader(1);

    $.ajax({
        type: 'POST',
        url: $SCRIPT_ROOT + '/storage/uploader',
        data: data,
        contentType: false,
        cache: false,
        processData: false,
        //async: false,

        success: function(x, status, ob) {
            is_loaded_success = true;

            $ShowLoader(-1);

            var errors = x['errors'];

            if (!is_empty(errors)) {
                var msg = errors.join('<br>');
                $ShowError(msg, true, true, false);
            }

            else if (!is_null(handler)) {

                var t = typeof handler;

                if (IsTrace)
                    alert('$web_uploader.handler:'+action+':'+t);

                handler(x);
            }
        },
        
        error: function(ob, status, error) {
            is_loaded_success = false;

            $ShowLoader(-1);
        },

        complete: function(ob, status) {
            if (IsLog)
                console.log('$web_uploader.complete, status:', status, is_loaded_success);
        }
    });
}

function $web_logging(action, handler, params) {
/***
 *  General AJAX-backside handler.
 *  Used to interact with the core of the application.
 *
 *  Action:        action number (000-999)
 *  [Handler]:     handler (to process the returned data)
 *  [Params]:      query data (object)
 *
 *  System args and state-items:
 * 
 *  $SCRIPT_ROOT - root-part of URL
 *  loader_page  - page name, may be omitted (provision|workflow...)
 *  loaderURI    - path to backside handler (/loader)
 * 
 *  isWebServiceExecute: loader is busy 1|0
 *  is_show_error: got error or not 1|0
 * 
 *  Hard link.
 */
    var uri = $SCRIPT_ROOT + loader_page + loaderURI;

    if (IsDeepDebug)
        alert('>>> web_logging:'+uri+':'+isWebServiceExecute+':'+is_show_error);

    if ($web_busy())
        return;

    var current_action = action;
    var args = new Object();

    if (IsLog)
        console.log('$web_logging, action:'+action+':'+selected_menu_action, uri);

    // -----------------------
    // Check Action parameters
    // -----------------------

    if (action == default_action) {
        args = {
            'action' : action,
            'selected_menu_action' : selected_menu_action
        };

        switch (action) {
            case '100':
                args['user_id'] = SelectedGetItem(LINE, 'id');
                current_action = '000';
                break;
            case '200':
                break;
            case '300':
                args['file_id'] = SelectedGetItem(LINE, 'id');
                args['batchtype'] = $("#batchtype").val();
                args['batchstatus'] = $("#batchstatus").val();
                break;
            case '400':
                break;
            case '500':
                args['order_id'] = SelectedGetItem(LINE, 'id');
                break;
            case '600':
                args['file_id'] = SelectedGetItem(LINE, 'id');
                args['filter-batchtype'] = $("#batchtype").val();
                break;
            case '700':
                args['pers_id'] = SelectedGetItem(LINE, 'id');
                break;
            case '800':
                args['order_id'] = SelectedGetItem(LINE, 'id');
                args['batchtype'] = $('input[name=batchtype]:checked').val();
                args['operator'] = $("#operator").val();
                break;
            case '830':
                args['order_id'] = SelectedGetItem(LINE, 'id');
                break;
        }

    } else if (action > '870') {
        args = {
            'action'                : action,
            'order_id'              : getattr(params, 'order_id', null),
        };

    } else if (action > '860') {
        var order_id = SelectedGetItem(LINE, 'id');

        args = {
            'action'                : action,
            'order_id'              : order_id,
        };

    } else if (action > '830') {
        var order_id = SelectedGetItem(LINE, 'id');
        var review_id = SelectedGetItem(SUBLINE, 'id');

        if (is_empty(order_id) && ['831','843','845'].indexOf(action) == -1) {
            order_id = getattr(params, 'order_id', null);
            review_id = getattr(params, 'review_id', null);
            
            if (is_empty(order_id) || is_empty(review_id))
                return;
        }

        args = {
            'action'                : action,
            'order_id'              : order_id,
            'review_id'             : review_id,
            'note'                  : $("#note").val(),
        };

        if (action == default_action && $TablineSelector.get_mode() == 'items')
            args['item_id'] = $TablineSelector.get_id();

        if (['832','833','834','835','846','854','857','858','859'].indexOf(action) > -1)
            current_action = default_action;

    } else if (action > '800') {
        var order_id = SelectedGetItem(LINE, 'id');
        var batch_id = SelectedGetItem(SUBLINE, 'id');

        if (action == default_log_action && batch_id == null)
            return;

        args = {
            'action'                : action,
            'order_id'              : order_id,
            'batch_id'              : batch_id,
            'batchtype'             : $('input[name=batchtype]:checked').val(),
            'operator'              : $("#operator").val(),
        };

    } else if (action > '700') {
        var pers_id = SelectedGetItem(LINE, 'id');
        var oper_id = SelectedGetItem(SUBLINE, 'id');

        args = {
            'action'                : action,
            'pers_id'               : pers_id,
            'oper_id'               : oper_id,
            'selected-items'        : $getSelectedItems()
        };

    } else if (action > '600') {
        var file_id = SelectedGetItem(LINE, 'id');
        var batch_id = SelectedGetItem(SUBLINE, 'id');

        args = {
            'action'                : action,
            'file_id'               : file_id,
            'batch_id'              : batch_id,
            'filter-batchtype'      : $("#batchtype").val(),
            'filter-tag'            : $("#tag").val(),
            'filter-tagvalue'       : $("#tagvalue").val(),
            'active_links'          : jsonify($ConfigSelector.get_active_links())
        };

    } else if (action > '500') {
        var order_id = SelectedGetItem(LINE, 'id');
        var event_id = SelectedGetItem(SUBLINE, 'id');

        args = {
            'action'                : action,
            'order_id'              : order_id,
            'event_id'              : event_id,
            'filter-client'         : $("#client").val(),
            'filter-action'         : $("#action").val(),
            'filter-config'         : $("#config").val(),
            'filter-type'           : $("#type").val(),
            'filter-search-context' : $("#search-context").val()
        };

    } else if (action > '400') {
        var preload_id = SelectedGetItem(LINE, 'id');
        var article = SelectedGetItem(SUBLINE, 'id');

        args = {
            'action'     : action,
            'preload_id' : preload_id,
            'article'    : article
        };

    } else if (action > '300') {
        var file_id = SelectedGetItem(LINE, 'id');
        var batch_id = SelectedGetItem(SUBLINE, 'id');

        if (action == default_log_action && batch_id == null)
            return;

        args = {
            'action'     : action,
            'file_id'    : file_id,
            'batch_id'   : batch_id
        };

    } else if (action > '200') {

        args = {
            'action'     : action
        };

    } else if (action > '100') {
        var user_id = SelectedGetItem(LINE, 'id');

        if (is_null(user_id))
            return;

        args = {
            'action'     : action,
            'user_id'    : user_id,
        };
    }

    if (!is_null(params))
        args['params'] = jsonify(params);

    args['current_sort'] = current_sort;

    var error = {
        'exchange_error'    : 0, 
        'exchange_message'  : '', 
        'error_description' : '', 
        'error_code'        : '', 
        'errors'            : ''
    };

    if (IsLog)
        console.log('$web_logging, args:'+reprObject(args), current_action);

    // ------------
    // START ACTION
    // ------------

    $TriggerActions(true);

    is_loaded_success = false;

    //alert(current_action+':'+$SCRIPT_ROOT+loaderURI);

    $ShowSystemMessages(true, true);
    $ShowLoader(1);

    $.post(uri, args, function(x) {
        var action = x['action'];

        if (IsTrace)
            alert('$web_logging.post:'+action);

        //if (current_action != x['action'])
        //    alert('--> post:'+action+':'+current_action+':'+default_action);

        var total = parseInt(x['total'] || 0);
        var status = x['status'];
        var path = x['path'];
        var data = x['data'];
        var props = x['props'];
        var columns = x['columns'];

        var refresh_state = true;

        // -----------------------
        // Server Exchange erorors
        // -----------------------

        error.exchange_error = parseInt(x['exchange_error'] || 0);
        error.exchange_message = x['exchange_message'];

        // --------
        // RESPONSE
        // --------

        $ShowLoader(-1);

        if (typeof log_callback_error === 'function' && should_be_updated) {
            var errors = x['errors'];
            log_callback_error(action, errors);
        }

        if (error.exchange_error)
            refresh_state = false;

        else if (!is_null(handler)) {

            var t = typeof handler;

            if (IsTrace)
                alert('$web_logging.handler:'+action+':'+t);

            handler(x);
        }

        // -----------------------------------------
        // Run default action (change LINE position)
        // -----------------------------------------

        else if (current_action == default_action)
        {
            $updateSublineData(current_action, x, props, total, status, path);
        }

        else if (action == '101') 
        {
            $ProfileClients.reset();
            $updateUserForm(data);
            $ProfileClients.update(x['profile_clients']);
            $updateUserPhoto(x['photo']);
            $getSettings(x['settings']);
            $getPrivileges(x['privileges']);
        }
        else if (['201','202'].indexOf(action) > -1) 
        {
            $StatusChangeDialog.open(action, data);
        }
        else if (action == default_log_action)
        {
            $updateLog(data, props);
        }
        else
        {
            $updateTabData(current_action, data, columns, total, status, path);
        }

        is_loaded_success = true;

        $TriggerActions(false);

        $ShowLogPage();

        // --------------------
        // Run Callback Handler
        // --------------------

        if (isCallback) {
            isCallback = false;

            if (typeof log_callback === 'function')
                log_callback(current_action, data, props);
        }

    }, 'json')
    .fail(function() {
        is_loaded_success = false;
    })
    .always(function() {
        if (page_state == -1)
            page_state = 0;

        $ShowLoader(-1);
        $TriggerActions(false);
    });
}
