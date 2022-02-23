
    $("#sidebarFrame").mouseover(function(e) {
        $SidebarControl.onFrameMouseOver();
        e.stopPropagation();
    })

    $("#dataFrame").mouseover(function(e) {
        /*
        var id = $(this).attr('id');
        var tid = e.target.id;

        if (id != tid) { 
            e.stopPropagation();

            alert('out:'+
                id+':'+
                e.currentTarget.id+':'+
                e.delegateTarget.id+':'+
                tid
            );

            return false;
        }
        */

        //var n = $(this).parents("div[id='sidebarFrame']").length;
        //var ob = $(this).parents().find('#sidebarFrame').first();
        /*
        var ob = $(e.target);
        var id = $(this).attr('id');
        var parent = null;

        if (id != 'sidebarFrame')
            alert('go?');

        //alert(e.target.id);

        ob.parents().each(function() {
            if ($(this).attr('id') == id) {
                parent = $(this);
            }
        });

        //alert('parent:'+(parent ? parent.attr('id') : parent));

        var child = null;

        ob.children().each(function() {
            if ($(this).attr('id') == id) {
                child = $(this);
            }
        });

        //alert('child:'+(child ? child.attr('id') : child));

        if (is_null(parent) && is_null(child)) {
            alert('go:'+
                id+':'+
                e.currentTarget.id+':'+
                e.delegateTarget.id+':'+
                e.target.id
            );
        }
        */

        $SidebarControl.onFrameMouseOut();
        e.stopPropagation();
    });
