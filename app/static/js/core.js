// ==================================
//  Core javascript helper functions
// ==================================

function is_null(x) { return (typeof(x)=='undefined' || x === null || x === undefined) ? true : false; }

function int(x) { return parseInt(x); }

function is_empty(x) { return (is_null(x) || x.toString().length == 0 || (!isNaN(x) && int(x)==0)) ? true : false; }

function is_exist(x) { return !is_null(x) && x.length > 0 ? true : false; }

function mceil(value, multiple) { 
    var x=value % multiple; 
    if (x != 0) value += value > -1 ? multiple-x : -x; 
    return value; 
}

function capitalize(name) {
    return name.charAt(0).toUpperCase() + name.slice(1);
}

function getattr(ob, id, value) { return (typeof(ob)=='object' && !is_null(ob) && id in ob) ? ob[id] : value; }

function setattr(ob, id, value) { if (typeof(ob)=='object' && !is_null(ob) && id in ob) ob[id] = value; }

function getvalue(ob, value) { return (typeof(ob)=='object' && is_exist(ob)) ? ob.val() : value; }

function setvalue(ob, value) { if (typeof(ob)=='object' && is_exist(ob)) ob.val(value); }

function getprop(ob, prop, value) { return (typeof(ob)=='object' && is_exist(ob)) ? ob.prop(prop) : value; }

function setprop(ob, prop, value) { if (typeof(ob)=='object' && is_exist(ob)) ob.prop(value); }

function getsplitteditem(value, by_key, item, default_value)
{
    var x = !is_empty(value) ? value.split(by_key.length > 0 ? by_key : ':') : '';
    return x.length > 1 ? x[1] : (default_value.length > 0 ? default_value : '');
}

/**
 * Returns a updated query string for change location
 */
function makeLocation(query_string, key, value) {
    //alert(query_string.length);

    if (query_string.startswith('?'))
        query_string = query_string.slice(1);

    var args = '{'
        + (query_string.length > 0 ? '"'+decodeURI(query_string.replace(/&/g, '","').replace(/=/g,'":"'))+'"' : '') 
        + '}';

    //alert(args);

    params = JSON.parse(args);
    
    params[key] = value;
    
    var url = '?' + Object.keys(params).map(function(key) { return key+'='+params[key]; }).join('&');

    //alert(url);
    
    return url;
}

/**
 * Returns a random number between min (inclusive) and max (exclusive)
 */
function getRandomArbitrary(min, max) {
    return Math.random() * (max - min) + min;
}

/**
 * Returns a random integer between min (inclusive) and max (inclusive).
 * The value is no lower than min (or the next integer greater than min
 * if min isn't an integer) and no greater than max (or the next integer
 * lower than max if max isn't an integer).
 * Using Math.round() will give you a non-uniform distribution!
 */
