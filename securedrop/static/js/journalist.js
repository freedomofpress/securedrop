/**
 * The journalist page should degrade gracefully without JavaScript. To avoid
 * confusing users, this function dynamically adds elements that require JS.
 */

const COLLECTION_SELECTOR_PREFIX = "table";
const ROW_SELECTOR_PREFIX = COLLECTION_SELECTOR_PREFIX + " tr"

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

function show(selector, displayStyle = "revert") {
  let nodelist = document.querySelectorAll(selector);
  Array.prototype.forEach.call(nodelist, function(element) {
    element.style.display = displayStyle;
    element.classList.remove("hidden");
  });
}

function disableButtons(selector) {
  let nodelist = document.querySelectorAll(selector);
  Array.prototype.forEach.call(nodelist, function(element) {
    element.disabled = true;
    element.classList.add("disabled");
  })
}

function enableButtons(selector) {
  let nodelist = document.querySelectorAll(selector);
  Array.prototype.forEach.call(nodelist, function(element) {
    element.disabled = false;
    element.classList.remove("disabled");
  })
}

function disableButtonsIfNoCheckedRows() {
  let buttons = 'button[name="action"]';
  let deletelink = 'a#delete-collections-link'
  let checkedboxes = document.querySelectorAll(ROW_SELECTOR_PREFIX + ":not(.hidden) input[type=checkbox]:checked");
  if (checkedboxes.length == 0) {
    disableButtons(buttons);
    disableButtons(deletelink);
  } else {
    enableButtons(buttons);
    enableButtons(deletelink);
  }
}

function enhance_ui() {
  // Add the "quick filter" box for the list of sources
  let filterContainer = document.getElementById("filter-container");
  if (filterContainer) {
    filterContainer.innerHTML = '<input id="filter" type="text" placeholder="' +
      get_string("filter-by-codename-placeholder-string") +
      '" aria-label="' +
      get_string("filter-by-codename-placeholder-string") +
      '" autofocus >';
  }

  // Add the "select {all,none}" buttons for the list of sources
  let indexSelectContainer = document.getElementById("index-select-container");
  if (indexSelectContainer) {
    indexSelectContainer.outerHTML =
      '<button id="select_all" type="button" class="small"> ' +
      get_string("select-all-string") +
      '</button> <button id="select_none" type="button" class="small"> ' +
      get_string("select-none-string") +
      '</button>';
  }

  // Add the "select {all,unread,none}" buttons for the source collection
  let selectContainer = document.getElementById("select-container");
  if (selectContainer) {
    selectContainer.innerHTML =
      '<button id="select_all" type="button" class="small"> ' +
      get_string("select-all-string") +
      '</button> <button id="select_unread" type="button" class="small"> ' +
      get_string("select-unread-string") +
      '</button> <button id="select_none" type="button" class="small"> ' +
      get_string("select-none-string") +
      '</button>';
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
    show(ROW_SELECTOR_PREFIX);
  } else {
    hide(ROW_SELECTOR_PREFIX);
    show(
      ROW_SELECTOR_PREFIX + '[data-source-designation*="' + value.replace(/"/g, "").toLowerCase() + '"]'
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
  disableButtonsIfNoCheckedRows();
  enhance_ui();

  let selectAll = document.getElementById("select_all");
  if (selectAll) {
    selectAll.style.cursor = "pointer";
    selectAll.addEventListener("click", function() {
      let checkboxes = document.querySelectorAll(ROW_SELECTOR_PREFIX + ":not(.hidden) input[type=checkbox]");
      for (let i = 0; i < checkboxes.length; i++) {
        checkboxes[i].checked = true;
      }
      disableButtonsIfNoCheckedRows();
    });
  }

  let selectNone = document.getElementById("select_none");
  if (selectNone) {
    selectNone.style.cursor = "pointer";
    selectNone.addEventListener("click", function() {
      let checkboxes = document.querySelectorAll(ROW_SELECTOR_PREFIX + ":not(.hidden) input[type=checkbox]");
      for (let i = 0; i < checkboxes.length; i++) {
        checkboxes[i].checked = false;
      }
      disableButtonsIfNoCheckedRows();
    });
  }

  let selectUnread = document.getElementById("select_unread");
  if (selectUnread) {
    selectUnread.style.cursor = "pointer";
    selectUnread.addEventListener("click", function() {
      let checkboxes = document.querySelectorAll(ROW_SELECTOR_PREFIX + " input[type='checkbox']:not(.hidden)");
      for (let i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].classList.contains("unread-cb")) {
          checkboxes[i].checked = true;
        } else {
          checkboxes[i].checked = false;
        }
      }
    });
  }

  let checkboxes = document.querySelectorAll(ROW_SELECTOR_PREFIX + ":not(.hidden) input[type=checkbox]");
  for (let i = 0; i < checkboxes.length; i++) {
    checkboxes[i].addEventListener("click", disableButtonsIfNoCheckedRows);
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

  let deleteSourcesButton = document.getElementById('delete-collections-link');
  if (deleteSourcesButton) {
    deleteSourcesButton.onclick = function() {
      var checkboxes = document.querySelectorAll('input[name="cols_selected"]:checked');
      let deleteMenuCTA = document.getElementById('delete-menu-cta');
      let deleteMenuNoSelect = document.getElementById('delete-menu-no-select');
      if (checkboxes.length <= 0) {
          if (deleteMenuCTA) {
              deleteMenuCTA.style.display = "none"
          }
          if (deleteMenuNoSelect) {
              deleteMenuNoSelect.style.display = "revert"
          }
      } else {
          if (deleteMenuCTA) {
              deleteMenuCTA.style.display = "revert"
          }
          if (deleteMenuNoSelect) {
              deleteMenuNoSelect.style.display = "none"
          }
      }
      let deleteSummarySpan = document.getElementById("delete-menu-summary");
      if (deleteSummarySpan) {
          deleteSummarySpan.innerHTML = get_string("sources-selected") + "<b>"+ checkboxes.length + "</b>";
      }
      let btnRect=deleteSourcesButton.getBoundingClientRect();
      let deleteDialog = document.getElementById('delete-menu-dialog');
      if (deleteDialog) {
          let menuOffset = 120;
          deleteDialog.style.position = "absolute";
          deleteDialog.style.top = btnRect.bottom +'px';
          deleteDialog.style.marginTop = "0px";
          deleteDialog.style.left = (btnRect.left - menuOffset) + 'px';
      }
      let confirmDialog = document.getElementById('delete-confirm-menu-dialog');
      if (confirmDialog) {
          let menuOffset = 250;
          btnRect=deleteSourcesButton.getBoundingClientRect();
          confirmDialog.style.position = "absolute";
          confirmDialog.style.top = btnRect.bottom +'px';
          confirmDialog.style.marginTop = "0px";
          confirmDialog.style.left = (btnRect.left - menuOffset) +'px';
      }
    }
  }
});


