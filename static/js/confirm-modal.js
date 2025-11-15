/* ============================================================
   *** JS: Reusable Confirmation Modal ***
   Provides a branded alternative to native confirm()/alert().
   Attach via data-confirm attributes on forms, buttons or links.
   ============================================================ */
;(function () {
  'use strict'

  function ready(fn) {
    if (document.readyState !== 'loading') {
      fn()
    } else {
      document.addEventListener('DOMContentLoaded', fn)
    }
  }

  ready(function () {
    var modalEl = document.getElementById('gaConfirmModal')
    if (!modalEl || !window.bootstrap) return // Bootstrap required
    var modalBody = modalEl.querySelector('.comp-confirm-modal__body')
    var confirmBtn = modalEl.querySelector('.ga-confirm-yes')
    var bsModal = new window.bootstrap.Modal(modalEl)
    var pendingAction = null

    function showConfirm(message, onConfirm, title) {
      var modalTitle = modalEl.querySelector('.comp-confirm-modal__title')
      if (modalTitle) modalTitle.textContent = title || 'Confirm action'
      modalBody.textContent = message
      pendingAction = onConfirm
      bsModal.show()
    }

    confirmBtn.addEventListener('click', function () {
      if (pendingAction) pendingAction()
      pendingAction = null
    })

    // Intercept forms with data-confirm
    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        if (form.dataset.confirmAccepted) return // Already confirmed
        e.preventDefault()
        var title = form.getAttribute('data-confirm-title') || 'Confirm action'
        showConfirm(
          form.getAttribute('data-confirm'),
          function () {
            form.dataset.confirmAccepted = 'true'
            form.submit()
          },
          title,
        )
      })
    })

    // Intercept buttons or links with data-confirm
    document
      .querySelectorAll('button[data-confirm], a[data-confirm]')
      .forEach(function (el) {
        el.addEventListener('click', function (e) {
          var isLink = el.tagName === 'A'
          var form = el.form
          e.preventDefault()
          var message = el.getAttribute('data-confirm')
          var title = el.getAttribute('data-confirm-title') || 'Confirm action'
          showConfirm(
            message,
            function () {
              if (isLink) {
                window.location.href = el.getAttribute('href')
                return
              }
              if (form) {
                // Handle formaction override
                var formaction = el.getAttribute('formaction')
                if (formaction) form.setAttribute('action', formaction)
                // Ensure name/value submission when using button name
                if (el.name && !form.querySelector('input[name="' + el.name + '"]')) {
                  var hidden = document.createElement('input')
                  hidden.type = 'hidden'
                  hidden.name = el.name
                  hidden.value = el.value || '1'
                  form.appendChild(hidden)
                }
                form.submit()
              }
            },
            title,
          )
        })
      })
  })
})()
