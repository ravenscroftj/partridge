/**
 *  A set of functions for making remote requests and downloading papers
 *
 *
 */ 

$(function(){

   $("#urlScanButton").click( function(event){  

        var url = $("#remote_url").val();

        $.bbq.pushState({"url":url});

   });

   $(window).bind( "hashchange", function(e) {

        var params = $.deparam.fragment();

        for( var constraint in params) {
            
            if( constraint == "url"){
                
                var url = params[constraint];
                $("#remote_url").val(url);

                $("#resultsDiv").html("<img src=\"" + loader_image
                +"\" alt=\"Loading...\" />");

                $.ajax({
                    "url"  : remote_paper_backend,
                    "type" : "POST",
                    "data" : {"url" : url },
                    "success" : onPaperScan
                });

            }

        }


   });

    //trigger hashchange and find any initial constraints
    $(window).trigger( 'hashchange' );
});

//----------------------------------------------



//----------------------------------------------

function onPaperScan( data, status){
        $("#resultsDiv").html(data);

        $("#downloadSingle").click( function(event){
            setUpDownloader([$("#theURL").text() ]);
        });

}


var totalDownloads = 0;
var finishedDownloads = 0;
var downloads = [];
var currentDownload = "";
//----------------------------------------------

function onDownloadPaper( data, status){

    finishedDownloads++;

    if( data.status == "ok" ) {
        $("#downloadLog").append("\n Downloaded " + currentDownload + 
        "sucessfully");
    }else{
         $("#downloadLog").append("\n Failed to download " + currentDownload + 
        "because " + data.message);

    }


    $("#finishedDownloads").html( finishedDownloads );

    $("#dlProgress").css("width", (finishedDownloads * 100 / totalDownloads) + "%");
    
    if( downloads.length > 0){
        downloadPaper();
    }else{
       $("#dlText").html("Finished!");
       $("#dlProgressWrapper").removeClass("active").removeClass("progress-striped");
       $("#urlScanButton").removeAttr('disabled');

    }
}


//----------------------------------------------

function downloadPaper(){

    var email = $("#email").val()

    var url = downloads.pop();
    currentDownload = url;

    var data = {"download_url" : url}

    if( email != "" ){
        data['email'] = email
    }

    $("#downloadLog").append("\n Downloading " + url  + "...");

    $.ajax({
        "url": remote_paper_backend,
        "type" : "POST",
        "data" : data,
        "success" : onDownloadPaper
    });

}

//----------------------------------------------



/**
 * Register the downloader code
 *
 */
function setUpDownloader(urls){

    downloads = urls;
    totalDownloads = urls.length;
    finishedDownloads = 0;
    
    $("#resultsDiv").html("<h2>Downloading Papers...</h2>" + 
        "<p id=\"dlText\"> Downloading <span id=\"finishedDownloads\">1</span> of " +
        "<span id=\"totalDownloads\">" + totalDownloads + "</span></p>"+
        "<div id=\"dlProgressWrapper\" class=\"progress progress-striped active\">" +
        "<div class=\"bar\" id=\"dlProgress\" style=\"width: 2%;\"></div></div>" +
        "<textarea readonly=\"true\" rows=\"10\" id=\"downloadLog\">" +
        "</textarea>"
    );

   //disable scan button until downloads are finished
   $("#urlScanButton").attr('disabled', 'disabled');

   downloadPaper(); 

}