function getRandomInt(min, max) {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Extra Math functions
 */
function ctg(x) { return 1 / Math.tan(x); }

function arcctg(x) { return Math.PI / 2 - Math.atan(x); }

// ----------------------------------------
//  Basic browser identification & version
// ----------------------------------------

var BrowserDetect = {
    init: function () {
        this.browser = this.searchString(this.dataBrowser).toLowerCase() || "An unknown browser";
        this.version = this.searchVersion(navigator.userAgent)
            || this.searchVersion(navigator.appVersion)
            || "an unknown version";
        this.OS = this.searchString(this.dataOS) || "an unknown OS";
    },
    searchString: function (data) {
        for (var i=0; i<data.length; i++)    {
            var dataString = data[i].string;
            var dataProp = data[i].prop;
            this.versionSearchString = data[i].versionSearch || data[i].identity;
            if (dataString) {
                if (dataString.indexOf(data[i].subString) != -1)
                    return data[i].identity;
            }
            else if (dataProp)
                return data[i].identity;
        }
    },
    searchVersion: function (dataString) {
        var index = dataString.indexOf(this.versionSearchString);
        if (index == -1) return;
        return parseFloat(dataString.substring(index+this.versionSearchString.length+1));
    },
    dataBrowser: [
        {
            string: navigator.userAgent,
            subString: "YaBrowser",
            identity: "Yandex"
        },
        {
            string: navigator.userAgent,
            subString: "Chrome",
            identity: "Chrome"
        },
        {   
            string: navigator.userAgent,
            subString: "OmniWeb",
            versionSearch: "OmniWeb/",
            identity: "OmniWeb"
        },
        {
            string: navigator.vendor,
            subString: "Apple",
            identity: "Safari",
            versionSearch: "Version"
        },
        {
            prop: window.opera,
            identity: "Opera",
            versionSearch: "Version"
        },
        {
            string: navigator.vendor,
            subString: "iCab",
            identity: "iCab"
        },
        {
            string: navigator.vendor,
            subString: "KDE",
            identity: "Konqueror"
        },
        {
            string: navigator.userAgent,
            subString: "Firefox",
            identity: "Firefox"
        },
        {
            string: navigator.vendor,
            subString: "Camino",
            identity: "Camino"
        },
        {   // for newer Netscapes (6+)
            string: navigator.userAgent,
            subString: "Netscape",
            identity: "Netscape"
        },
        {
            string: navigator.userAgent,
            subString: "MSIE",
            identity: "Explorer",
            versionSearch: "MSIE"
        },
        {
            string: navigator.userAgent,
            subString: "Trident",
            identity: "Explorer",
            versionSearch: "rv"
        },
        {
            string: navigator.userAgent,
            subString: "Gecko",
            identity: "Mozilla",
            versionSearch: "rv"
        },
        {   // for older Netscapes (4-)
            string: navigator.userAgent,
            subString: "Mozilla",
            identity: "Netscape",
            versionSearch: "Mozilla"
        }
    ],
    dataOS : [
        {
            string: navigator.platform,
            subString: "Win",
            identity: "Windows"
        },
        {
            string: navigator.platform,
            subString: "Mac",
            identity: "Mac"
        },
        {
            string: navigator.userAgent,
            subString: "iPhone",
            identity: "iPhone/iPod"
        },
        {
            string: navigator.platform,
            subString: "Linux",
            identity: "Linux"
        }
    ]

};
BrowserDetect.init();

var isYandex = BrowserDetect.browser == 'yandex' ? true : false;
var isChrome = BrowserDetect.browser == 'chrome' ? true : false;
var isFirefox = BrowserDetect.browser == 'firefox' ? true : false;
var isMozilla = BrowserDetect.browser == 'mozilla' ? true : false;
var isSafari = BrowserDetect.browser == 'safari' ? true : false;
var isOpera = BrowserDetect.browser == 'opera' ? true : false;
var isIE = BrowserDetect.browser == 'explorer' ? BrowserDetect.version : 0;

//alert(navigator.userAgent+':'+BrowserDetect.version+':'+isIE.toString());

// ------------------------------
//  Cross-browser event handlers
// ------------------------------

function addEvent(obj, evType, fn) {
    if (obj.addEventListener) {
        obj.addEventListener(evType, fn, false);
        return true;
    } else if (obj.attachEvent) {
        var r = obj.attachEvent("on" + evType, fn);
        return r;
    } else {
        return false;
    }
}

function removeEvent(obj, evType, fn) {
    if (obj.removeEventListener) {
        obj.removeEventListener(evType, fn, false);
        return true;
    } else if (obj.detachEvent) {
        obj.detachEvent("on" + evType, fn);
        return true;
    } else {
        return false;
    }
}

// ---------------------------------------------------------------------------------------------
//  quickElement(tagType, parentReference, textInChildNode, [, attribute, attributeValue ...]);
// ---------------------------------------------------------------------------------------------

function quickElement() {
    var obj = document.createElement(arguments[0]);
    if (arguments[2] != '' && arguments[2] != null) {
        var textNode = document.createTextNode(arguments[2]);
        obj.appendChild(textNode);
    }
    var len = arguments.length;
    for (var i = 3; i < len; i += 2) {
        obj.setAttribute(arguments[i], arguments[i+1]);
    }
    arguments[1].appendChild(obj);
    return obj;
}

// --------------------------------------------------------------------------------
//  Cross-browser xmlhttp object from http://jibbering.com/2002/4/httprequest.html
// --------------------------------------------------------------------------------

var xmlhttp;
/*@cc_on @*/
/*@if (@_jscript_version >= 5)
    try {
        xmlhttp = new ActiveXObject("Msxml2.XMLHTTP");
    } catch (e) {
        try {
            xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
        } catch (E) {
            xmlhttp = false;
        }
    }
@else
    xmlhttp = false;
@end @*/
if (!xmlhttp && typeof XMLHttpRequest != 'undefined') {
  xmlhttp = new XMLHttpRequest();
}

// -------------------------------------------------------------------------------
//  Find-position functions by PPK. See http://www.quirksmode.org/js/findpos.html
// -------------------------------------------------------------------------------

function findPosX(obj) {
    var curleft = 0;
    if (obj.offsetParent) {
        while (obj.offsetParent) {
            curleft += obj.offsetLeft - ((isOpera) ? 0 : obj.scrollLeft);
            obj = obj.offsetParent;
        }
        // IE offsetParent does not include the top-level 
        if (isIE && obj.parentElement){
            curleft += obj.offsetLeft - obj.scrollLeft;
        }
    } else if (obj.x) {
        curleft += obj.x;
    }
    return curleft;
}

function findPosY(obj) {
    var curtop = 0;
    if (obj.offsetParent) {
        while (obj.offsetParent) {
            curtop += obj.offsetTop - ((isOpera) ? 0 : obj.scrollTop);
            obj = obj.offsetParent;
        }
        // IE offsetParent does not include the top-level 
        if (isIE && obj.parentElement){
            curtop += obj.offsetTop - obj.scrollTop;
        }
    } else if (obj.y) {
        curtop += obj.y;
    }
    return curtop;
}

// ------------------------
//  Date object extensions
// ------------------------

Date.prototype.getCorrectYear = function() {
    // Date.getYear() is unreliable --
    // see http://www.quirksmode.org/js/introdate.html#year
    var y = this.getYear() % 100;
    return (y < 38) ? y + 2000 : y + 1900;
};

Date.prototype.getTwoDigitMonth = function() {
    return (this.getMonth() < 9) ? '0' + (this.getMonth()+1) : (this.getMonth()+1);
};

Date.prototype.getTwoDigitDate = function() {
    return (this.getDate() < 10) ? '0' + this.getDate() : this.getDate();
};

Date.prototype.getTwoDigitHour = function() {
    return (this.getHours() < 10) ? '0' + this.getHours() : this.getHours();
};

Date.prototype.getTwoDigitMinute = function() {
    return (this.getMinutes() < 10) ? '0' + this.getMinutes() : this.getMinutes();
};

Date.prototype.getTwoDigitSecond = function() {
    return (this.getSeconds() < 10) ? '0' + this.getSeconds() : this.getSeconds();
};

Date.prototype.getISODate = function() {
    return this.getCorrectYear() + '-' + this.getTwoDigitMonth() + '-' + this.getTwoDigitDate();
};

Date.prototype.getHourMinute = function() {
    return this.getTwoDigitHour() + ':' + this.getTwoDigitMinute();
};

Date.prototype.getHourMinuteSecond = function() {
    return this.getTwoDigitHour() + ':' + this.getTwoDigitMinute() + ':' + this.getTwoDigitSecond();
};

Date.prototype.getToday = function() {
  var mm = this.getMonth() + 1;
  var dd = this.getDate();
  return [this.getFullYear(), (mm>9 ? '' : '0') + mm, (dd>9 ? '' : '0') + dd].join('-');
};

// --------------------------
//  String object extensions
// --------------------------

String.prototype.pad_left = function(pad_length, pad_string) {
    var new_string = this;
    for (var i = 0; new_string.length < pad_length; i++) {
        new_string = pad_string + new_string;
    }
    return new_string;
};

String.prototype.startswith = function(s) {
    return (s && this.substr(0, s.length) == s) ? true : false;
};

String.prototype.endswith = function(s) {
    return (s && this.substr(-s.length) == s) ? true : false;
};

function strip(s) {
    return s.replace(/^\s+|\s+$/g, ''); // trim leading/trailing spaces
}

function dumping(ob) {
    var s = '';
    if (typeof(ob) != 'object')
        s = ob.toString();
    else {
        try { 
            for (p in ob) s += p+'['+ob[p].toString()+']:'; 
        }
        catch(e) {}
    }
    return s;
}

var htmlMap = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': '&quot;',
    "'": '&#39;',
    "/": '&#x2F;'
};

