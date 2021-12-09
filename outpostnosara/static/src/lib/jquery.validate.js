(function( factory ) {
    if ( typeof define === "function" && define.amd ) {
        define( ["jquery"], factory );
    } else if (typeof module === "object" && module.exports) {
        module.exports = factory( require( "jquery" ) );
    } else {
        factory( jQuery );
    }
}(function( $ ) {

// JQuery trim is deprecated, provide a trim method based on String.prototype.trim
var trim = function( str ) {

    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/trim#Polyfill
    return str.replace( /^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, "" );
};

// Custom selectors
$.extend( $.expr.pseudos || $.expr[ ":" ], {

    // https://jqueryvalidation.org/blank-selector/
    blank: function( a ) {
        return !trim( "" + $( a ).val() );
    },

    // https://jqueryvalidation.org/filled-selector/
    filled: function( a ) {
        var val = $( a ).val();
        return val !== null && !!trim( "" + val );
    },

    // https://jqueryvalidation.org/unchecked-selector/
    unchecked: function( a ) {
        return !$( a ).prop( "checked" );
    }
});

return $;
}));
