/**
 *  User interface routines for the query form
 *
 *  @author James Ravenscroft
 */

/**
 * Using current filters and queries, update results
 *
 */
function updateResults(){
    
    $("#searchResults").html("<img src=\"" + loader_image +
        "\" alt=\"loading...\" />");

    currentField = "";
    
    query = $.deparam.fragment();

    query['q'] = "true";

    $.ajax({
        "success" : showResults,
        "data" : query
    });

}

var offset = 0;

/**
 * Callback function from get request for papers
 * 
 */
function showResults( getResult ){


   if( getResult.count < 1){
        
       $("#resultStats").html("No results - try generalising your query");
       $("#searchResults").html("");

   }else{
       $("#resultStats").html("Showing results " + 
       (1+offset) + " to " + (offset + getResult.count)
       + " of " + getResult.total);

       $("#searchResults").html(getResult.html); 
   }
}

var constraints = 0;
var constraintID = 1;

$(function(){
    /**
     * When everything is loaded, update the search results
     *
     */
    updateResults();

    /**
     * onClick handler for adding a new constrain to the query
     */
    $("#addConstraint").click(function( event ){
        
        var newHTML = "";

        var section = $("#corescSelect").val();
        var text = $("#queryText").val();

        var params = {}
        params[ section + "_" + constraintID ] = text;

        jQuery.bbq.pushState(params);

        constraints++;
        constraintID++;

        updateResults();

    });

    /**
     * Set up bbq hooks
     *
     */
    $(window).bind( 'hashchange', function(e) {
        

        var params = $.deparam.fragment();

        for( var constraint in params ){
            
            var parts = constraint.split("_");
            var id = parts[1];
            var text = params[constraint];
            var section = parts[0];

            // we need to allocate a new id larger than this next time
            if( id > constraintID){
                constraintID = id + 1;
            }

            if( $("#constraint" + constraintID).length < 1){

                newHTML = "<li id=\"constraint" + id + "\">" 
                + text + " in " + section
                + "<a href=\"javascript: void(0)\" "
                + " onclick=\"removeConstraint("+ id +")\">"
                + "<i class=\"icon-remove-circle\" ></i></li>";
             

                if( constraints == 0){
                    $("#queryList").html(newHTML);
                }else{
                    $("#queryList").append(newHTML);
                }
            }

        }

        //with all constraints in place, pull the latest results
        updateResults(); 

    });

    //trigger hashchange and find any initial constraints
    $(window).trigger( 'hashchange' );
});

/**
 * When a user clicks 'x', remove constraint from query
 *
 */
function removeConstraint( id ){
   
    constraints--;

    var params = $.deparam.fragment();
    var newparams = {};

    for( var constraint in params ){
        
        var parts = constraint.split("_");

        if(parts[1] != id) {
            newparams[constraint] = params[constraint];
        }

    }

    $("#constraint" + id).remove();

    //overwrite current fragment string
    jQuery.bbq.pushState(newparams, 2);

    if(constraints < 1){
        $("#queryList").html("<i>No query constraints</i>");
    }

    updateResults();
}
