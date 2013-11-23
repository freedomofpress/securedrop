$(function () {
  var all = $("#select_all");
  var none = $("#select_none");
  var checkboxes = $(":checkbox");

  all.css('cursor', 'pointer');
  none.css('cursor', 'pointer');

  all.click( function() { checkboxes.prop('checked', true); });
  none.click( function() { checkboxes.prop('checked', false); });
});