function escapeHtml(string) {
    return String(string).replace(/[&<>"'\/]/g, function (s) {
        return htmlMap[s];
    });
}

function cleanTextValue(string) {
    return String(string).replace(/[&<>"'\/]/g, function (s) {
        return '';
    });
}

function right(str, chr)
{
    return str.slice( -( chr ) );
}
function left(str, chr)
{
    return str.slice( 0, chr );
}

// ----------------------------------------
//  Get the computed style for and element
// ----------------------------------------

function getStyle(oElm, strCssRule) {
    var strValue = "";

    if (document.defaultView && document.defaultView.getComputedStyle) {
        strValue = document.defaultView.getComputedStyle(oElm, "").getPropertyValue(strCssRule);
    }
    else if (oElm.currentStyle) {
        strCssRule = strCssRule.replace(/\-(\w)/g, function (strMatch, p1){
            return p1.toUpperCase();
        });
        strValue = oElm.currentStyle[strCssRule];
    }

    return strValue;
}

// -----------------------
//  Hash table prototype
// -----------------------
/*  Usage: var attrs = new Hash(key1, value1, key2, value2, ...);
 *    key   -- name of the attribute, String
 *    value -- any valid data
 *  i.e. list of the argument pairs, can be omitted.
 */

function Hash()
{
    this.length = 0;
    this.items = new Array();
    for (var i = 0; i < arguments.length; i += 2) {
        if (typeof(arguments[i + 1]) != 'undefined') {
            this.items[arguments[i]] = arguments[i + 1];
            this.length++;
        }
    }
   
    this.removeItem = function(key)
    {
        var tmp_previous;
        if (typeof(this.items[key]) != 'undefined') {
            this.length--;
            var tmp_previous = this.items[key];
            delete this.items[key];
        }
        return tmp_previous;
    };

    this.getItem = function(key) {
        return this.items[key];
    };

    this.setItem = function(key, value)
    {
        var tmp_previous;
        if (typeof(value) != 'undefined') {
            if (typeof(this.items[key]) == 'undefined') {
                this.length++;
            }
            else {
                tmp_previous = this.items[key];
            }
            this.items[key] = value;
        }
        return tmp_previous;
    };

    this.hasItem = function(key)
    {
        return typeof(this.items[key]) != 'undefined';
    };

    this.clear = function()
    {
        for (var i in this.items) {
            delete this.items[i];
        }
        this.length = 0;
    };
}

