$(function () {
  var all = $("#select_all");
  var none = $("#select_none");
  var checkboxes = $(":checkbox");

  all.css('cursor', 'pointer');
  none.css('cursor', 'pointer');

  all.click( function() { checkboxes.prop('checked', true); });
  none.click( function() { checkboxes.prop('checked', false); });
});

function toggle_delete_warning(newState) {
  var css_display_value;
  if (newState == "show") {
    css_display_value = "block";
  } else if (newState == "hide") {
    css_display_value = "none";
  } else {
    console.log('Unrecognized value "' + newState + '" for newState in toggle_delete_warning');
    return;
  }
  $('div#modal-dim').css('display', css_display_value);
  $('div#delete-collection-warning').css('display', css_display_value);
}

$(function () {
  $('button.delete-collection').hover(
  function hoverIn(e) {
    $(this).find('img.delete-collection-icon').attr('src', "/static/i/delete_red.png");
  },
  function hoverOut(e) {
    $(this).find('img.delete-collection-icon').attr('src', "/static/i/delete_gray.png");
  });

  // keep track of the form that was submitted (that needs confirmation)
  var collection_delete_form = null;

  $('form.delete-collection').submit(function click(e) {
    // Block the post request, it will be re-triggered by the warning if
    // the user chooses to continue

    // if this variable is non-null, this is the second submit call, which was
    // triggered by the confirmation handler and should just do the request
    if (collection_delete_form) {
      collection_delete_form = null;
      return true;
    }

    e.preventDefault();
    collection_delete_form = $(this);
    // check if the user has opted out of future warnings
    localForage.getItem('optoutDeleteWarning',
    function (optoutDeleteWarning) {
      // if key not found, getItem returned null (evaluates to false)
      if (!optoutDeleteWarning) {
        toggle_delete_warning('show');
      } else {
        collection_delete_form.submit();
      }
    });
  });

  // Sets a hidden field in the warning form in order to determine which submit
  // button was clicked
  $("form#delete-warning-confirmation :submit").click(function () {
    $("form#delete-warning-confirmation input#action").val(this.name);
  });

  $('form#delete-warning-confirmation').submit(function (e) {
    var form = {};
    $.each($(this).serializeArray(), function() {
      form[this.name] = this.value;
    });

    // check for the optout
    if ("optout" in form && form["optout"] == "yes") {
      localForage.setItem('optoutDeleteWarning', true)
    }

    switch(form["action"]) {
    case "del":
      // submit the delete-collection form
      collection_delete_form.submit();
    case "nodel":
      // reset the collection_delete_form variable
      collection_delete_form = null;
      break;
    default:
      console.log('Got unexpected value "' + form["action"] + '" for form#delete-warning-confirmation action');
      break;
    }

    toggle_delete_warning("hide");
    return false;
  });
});
