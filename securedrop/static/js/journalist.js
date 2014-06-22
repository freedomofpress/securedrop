/**
 * The journalist page should degrade gracefully without Javascript. To avoid
 * confusing users, this function dyanamically adds elements that require JS.
 */
function enhance_ui() {
  // Add the filter block for sources
  $('div#filter-container').html($('#filter_block').html());

  // Add the "select {all,none}" buttons
  $('div#select-container').html('<span id="select_all" class="select"><i class="fa fa-check-square-o"></i> select all</span> <span id="select_none" class="select"><i class="fa fa-square-o"></i> select none</span>');
}

$(function () {
  enhance_ui();

  var all = $("#select_all");
  var none = $("#select_none");
  var checkboxes = $(":checkbox");

  all.css('cursor', 'pointer');
  none.css('cursor', 'pointer');

  all.click( function() { checkboxes.prop('checked', true); });
  none.click( function() { checkboxes.prop('checked', false); });

  $("#delete_collections").click(function () {
    var num_checked = 0;

    // we don't want to delete the collections which aren't visible because they are filtered...
    $('ul#cols li:visible').each(function () {
      if ($(":checkbox", this).first().prop('checked')) num_checked++;
    });
    if (num_checked > 0) {
      var delete_collections = confirm("Are you sure you want to delete the " + num_checked + " selected collection" + (num_checked > 1 ? "s?" : "?"));
      if(delete_collections){
        // uncheck the invisible collections just before sending POST
        $('ul#cols li:not(:visible) :checkbox').attr('checked', false)
      }
      return delete_collections;
    }
    // Don't submit the form if no collections are selected
    return false;
  });

  // don't star/unstar invisible collections
  $("#star_collections, #unstar_collections, #delete_submissions, #download_submissions").click(function(){
    $('ul li:not(:visible) :checkbox').attr('checked', false)
    return true;
  });

  $("span.unread a").click(function(){
    sid = $(this).data('sid');
    $("span.unread[data-sid='" + sid + "']").remove();
  });

  if($('#content.journalist-view-all').length){
    var filter = function(){
      var codename = $('#codename').val()
      var starred_status = $('#starred_status').val()
      var read_status = $('#read_status').val()

      $('ul#cols li').show()

      if(codename != ""){
        $('ul#cols li').hide()
        $('ul#cols li[data-source-designation*="' + codename.replace(/"/g, "").toLowerCase() + '"]').show()
      }

      if(starred_status == "starred"){
        $('ul#cols li[data-starred="unstarred"]').hide()
      }
      if(starred_status == "unstarred"){
        $('ul#cols li[data-starred="starred"]').hide()
      }

      if(read_status == "read"){
        $('ul#cols li[data-read="unread"]').hide()
      }
      if(read_status == "unread"){
        $('ul#cols li[data-read="read"]').hide()
      }

    }

    $('#codename').keyup(filter)
    $('#starred_status').change(filter)
    $('#read_status').change(filter)

    filter()
  }
  if($('#content.journalist-view-single').length){
    var filter = function(){
      var starred_status = $('#starred_status').val()
      var read_status = $('#read_status').val()
      var type = $('#type').val()

      $('ul#submissions li').show()

      if(starred_status == "starred"){
        $('ul#submissions li[data-starred="unstarred"]').hide()
      }
      if(starred_status == "unstarred"){
        $('ul#submissions li[data-starred="starred"]').hide()
      }

      if(read_status == "read"){
        $('ul#submissions li[data-read="unread"]').hide()
      }
      if(read_status == "unread"){
        $('ul#submissions li[data-read="read"]').hide()
      }

      if(type == "documents"){
        $('ul#submissions li[data-type="message"]').hide()
      }
      if(type == "messages"){
        $('ul#submissions li[data-type="document"]').hide()
      }

    }

    $('#type').change(filter)
    $('#starred_status').change(filter)
    $('#read_status').change(filter)

    filter()
  }

});