// ------------------------
//  Functions under Arrays
// ------------------------

if (!Array.prototype.forEach) Array.prototype.forEach = function(callback) {
    var T, k;

    if (this == null) {
        throw new TypeError('this is null or not defined');
    }

    var O = Object(this);
    var len = O.length >>> 0;

    if (typeof callback !== 'function') {
        throw new TypeError(callback + ' is not a function');
    }

    if (arguments.length > 1) {
        T = arguments[1];
    }

    k = 0;
    while (k < len) {
        var kValue;
        if (k in O) {
            kValue = O[k];
            callback.call(T, kValue, k, O);
        }
        k++;
    }
};

if (!Array.prototype.indexOf) Array.prototype.indexOf = function(value) {
    for (var i=0; i<this.length; i++) {
        if (this[i] === value) return i;
    }
    return -1;
};

if (typeof Array.isArray === 'undefined') {
    Array.isArray = function(obj) {
        return Object.prototype.toString.call(obj) === '[object Array]';
    }
};

Array.prototype.isEqual = function(arr) {
    if (this.length != arr.length)
        return false;
    for(var i=0; i<this.length; i++) {
        if (this[i] != arr[i])
            return false;
    }
    return true;
};

Array.prototype.makeEqual = function() {
    var value = new Array();
    for(var i=0; i<this.length; i++) {
        value.push(this[i]);
    }
    return value;
};

Array.prototype.remove = function(value) {
    for(var i=0; i<this.length; i++) {
        if (this[i] === value) {
            this.splice(i,1);
            break;
        }
    }
};

Array.prototype.sum = function() {
    return this.reduce(function(a, b) { return a + b; }, 0);
};

Array.prototype.max = function() {
  return Math.max.apply(null, this);
};

Array.prototype.min = function() {
  return Math.min.apply(null, this);
};

Array.prototype.unique = function() {
    var a = this.concat();
    for(var i=0; i<a.length; ++i) {
        for(var j=i+1; j<a.length; ++j) {
            if(a[i] === a[j])
                a.splice(j--, 1);
        }
    }
    return a;
};

