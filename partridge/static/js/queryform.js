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

        newHTML += "<li id=\"constraint" + constraintID + "\">" 
        + text + " in " + section
        + "<input type=\"hidden\" value=\"" + section + "\""
        + " name=\"section\" />\n"
        + "<input type=\"hidden\" value=\""+ text +"\"" 
        + " name=\"query\" /><a href=\"#\">"
        + "<i class=\"icon-remove-circle\"></i></li>";
      

        if( constraints == 0){
            $("#queryList").html(newHTML);
        }else{
            $("#queryList").append(newHTML);
        }

        constraints++;
        constraintID++;

    });
});
