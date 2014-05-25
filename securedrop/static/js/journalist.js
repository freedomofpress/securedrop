/**
 * The journalist page should degrade gracefully without Javascript. To avoid
 * confusing users, this function dyanamically adds elements that require JS.
 */
function enhance_ui() {
  // Add the "quick filter" box for sources
  $('div#filter-container').html('<input id="filter" type="text" placeholder="filter by codename" autofocus >');

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

  $("#delete_collection").submit(function () {
    return confirm("Are you sure you want to delete this collection?");
  });
  $("#delete_collections").submit(function () {
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

  $("#unread a").click(function(){
    $("#unread").html("unread: 0");
  });

  var filter_codenames = function(value){
    if(value == ""){
      $('ul#cols li').show()
    } else {
      $('ul#cols li').hide()
      $('ul#cols li[data-source-designation*="' + value.replace(/"/g, "").toLowerCase() + '"]').show()
    }
  }

  $('#filter').keyup(function(){ filter_codenames(this.value) })

  filter_codenames($('#filter').val())

});
