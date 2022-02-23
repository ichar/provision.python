// ********************************
// HELPER FUNCTION CONTROLS MANAGER
// --------------------------------
// Version: 1.0
// Date: 31-08-2021

// =======================
// Component control class
// =======================

var $PageScroller = {
    page      : { 'base':null, 'top':0, 'height':0 },
    control   : { 'ob':null, 'default_position':0, 'top':0, 'height':0, 'isDefault':0, 'isMoved':0, 'isShouldBeMoved':0 },
    position  : 0,
    is_trace  : 0,

    init: function() {
    },

    reset: function(force) {
    },

    trace: function(force) {
    },

    checkPosition: function(reset) {
    },

    move: function() {
    }
};

var $BarcodeReader = {
    container   : null,
    box         : null,
    ob          : null,

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    action      : null,
    mode        : '',

    is_error    : false,

    init: function(ob) {
        this.ob = ob;
        this.box = $("#line-content");
        this.container = this.ob.parent().parent();

        if (this.IsTrace)
            alert('$BarcodeReader.init: id='+this.container.attr('id'));

        this.focus();
    },

    _show: function() {
        if (is_empty(this.mode))
            return;
    },

    check: function(x) {
        var errors = x['errors'];

        if (this.IsLog)
            console.log('$BarcodeReader.check, errors:', errors);

        if (!is_null(errors) && errors.length > 0) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
            this.is_error = true;

            this._show();
        }
    },

    focus: function() {
        this.ob.focus();
    },

    handle: function(x) {
        this.check(x);

        if (this.is_error)
            return;

        var data = getObjectValueByKey(x, 'data');

        switch (this.mode) {
            case 'refresh':
                this.refresh(data);
        }
    },

    reset: function() {
        this.ob.val('');
        
        this.box.html('');
        this.box.hide();
        
        this.focus();
    },

    refresh: function(data) {
        if (this.IsDebug)
            alert(reprObject(getObjectValueByKey(data, 'orders')));

        if (is_null(data)) {
            this.box.hide();
            return;
        }

        var attrs = data['attrs'];
        var columns = data['columns'];
        var titles = data['titles'];
        var headers = data['headers'];
        var keys = data['keys'];
        var orders = data['orders'];
        var items = data['items'];
        var total = data['total'];
        var sum_price = data['sum_price'];
        var currency = data['currency'];

        if (this.IsLog)
            console.log('$BarcodeReader.refresh, data:', data);
        
        this.box.html('');

        var content = '';

        content += 
            '<form action="" class="common-form" id="barcode-orders-form" method="POST" enctype="multipart/form-data">'+
            '<table class="lines" border="0">';

        orders.forEach(function(order, i) {
            var index = i+1;
            var id = order['TID'];
            var classes = getattr(order, 'classes', '');
            content += 
              '<tr class="line" id="row-line:'+id+':'+index+'">';

            columns.forEach(function(column, n) {
                var cls = getattr(classes, column, '');
                var title = getattr(titles[id], column, '');
                var value = order[column];
                content += 
                    '<td class="column '+column+' '+cls+'" title="'+title+'">'+value+'</td>';
            });

            content += 
              '</tr>';

            content += 
              '<tr>'+
                '<td colspan="'+columns.length+'">'+
                  '<div class="info-container" id="info:'+id+':'+index+'">'+
                    '<table class="info" border="0">';

            keys.forEach(function(key, p) {
                var header = headers[key]['title'];
                var cls = headers[key]['class'];
                var value = items[id][key];
                content += 
                    '<tr>'+
                      '<td><dt>'+header+':'+'</dt></td>'+
                      '<td class="'+cls+'">'+'<dd>'+value+'</dd>'+'</td>'+
                    '</tr>';
            });

            content += 
                    '</table>'+
                  '</div>'+
                '</td>'+
              '</tr>';
        });

        content += 
            '</table>'+
            '</form>';

        this.box.append(content);
        this.box.show();

        resize();
    },

    render: function(barcode) {
        if (this.IsTrace)
            alert('$BarcodeReader.render:['+barcode+']');

        this.action = '869';
        this.mode = 'refresh';

        var params = {'command':'render', 'barcode':barcode};

        $Handle(this.action, function(x) { $BarcodeReader.handle(x); }, params);
    }
};