Array.prototype.union = function(arr) {
    var out = new Array();
    this.concat(arr).forEach(function(x) {
        if (out.indexOf(x) == -1)
            out.push(x);
    });
    return out;
};

// ------------------------
//  Functions under Objects
// ------------------------

function setObjectByValue(key, value) {
    var x = new Object();
    x[key] = value;
    return x;
}

function getObjectValueByKey(ob, key, value) {
    return !is_empty(ob) && (key in ob) ? ob[key] : value;
}

function objectKeys(ob) {
    return ob ? Object.keys(ob) : [];
}

function objectValues(ob) {
    return ob ? Object.values(ob) : [];
}

function objectItems(ob) {
    return ob ? Object.entries(ob) : [];
}

function objectKeyValues(ob) {
    return '{'+Object.keys(ob).map(function (key) { return key+':'+(typeof ob[key] === 'object' ? 'Object' : ob[key]); })+'}';
}

function reprObject(ob) {
    var s = is_null(ob) ? 'null' : '{'+Object.keys(ob).map(function (key) { 
        return key+':'+(typeof ob[key] === 'object' ? reprObject(ob[key]) : ob[key]); 
    })+'}';
    return s;
}

function reprObjectsList(obs) {
    var s = '';
    obs.forEach(function(item, index) {
        var x = '{'+Object.keys(item).map(function (key) { return key+':'+item[key]; })+'}';
        s += x.join(',');
    });
    return s;
}

function joinToPrint(values, delimeter) {
    return values.join(delimeter || ':');
}

function makeTempObject(s) {
    var ob = {};
    var items = s.split(',') || [];
    items.forEach(function(x) {
        var item = x.split(':');
        ob[item[0]] = item[1];
    });
    return ob;
}

function jsonify(ob) {
    if (typeof(ob) === 'object') {
        Object.keys(ob).map(function(key, index) {
            if (is_null(ob[key]))
                ob[key] = '';
        });
        return JSON.stringify(ob);
    }
    else
        return ob;
}

function ObjectAssign(target, sources) {
    // --------------------
    // JS CLASS INHERITANCE
    // --------------------
    // var $dialog = ObjectAssign({}, [class1, class2, ...]);
    // alert(joinToPrint(objectKeys($dialog), ':'));
    // alert(reprObject($dialog));
    //
    sources.forEach(function(source) {
        Object.defineProperties(
            target, 
            Object.keys(source).reduce(function(descriptors, key) {
                descriptors[key] = Object.getOwnPropertyDescriptor(source, key);
                return descriptors;
            }, {})
        );
    });
    return target;
}

// ---------------------
//  Functions under DOM
// ---------------------

function appendImageInside(parent, src, attrs) {
    var area = document.getElementById(parent);
    if (typeof(area) != 'object')
        return;
    var img = document.createElement('img');
    if (typeof(attrs) == 'object' && 'class' in attrs)
        img.className = attrs['class'];
    img.src = src;
    area.appendChild(img);
}

function preloadImages(items, callback) {
    var n = items.length;
    function ok() { 
        --n; 
        if (!n && typeof callback === 'function') 
            callback();
    }
    for(var i=0; i < n; i++) {
        if (!is_empty(items[i])) {
            var img = document.createElement('img');
            img.onload = img.onerror = ok;
            img.src = items[i];
        }
        else ok();
    }
}

function printDiv(divName, mode) {
    var printContents = document.getElementById(divName).innerHTML;

    switch (mode) {
        case 0:
            var originalContents = document.body.innerHTML;

            document.body.innerHTML = printContents;
            window.print();

            document.body.innerHTML = originalContents;
            window.location.reload();
            break;
        case 1:
            w = window.open();
            w.document.write(printContents);
            w.print();
            w.close();
    }
}

function xround(value) {
    return Math.round(value);
}

function removeClass(ob, c) {
    if (!is_null(ob) && ob.hasClass(c)) 
        ob.removeClass(c);
}

// ----------------
// Global namespace
// ----------------

var self = window;

var $SCRIPT_ROOT = '';
var $IS_MOBILE = false;
var $IS_FRAME = true;
var $IS_DEMO = false;

var n_a = 'n/a';
