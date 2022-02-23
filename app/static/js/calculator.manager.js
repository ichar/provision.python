// ********************************
// HELPER FUNCTION CONTROLS MANAGER
// --------------------------------
// Version: 1.01
// Date: 05-07-2017

// =======================
// Component control class
// =======================

var $PageScroller = {
    page      : { 'base':null, 'top':0, 'height':0 },
    control   : { 'ob':null, 'default_position':0, 'top':0, 'height':0, 'isDefault':0, 'isMoved':0, 'isShouldBeMoved':0 },
    position  : 0,

    IsTrace   : 0,
    IsLog     : 0,

    init: function() {
        this.position = $(window).scrollTop();

        var ob = $("#info-data");
        this.control.ob = ob;

        var base = $("#info-container");
        this.page.base = base;

        this.control.default_position = this.control.top = base.position().top;

        if (this.IsLog)
            console.log('init', this.control.default_position);
    },

    reset: function(force) {
        //
        // force=true - принудительная перерисовка нового инфоблока, либо изменение геометрии страницы
        //
        if (force || is_null(this.control.ob) || is_null(this.page.base))
            this.init();

        if (this.IsLog)
            console.log('reset', force);

        this.page.height = this.page.base.height();
        this.control.height = this.control.ob.height();
        
        this.checkPosition(force);
    },

    trace: function(force) {
        if (force || (this.IsTrace && this.control.isMoved))
            alert('--> control:'+
                this.control.ob.attr('id')+':'+
                int(this.control.default_position)+':'+
                this.control.top+':'+
                this.control.height+':'+
                this.control.isDefault+':'+this.control.isMoved+':'+this.control.isShouldBeMoved+
                ',page:'+
                this.position+':'+
                this.page.height
                );
    },

    checkPosition: function(reset) {
        /*
         *  this.control.default_position -- default position of control (always equal to `this.page.top`)
         *  this.control.top              -- offset from default position
         *  this.position                 -- scroll top
         *  flush > 0                     -- offset of base to invisible zone
         *  visible_page_size             -- visible height of page
         *  control_size                  -- full height of control with offset from default position
         */
        var x = int($(window).scrollTop());
        this.position = x;

        var flush = this.position - this.control.default_position;
        var visible_page_size = this.page.height - flush;
        var control_size = this.control.top + this.control.height;

        //alert(this.position+':'+int(flush)+':'+this.page.top);

        if (this.IsLog)
            console.log('checkPosition', flush, this.page.height, visible_page_size, control_size, reset);

        if (reset) {
            //
            // Инфоблок выше контейнера
            //
            if (this.control.height >= this.page.height)
                this.control.isDefault = 1;
            //
            // Контейнер не перекрыт
            //
            else if (flush <= 0)
                this.control.isDefault = 1;
            //
            // Контейнер перекрыт. Видимая часть контейнера меньше высоты инфоблока
            //
            else if (visible_page_size < this.control.height) {
                this.position = this.page.height - this.control.height + this.control.default_position;
                this.control.isShouldBeMoved = 1;
            }
            //
            // Суммарная высота инфоблока больше высоты контейнера
            // Сдвиг на величину смещения `this.position`
            //
            else if (control_size > this.page.height) {
                //this.position = 0; //this.page.height - control_size;
                this.control.isShouldBeMoved = 1;
            }
            /*
            else
                this.control.isShouldBeMoved = 1;
            */
        }
        else {
            //
            // Инфоблок выше контейнера
            //
            if (this.control.height >= this.page.height)
                this.control.isDefault = 1;
            //
            // Контейнер не перекрыт
            //
            else if (flush <= 0)
                this.control.isDefault = 1;
            //
            // Смещение выполнялось на предыдущем шаге ...
            //
            else if ((this.position == 0 || this.position <= this.control.top) && this.control.isMoved)
                this.control.isDefault = 1;
            //
            // Контейнер перекрыт ...
            //
            else if (this.position > this.control.top) {
                if (this.position <= this.control.default_position)
                    this.control.isDefault = 1;
                else if (this.control.height + flush <= this.page.height)
                    this.control.isShouldBeMoved = 1;
            }
        }

        //if (0 && (this.control.isDefault || this.control.isShouldBeMoved))
        //    alert('--> '+int(this.control.top)+':'+this.position+' flush:'+int(flush)+':'+this.control.isMoved+':'+this.control.isShouldBeMoved+':'+this.control.isDefault);

        this.move();
    },

    move: function() {
        var top = null;

        if (is_null(this.control.ob))
            return;

        if (this.IsLog)
            console.log('move', this.position, this.page.height, this.control.top, this.control.height, 
                this.control.isDefault, this.control.isShouldBeMoved);

        if (this.control.isDefault) {
            top = 0;
            this.control.isDefault = 0;
            this.control.isMoved = 0;
        }
        else if (this.control.isShouldBeMoved) {
            top = int(this.position - this.control.default_position);
            if (top < 0) {
                if (this.page.height > this.control.height)
                    top = this.page.height - this.control.height;
                else
                    top = 0;
            }
            this.control.isShouldBeMoved = 0;
            this.control.isMoved = 1;
        }

        if (top != null && top >= 0) {
            this.control.ob.css({ 'top' : top.toString()+'px', 'position' : 'relative' });
            this.control.top = top;
        }

        this.trace();
    }
};
