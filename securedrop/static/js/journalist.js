$(function () {
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
    checkboxes.each(function () {
      if (this.checked) num_checked++;
    });
    if (num_checked > 0) {
      return confirm("Are you sure you want to delete the " + num_checked + " selected collection" + (num_checked > 1 ? "s?" : "?"));
    }
    // Don't submit the form if no collections are selected
    return false;
  });
});
