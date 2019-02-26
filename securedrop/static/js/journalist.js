/**
 * The journalist page should degrade gracefully without JavaScript. To avoid
 * confusing users, this function dynamically adds elements that require JS.
 */

function closest(element, selector) {
  let parent = element.parentNode;
  let closest = null;
  while (parent.parentNode) {
    if (parent.matches(selector)) {
      closest = parent;
    }
    parent = parent.parentNode;
  }
  return closest;
}

function hide(selector) {
  let nodelist = document.querySelectorAll(selector);
  Array.prototype.forEach.call(nodelist, function(element) {
    element.style.display = "none";
    element.classList.add("hidden");
  });
}

function show(selector, displayStyle = "block") {
  let nodelist = document.querySelectorAll(selector);
  Array.prototype.forEach.call(nodelist, function(element) {
    element.style.display = displayStyle;
    element.classList.remove("hidden");
  });
}

function enhance_ui() {
  // Add the "quick filter" box for the list of sources
  let filterContainer = document.getElementById("filter-container");
  if (filterContainer) {
    filterContainer.innerHTML = '<input id="filter" type="text" placeholder="' +
      get_string("filter-by-codename-placeholder-string") +
      '" autofocus >';
  }

  // Add the "select {all,none}" buttons for the list of sources
  let indexSelectContainer = document.getElementById("index-select-container");
  if (indexSelectContainer) {
    indexSelectContainer.outerHTML =
      '<span id="select_all" class="select"><i class="far fa-check-square"></i> ' +
      get_string("select-all-string") +
      '</span> <span id="select_none" class="select"><i class="far fa-square"></i> ' +
      get_string("select-none-string") +
      '</span>';
  }

  // Add the "select {all,unread,none}" buttons for the source collection
  let selectContainer = document.getElementById("select-container");
  if (selectContainer) {
    selectContainer.innerHTML =
      '<span id="select_all" class="select"><i class="far fa-check-square"></i> ' +
      get_string("select-all-string") +
      '</span> <span id="select_unread" class="select"><i class="far fa-check-square"></i> ' +
      get_string("select-unread-string") +
      '</span> <span id="select_none" class="select"><i class="far fa-square"></i> ' +
      get_string("select-none-string") +
      '</span>';
  }

}

function get_string(string_id) {
  let stringContainer = document.querySelector("#js-strings > #" + string_id);
  return stringContainer ? stringContainer.innerHTML : "";
}

// String interpolation helper
// Credit where credit is due: http://stackoverflow.com/a/1408373
String.prototype.supplant = function (o) {
    return this.replace(/{([^{}]*)}/g,
        function (a, b) {
            let r = o[b];
            return typeof r === 'string' || typeof r === 'number' ? r : a;
        }
    );
};

function filter_codenames(value) {
  if(value == ""){
    show('ul#cols li');
  } else {
    hide('ul#cols li');
    show(
      'ul#cols li[data-source-designation*="' + value.replace(/"/g, "").toLowerCase() + '"]'
    );
  }
}

function ready(fn) {
  if (document.readyState != 'loading'){
    fn();
  } else {
    document.addEventListener('DOMContentLoaded', fn);
  }
}

ready(function() {
  enhance_ui();

  let selectAll = document.getElementById("select_all");

  if (selectAll) {
    selectAll.style.cursor = "pointer";
    selectAll.addEventListener("click", function() {
      let checkboxes = document.querySelectorAll(".panel li:not(.hidden) input[type=checkbox]");
      for (let i = 0; i < checkboxes.length; i++) {
        checkboxes[i].checked = true;
      }
    });
  }

  let selectNone = document.getElementById("select_none");
  if (selectNone) {
    selectNone.style.cursor = "pointer";
    selectNone.addEventListener("click", function() {
      let checkboxes = document.querySelectorAll(".panel li:not(.hidden) input[type=checkbox]");
      for (let i = 0; i < checkboxes.length; i++) {
        checkboxes[i].checked = false;
      }
    });
  }

  let selectUnread = document.getElementById("select_unread");
  if (selectUnread) {
    selectUnread.style.cursor = "pointer";
    selectUnread.addEventListener("click", function() {
      let checkboxes = document.querySelectorAll(".submission > input[type='checkbox']:not(.hidden)");
      for (let i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].classList.contains("unread-cb")) {
          checkboxes[i].checked = true;
        } else {
          checkboxes[i].checked = false;
        }
      }
    });
  }

  // When unread messages are downloaded from the source list, mark
  // the source read.
  let unreadLinks = document.querySelectorAll(".unread .unread a");
  for (let i = 0; i < unreadLinks.length; i++) {
    let link = unreadLinks[i];
    let sourceRow = closest(link, ".source");
    link.addEventListener("click", function(){
      sourceRow.classList.remove("unread");
      sourceRow.classList.add("read");
      link.parentNode.removeChild(link);
    });
  }

  let filterInput = document.getElementById("filter");
  if (filterInput) {
    filterInput.addEventListener("keyup", function() {
      filter_codenames(this.value);
    });

    filter_codenames(filterInput.value);
  }

  // Confirm before deleting user on admin page
  let deleteUser = document.querySelector('button.delete-user');
  if (deleteUser) {
    deleteUser.addEventListener('click', function(evt) {
      let username = this.dataset.username;
      let confirmed = confirm(get_string("delete-user-confirm-string").supplant({ username: username }));
      if (!confirmed) {
        evt.preventDefault();
      }
      return confirmed;
    });
  };

  // Confirm before resetting multifactor authentication on edit user page
  let resetTwoFactorForms = document.querySelectorAll('form.reset-two-factor');
  for (let i = 0; i < resetTwoFactorForms.length; i++) {
    resetTwoFactorForms[i].addEventListener('submit', function(evt) {
      let username = this.dataset.username;
      let confirmed = confirm(get_string("reset-user-mfa-confirm-string").supplant({ username: username }));
      if (!confirmed) {
        evt.preventDefault();
      }
      return confirmed;
    });
  }

  // make show password checkbox visible if javascript enabled
  show('.show-password-checkbox-container');

  // Set up listener for show password checkbox
  let showPasswordCheckbox = document.getElementById('show-password-check');
  if (showPasswordCheckbox) {
      showPasswordCheckbox.addEventListener('change', function(event) {
        let passwordInput = document.getElementById('login-form-password');
        if (passwordInput) {
          if(event.target.checked) {
            passwordInput.setAttribute('type', 'text');
          }
          else {
            passwordInput.setAttribute('type', 'password');
          }
        }
      });
  }

});
