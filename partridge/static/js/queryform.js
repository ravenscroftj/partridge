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

    $.ajax({
        "success" : showResults,
        "data" : {"q" : "true"}
    });

}


/**
 * Callback function from get request for papers
 * 
 */
function showResults( getResult ){

   $("#searchResults").html(getResult); 

}

/**
 * When everything is loaded, update the search results
 *
 */
$(function(){
    updateResults();
});

var constraints = 0;

/**
 * onClick handler for adding a new constrain to the query
 */
$(function(){
    $("#addConstraint").click(function(){

        
    });
});
