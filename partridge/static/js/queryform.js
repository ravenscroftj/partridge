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
    
    query = {}

    $("#queryList input[type=hidden]").each(function(i){
        if( $(this).attr("name") == "section"){
            currentField = $(this).val() + "_" + i;   
        }else{
            query[currentField] = $(this).val();
        }
    });

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

        newHTML += "<li id=\"constraint" + constraintID + "\">" 
        + text + " in " + section
        + "<input type=\"hidden\" value=\"" + section + "\""
        + " name=\"section\" />\n"
        + "<input type=\"hidden\" value=\""+ text +"\"" 
        + " name=\"query\" /><a href=\"javascript: void(0)\" "
        + " onclick=\"removeConstraint("+ constraintID +")\">"
        + "<i class=\"icon-remove-circle\" ></i></li>";
      

        if( constraints == 0){
            $("#queryList").html(newHTML);
        }else{
            $("#queryList").append(newHTML);
        }

        constraints++;
        constraintID++;

        updateResults();

    });
});

function removeConstraint( id ){
   
    constraints--;

    $("#constraint" + id).remove();

    if(constraints < 1){
        $("#queryList").html("<i>No query constraints</i>");
    }

    updateResults();
}
