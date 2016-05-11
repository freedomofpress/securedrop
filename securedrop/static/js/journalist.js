/**
 * The journalist page should degrade gracefully without Javascript. To avoid
 * confusing users, this function dynamically adds elements that require JS.
 */
ready(function() {
  enhance_ui();

  var all = document.getElementById("select_all");
  var none = document.getElementById("select_none");
  var unread = document.getElementById("select_unread");

  if (all) {
    all.style.cursor = 'pointer';
    all.addEventListener('click', function() {
      var checkboxes = document.querySelectorAll('input[type="checkbox"]:not(.hidden)');
      for (var i = 0; i < checkboxes.length; i++) {
        checkboxes[i].checked = true;
      }
    });
  }
  
  if (none) {
    none.style.cursor = 'pointer';
    none.addEventListener('click', function() {
      var checkboxes = document.querySelectorAll('input[type="checkbox"]:not(.hidden)');
      for (var i = 0; i < checkboxes.length; i++) {
        checkboxes[i].checked = false;
      }
    });
  }
  
  if (unread) {
    unread.style.cursor = 'pointer';
    unread.onclick = function() {
      var checkboxes = document.querySelectorAll(".submission > [type='checkbox']");
      for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].className.includes("unread-cb")) {
          checkboxes[i].checked = true;
        } else {
          checkboxes[i].checked = false;
        }
      }
    };
  }

  var deleteCollection = document.getElementById('delete_collection');
  if (deleteCollection) {
    deleteCollection.addEventListener('submit', function(evt) {
      var confirmed = confirm("Are you sure you want to delete this collection?");
      if (!confirmed) {
        evt.preventDefault();
      }
      return confirmed;
    });
  }

  var deleteCollections = document.getElementById('delete_collections');
  if (deleteCollections) {
    deleteCollections.addEventListener('click', function(evt) {
      var checked = Array.prototype.filter.call(
        document.querySelectorAll('ul#cols li input[type="checkbox"]:not(.hidden)'),
        function(obj) { return obj.checked; }
      );
      if (checked.length > 0) {
        var confirmed = confirm("Are you sure you want to delete the " + checked.length + " selected collection"
                                  + (checked.length > 1 ? "s?" : "?"));
        if (!confirmed) {
          evt.preventDefault();
        }
        return confirmed;
      }
      // Don't submit the form if no collections are selected
      evt.preventDefault();
      return false;
    });
  }

  var deleteSelected = document.getElementById('delete_selected');
  if (deleteSelected) {
    deleteSelected.addEventListener('click', function(evt) {
      var checked = Array.prototype.filter.call(
        document.querySelectorAll('ul#submissions li input[type="checkbox"]:not(.hidden)'),
        function(obj) { return obj.checked; }
      );
      if (checked.length > 0) {
        var confirmed = confirm("Are you sure you want delete the " + checked.length + " selected submission"
                                  + (checked.length > 1 ? "s?" : "?"));
        if (!confirmed) {
          evt.preventDefault();
        }
        return confirmed;
      }
      // Don't submit the form if no submissions are selected
      evt.preventDefault();
      return false;
    });
  }

  var unread = document.querySelectorAll('.unread a');
  if (unread) {
    forEach(unread, function(index, el) {
      el.addEventListener('click', function() {
        document.querySelector('.unread').innerHTML = "unread: 0";
      });
    });
  }

  var filter_codenames = function(value) {
    if (value == "") {
      forEach(document.querySelectorAll('ul#cols li'), function(index, el) {
        el.style.display = 'block';
      });
    } else {
      forEach(document.querySelectorAll('ul#cols li'), function(index, el) {
        el.style.display = 'none';
      });
      var matches = document.querySelectorAll('ul#cols li[data-source-designation*="' + value.replace(/"/g, "").toLowerCase() + '"]');
      forEach(matches, function(index, el) {
        el.style.display = 'block';
      });
    }
  }

  var filter = document.getElementById('filter');
  if (filter) {
    filter.addEventListener('keyup', function() {
      filter_codenames(this.value);
    });
    filter_codenames(filter.value);
  }

  // Confirm before deleting user on admin page
  var deleteUser = document.querySelector('button.delete-user');
  if (deleteUser) {
    deleteUser.addEventListener('click', function(evt) {
      var username = this.dataset.username;
      var confirmed = confirm("Are you sure you want to delete the user " + username + "?");
      if (!confirmed) {
        evt.preventDefault();
      }
      return confirmed;
    });
  };

  // FIXME: #reset-two-factor is now #reset-two-factor-totp, #reset-two-factor-hotp
  // Confirm before resetting two factor authentication on edit user page
  var resetTwoFactor = document.querySelector('form#reset-two-factor');
  if (resetTwoFactor) {
    resetTwoFactor.addEventListener('submit', function(evt) {
      var confirmed = confirm("Are you sure to want to reset this user's two factor authentication?");
      if (!confirmed) {
        evt.preventDefault();
      }
      return confirmed;
    });
  }
});

function enhance_ui() {
  // Add the "quick filter" box for sources
  var quickFilter = document.querySelector('div#filter-container');
  if (quickFilter) {
    quickFilter.innerHTML =
      '<input id="filter" type="text" placeholder="filter by codename" autofocus >';
  }

  // Add the "select {all,none}" buttons if on col page
  var colSelectContainer = document.querySelector('div#select-container');
  if (colSelectContainer) {
    colSelectContainer.innerHTML =
      '<span id="select_all" class="select"><i class="fa fa-check-square-o"></i> select all</span>'
    + '<span id="select_none" class="select"><i class="fa fa-square-o"></i> select none</span>';
  }

  // Change the action on the /col pages so we use a Javascript
  // confirmation instead of redirecting to a confirmation page before
  // deleting submissions
  var deleteSelectedButton = document.querySelector('button#delete_selected');
  if (deleteSelectedButton) {
    deleteSelectedButton.setAttribute('value', 'delete');
  }
}

var forEach = function(array, callback, scope) {
  for (var i = 0; i < array.length; i++) {
    callback.call(scope, i, array[i]); // passes back stuff we need
  }
};

function ready(fn) {
  if (document.readyState != 'loading'){
    fn();
  } else {
    document.addEventListener('DOMContentLoaded', fn);
  }
}
