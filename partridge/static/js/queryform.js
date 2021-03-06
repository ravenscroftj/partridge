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

    //see if there is an offset set up
    if('offset' in $.deparam.fragment()){
        offset = parseInt($.deparam.fragment()['offset']);
    }


   if( getResult.count < 1){
        
       $("#resultStats").html("No results - try generalising your query");
       $("#searchResults").html("");
       $("#paginationStuff").html("");

   }else{
       $("#resultStats").html("Showing results " + 
       (1+offset) + " to " + (offset + getResult.count)
       + " of " + getResult.total);

       $("#searchResults").html(getResult.html); 
       doPagination(getResult.total);

  }

}

/**
 * Method for recalculating pages
 *
 *
 */
function doPagination( total ){

   $("#paginationStuff").html("");

   pages = Math.ceil(total / page_limit);

   if(offset == 0){
     currentPage = 1;
   }else{
     currentPage = Math.ceil( offset / page_limit ) + 1; 
   }      
  
   var html = "<li";

  
   if(currentPage == 1) {
        html += " class=\"disabled\"";
   }

   html += "><a href=\"javascript: void(0);\" onclick=\"prevPage()\"> &lt;&lt;"
         + "</a></li>";


   $("#paginationStuff").append(html);

   //we only want to render closest 5 pages either side of current page

   var startPage = (currentPage-5) < 0 ? 0 : currentPage-5;
   var endPage   = (currentPage+4) > pages ? pages : currentPage+4;

   for(var i=startPage; i < endPage; i++){

        var html = "<li";

        if( (i+1) == currentPage) {
            html += " class=\"active\"";
        }


        html += "><a href=\"javascript: void(0);\" "
        + "onclick=\"movePage(" + (i*page_limit) + ")\">" + 
        (i+1) + "</a></li>"
        $("#paginationStuff").append(html);
   }

   html = "<li";

   if( currentPage == pages ){
     html += " class=\"disabled\"";
   }

   html += "><a href=\"javascript:void(0)\" "
   + "onclick=\"nextPage()\">&gt;&gt;</a>";

   $("#paginationStuff").append(html);
 
}

/**
 * Change the results offset and retrieve next set of papers
 */
function movePage( newOffset ){
    
    $.bbq.pushState({'offset' : newOffset });

}

function nextPage(){

    var params = $.deparam.fragment();
    var offset = 0;

    if( 'offset' in params){
        offset = parseInt(params['offset']) + page_limit;
    }else{
        offset = page_limit;
    }

    movePage(offset);
}

function prevPage(){
    var params = $.deparam.fragment();
    var offset = 0;

    if( 'offset' in params){
        offset = parseInt(params['offset']) - page_limit;
    }

    movePage(offset);
  
}

var constraints = 0;
var constraintID = 1;

$(function(){

    /**
     * onClick handler for adding a new constrain to the query
     */
    $("#addConstraint").click(function( event ){
        
        var newHTML = "";

        var section = $("#corescSelect").val();
        var text = $("#queryText").val();

        var params = {}
        params[ section + "_" + constraintID ] = text;

        //reset current page
        params['offset'] = 0;

        jQuery.bbq.pushState(params);

        constraintID++;

        updateResults();

    });

    $("#paper_type").change( function( event ){
       
        type = $("#paper_type").val();

        var params = {}

        params [ "papertype_1" ] = type

        params['offset'] = 0;

        jQuery.bbq.pushState(params);

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

            if(constraint == "offset"){
                continue;
            }

            if(constraint == "papertype_1"){
               $("select[name='paper_type'] option[value='" + text + "']").attr('selected', true);
                continue;
            }

            // we need to allocate a new id larger than this next time
            if( id > constraintID){
                constraintID = id + 1;
            }

            if( $("#constraint" + id).length < 1){

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


                constraints++;
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

    //set the new offset to zero
    newparams['offset'] = 0;

    $("#constraint" + id).remove();

    //overwrite current fragment string
    jQuery.bbq.pushState(newparams, 2);

    if(constraints < 1){
        $("#queryList").html("<i>No query constraints</i>");
    }

    updateResults();
}
