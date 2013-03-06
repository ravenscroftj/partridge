/**
 *  This is a bookmarklet for Partridge remote paper adder
 *
 * Code based upon http://coding.smashingmagazine.com/2010/05/23/make-your-own-bookmarklets-with-jquery/
 *
 */ 

(function(){

        // the minimum version of jQuery we want
        var v = "1.3.2";

        // check prior inclusion and version
        if (window.jQuery === undefined || window.jQuery.fn.jquery < v) {
                var done = false;
                var script = document.createElement("script");
                script.src = "http://ajax.googleapis.com/ajax/libs/jquery/" + v + "/jquery.min.js";
                script.onload = script.onreadystatechange = function(){
                        if (!done && (!this.readyState || this.readyState == "loaded" || this.readyState == "complete")) {
                                done = true;
                                initMyBookmarklet();
                        }
                };
                document.getElementsByTagName("head")[0].appendChild(script);
        } else {
                initMyBookmarklet();
        }
        
        function initMyBookmarklet() {
                (window.myBookmarklet = function() {

                loc = encodeURI(window.location.href);

                var remoteLoc = "http://localhost:5000/remote#url=" + loc;

                if(jQuery("#partridgeFrame").length == 0){


                    //initialise partridge frame
                    jQuery("body").append("\
                        <div id='partridgeFrame'>\
                            <div id='partridgeFrame_veil' style=''>\
                                    <p>Loading...</p>\
                            </div>\
                            <iframe src='"+remoteLoc+"' onload=\"jQuery('#partridgeFrame iframe').slideDown(500);\">Enable iFrames.</iframe>\
                            <style type='text/css'>\
                                    #partridgeFrame_veil { display: none; position: fixed; width: 100%; height: 100%; top: 0; left: 0; background-color: rgba(255,255,255,.25); cursor: pointer; z-index: 900; }\
                                    #patridgeFrame_veil p { color: black; font: normal normal bold 20px/20px Helvetica, sans-serif; position: absolute; top: 50%; left: 50%; width: 10em; margin: -10px auto 0 -5em; text-align: center; }\
                                    #partridgeFrame iframe { display: none; position: fixed; top: 10%; left: 10%; width: 80%; height: 80%; z-index: 999; border: 10px solid rgba(0,0,0,.5); margin: -5px 0 0 -5px; }\
                            </style>\
                    </div>");


                    jQuery("#partridgeFrame_veil").fadeIn(750);
                

                }else{
                      jQuery("#partridgeFrame_veil").fadeOut(750);
                      jQuery("#partridgeFrame iframe").slideUp(500);
                      setTimeout("jQuery('#partridgeFrame').remove()", 750);
                }

                jQuery("#partridgeFrame_veil").click( function(event){
                      jQuery("#partridgeFrame_veil").fadeOut(750);
                      jQuery("#partridgeFrame iframe").slideUp(500);
                      setTimeout("jQuery('#partridgeFrame').remove()", 750);
                });


                })();
        }

})();
