/**
 * The journalist page should degrade gracefully without JavaScript. To avoid
 * confusing users, this function dynamically adds elements that require JS.
 */
function enhance_ui() {
  // Add the "quick filter" box for sources
  $('div#filter-container').html('<input id="filter" type="text" placeholder="' + get_string("filter-by-codename-placeholder-string") + '" autofocus >');

  // Add the "select {all,none}" buttons
  $('div#select-container').html('<span id="select_all" class="select"><i class="far fa-check-square"></i> ' + get_string("select-all-string") + '</span> <span id="select_unread" class="select"><i class="far fa-check-square"></i> ' + get_string("select-unread-string") + '</span> <span id="select_none" class="select"><i class="far fa-square"></i> ' + get_string("select-none-string") + '</span>');

  $('div#index-select-container').replaceWith('<span id="select_all" class="select"><i class="far fa-check-square"></i> ' + get_string("select-all-string") + '</span> <span id="select_none" class="select"><i class="far fa-square"></i> ' + get_string("select-none-string") + '</span>');

  // Change the action on the /col pages so we use a JavaScript
  // confirmation instead of redirecting to a confirmation page before
  // deleting submissions
  $('button#delete-selected').attr('value', 'delete');
}

function get_string(string_id) {
  return $("#js-strings > #" + string_id)[0].innerHTML;
}

// String interpolation helper
// Credit where credit is due: http://stackoverflow.com/a/1408373
String.prototype.supplant = function (o) {
    return this.replace(/{([^{}]*)}/g,
        function (a, b) {
            var r = o[b];
            return typeof r === 'string' || typeof r === 'number' ? r : a;
        }
    );
};

$(function () {
  enhance_ui();

  var all = $("#select_all");
  var none = $("#select_none");
  var unread = $("#select_unread");

  all.css('cursor', 'pointer');
  none.css('cursor', 'pointer');
  unread.css('cursor', 'pointer');

  all.click(function() {
    var checkboxes = $(".panel :checkbox").filter(":visible");
    checkboxes.prop('checked', true);
  });
  none.click(function() {
    var checkboxes = $(".panel :checkbox").filter(":visible");
    checkboxes.prop('checked', false);
  });
  unread.click(function() {
      var checkboxes = document.querySelectorAll(".submission > [type='checkbox']");
      for (var i = 0; i < checkboxes.length; i++) {
          if (checkboxes[i].className.includes("unread-cb"))
              checkboxes[i].checked = true;
          else
              checkboxes[i].checked = false;
      }
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

  // Check if #filter exists by checking the .length of the jQuery selector
  // http://stackoverflow.com/questions/299802/how-do-you-check-if-a-selector-matches-something-in-jquery
  if ($('#filter').length) {
    filter_codenames($('#filter').val())
  }

  // Confirm before deleting user on admin page
  $('button.delete-user').click(function(event) {
      var username = $(this).attr('data-username');
      return confirm(get_string("delete-user-confirm-string").supplant({ username: username }));
  });

  // Confirm before resetting two-factor authentication on edit user page
  $('.reset-two-factor').submit(function(event) {
      var username = $(this).attr('data-username');
      return confirm(get_string("reset-user-mfa-confirm-string").supplant({ username: username }));
  });

  // make show password checkbox visible if javascript enabled
  $('.show-password-checkbox-container').css("display", "block");

  // Set up listener for show password checkbox
  $('#show-password-check').change(function(event) {
    if(event.target.checked) {
      $('#login-form-password').attr('type', 'text');
    }
    else {
      $('#login-form-password').attr('type', 'password');
    }
  })

});
