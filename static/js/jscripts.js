$(document).ready(function () {

// the link to js is working now!
console.log("linked jscript working!");

// This function enables the site to track users' action-items, such as meetup/giving/congress
console.log("activated actionLinks!");
$('.actionLinks a').click( function(event) { 

                    var actionObj = this.dataset;
                    console.log(actionObj); 
                    $.post("/action", 
                         { tag_id: actionObj.tagid,
                            article_id: actionObj.articleid,
                            action_type: actionObj.linktype
                          }, 
                          function (result) { console.log(result) }
                          );
                          });

// function for checking valid url, using regex from msdn.microsoft.com
function checkUrl(url) {
    return /^(ht|f)tp(s?)\:\/\/[0-9a-zA-Z]([-.\w]*[0-9a-zA-Z])*(:(0-9)*)*(\/?)([a-zA-Z0-9\-\.\?\,\'\/\\\+&amp;%\$#_]*)?$/.test(url);
}

// add data attributes to element by id:
function addDataAttr(data, elementId) { $(elementId).attr({
                      "data-title" : data.title,
                      "data-img" : data.img
                    });
}

function getPreviewAttr(previewUrl) {
                  // post url in form to server, returns opengraph data based on url
                  $.post("/preview",
                    
                      // send previewUrl
                      { url: previewUrl },
                        // extract preview data
                        function (result) { 
                        var previewObj = { 
                          title: result.title, 
                          img: result.img, 
                          desc: result.desc
                        };
                        console.log(previewObj);
                        return previewObj;
                        });
}

// Preview article posting, getting Headline, Image, and Description 
function getPreview(data) {
                $.post(

                  // post url in form to server, returns opengraph data based on url
                  "/preview",
                  { url: data },

                  // insert preview into html
                  function (result) { 
                  $("#previewDiv .post-title h3").text(result.title); 
                  $("#previewDiv .post-image").attr("src", result.img);
                  $("#previewDiv .post-summary p").text(result.desc);
                  addDataAttr(result, "#postArticle");
                 });
 }



$("#url-field").on("change", function() { 
                        if (checkUrl($(this).val())) {
                          getPreview($(this).val());
                        } else {
                          $("#checkURL").html("Please enter a valid url.");
                        };
});

// working on posting to "/post_article"
$("#postArticle").submit( function(e) { 
            e.preventDefault(); 
   
            var allTags = [];
                $("input:checked").each(function () {
                  allTags.push($(this).val());
                  return allTags;
                });
            
            console.log("Tags after first assignment: " + allTags);

            var formInfo = { title: this.dataset.title,
              img_src: this.dataset.img,
              url: $("#url-field").val(),
              date: $("#date-field").val(),
              tagList: JSON.stringify(allTags)
            }

            console.log("Obj first assigned: " + formInfo);
            console.log("Tags after object is assigned: " + allTags);

            $.post("/post_article", formInfo, function (result) { window.location = result; });

            console.log("Obj after posting to db: " + formInfo)
            console.log("Tags after posted to db: " + allTags);
});

// add more tags on Article Page
$("#tagForm").click( function () {
  $('#updateArticle').toggle();
  $("#tagForm").text( function(i, text) { return text === "Nevermind, it's cool." ? "Add more tags!" : "Nevermind, it's cool."; })
});

});

