/**
Name editable input.

Shamelessly inspired by:
http://vitalets.github.io/x-editable/assets/x-editable/inputs-ext/address/address.js

Internal value stored as {first: "Antonín", last: "Dvořák"}
**/
(function ($) {
    "use strict";
    
    var Name = function (options) {
        this.init('name', options, Name.defaults);
    };

    //inherit from Abstract input
    $.fn.editableutils.inherit(Name, $.fn.editabletypes.abstractinput);

    $.extend(Name.prototype, {
        /**
        Renders input from tpl

        @method render() 
        **/        
        render: function() {
           this.$input = this.$tpl.find('input');
        },
        
        /**
        Default method to show value in element. Can be overwritten by display option.
        
        @method value2html(value, element) 
        **/
        value2html: function(value, element) {
            if(!value) {
                $(element).empty();
                return; 
            }
            var html = value.first+' '+value.last;
            if(value.researcher_id != false) {
                html = '<a href="/researcher/'+value.researcher_id+'/">'+html+'</a>'
            }
            $(element).html(html); 
        },
        
        /**
        Gets value from element's html
        
        @method html2value(html) 
        **/        
        html2value: function(html) {        
          /*
             Nothing, do not attempt to rebuild the value from the HTML (needs name parsing)
          */ 
          return null;  
        },
      
       /**
        Converts value to string. 
        It is used in internal comparing (not for sending to server).
        
        @method value2str(value)  
       **/
       value2str: function(value) {
           var str = '';
           if(value) {
               for(var k in value) {
                   str = str + k + ':' + value[k] + ';';  
               }
           }
           return str;
       }, 
       
       /*
        Converts string to value. Used for reading value from 'data-value' attribute.
        
        @method str2value(str)  
       */
       str2value: function(str) {
           /*
           this is mainly for parsing value defined in data-value attribute. 
           If you will always set value by javascript, no need to overwrite it
           */
           return str;
       },                
       
       /**
        Sets value of input.
        
        @method value2input(value) 
        @param {mixed} value
       **/         
       value2input: function(value) {
           if(!value) {
             return;
           }
           this.$input.filter('[name="first"]').val(value.first);
           this.$input.filter('[name="last"]').val(value.last);
       },       
       
       /**
        Returns value of input.
        
        @method input2value() 
       **/          
       input2value: function() { 
           return {
              first: this.$input.filter('[name="first"]').val(), 
              last: this.$input.filter('[name="last"]').val(), 
              researcher_id: false,
              
           };
       },        
       
        /**
        Activates input: sets focus on the first field.
        
        @method activate() 
       **/        
       activate: function() {
            this.$input.filter('[name="first"]').focus();
       },  
       
       /**
        Attaches handler to submit form in case of 'showbuttons=false' mode
        
        @method autosubmit() 
       **/       
       autosubmit: function() {
           this.$input.keydown(function (e) {
                if (e.which === 13) {
                    $(this).closest('form').submit();
                }
           });
       }       
    });

    Name.defaults = $.extend({}, $.fn.editabletypes.abstractinput.defaults, {
        tpl: '<div class="editable-address"><label><span>First name: </span><input type="text" name="first" class="input-small form-control"></label></div>'+
             '<div class="editable-address"><label><span>Last name: </span><input type="text" name="last" class="input-small form-control"></label></div>',
             
        inputclass: ''
    });

    $.fn.editabletypes.name = Name;

}(window.jQuery));
