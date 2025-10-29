/* ============================================================
   *** SCRIPT: Home Page - Pagination ***
   ============================================================ */
;(function () {
  'use strict'

  document.addEventListener('DOMContentLoaded', function () {
    const sections = document.querySelectorAll('[data-home-section]')
    if (!sections.length) {
      return
    }

    const reduceMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')

    sections.forEach(function (section) {
      section.addEventListener('click', function (event) {
        const link = event.target.closest('a[data-pagination-link]')
        if (!link || !section.contains(link)) {
          return
        }

        if (
          event.defaultPrevented ||
          event.button !== 0 ||
          event.metaKey ||
          event.ctrlKey ||
          event.shiftKey ||
          event.altKey
        ) {
          return
        }

        event.preventDefault()
        changePage(section, link)
      })
    })

    async function changePage(section, link) {
      if (section.dataset.isLoading === 'true') {
        return
      }

      const targetHref = link.getAttribute('href')
      const pageParam = section.dataset.pageParam
      const sectionName = section.dataset.homeSection
      const partialUrl = section.dataset.paginationUrl
      const list = section.querySelector('[data-posts-list]')
      const pagination = section.querySelector('[data-pagination]')
      const spinner = section.querySelector('.home-posts__spinner')

      const resolvedHref = new URL(targetHref, window.location.origin)
      const requestedPage = resolvedHref.searchParams.get(pageParam) || '1'
      const requestUrl = new URL(partialUrl, window.location.origin)
      requestUrl.searchParams.set('section', sectionName)
      requestUrl.searchParams.set('page', requestedPage)

      section.dataset.isLoading = 'true'
      section.classList.add('is-loading')
      section.setAttribute('aria-busy', 'true')

      if (spinner) {
        spinner.setAttribute('aria-hidden', 'false')
      }

      let exitAnimation = Promise.resolve()
      if (!reduceMotionQuery.matches && list && typeof list.animate === 'function') {
        const animation = list.animate(
          [
            { opacity: 1, transform: 'translateX(0)' },
            { opacity: 0, transform: 'translateX(-24px)' },
          ],
          { duration: 220, easing: 'ease', fill: 'forwards' },
        )
        exitAnimation = animation.finished.catch(() => undefined)
      }

      try {
        const response = await fetch(requestUrl.toString(), {
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          credentials: 'same-origin',
        })

        if (!response.ok) {
          throw new Error('Failed request')
        }

        const payload = await response.json()
        await exitAnimation

        if (list) {
          list.innerHTML = payload.posts_html
        }

        if (pagination) {
          pagination.innerHTML = payload.pagination_html
        }

        if (!reduceMotionQuery.matches && list && typeof list.animate === 'function') {
          const enterAnimation = list.animate(
            [
              { opacity: 0, transform: 'translateX(24px)' },
              { opacity: 1, transform: 'translateX(0)' },
            ],
            { duration: 260, easing: 'ease', fill: 'forwards' },
          )
          enterAnimation.finished.catch(() => undefined)
        } else if (list) {
          list.style.opacity = ''
          list.style.transform = ''
        }

        if (typeof payload.page === 'number') {
          section.dataset.currentPage = String(payload.page)
        }

        if ('history' in window && typeof history.replaceState === 'function') {
          const newUrl = new URL(window.location.href)
          const pageValue = Number(payload.page || requestedPage)
          if (Number.isFinite(pageValue) && pageValue > 1) {
            newUrl.searchParams.set(pageParam, pageValue)
          } else {
            newUrl.searchParams.delete(pageParam)
          }
          newUrl.searchParams.delete('page')
          history.replaceState({}, '', newUrl.toString())
        }

        if (typeof section.focus === 'function') {
          try {
            section.focus({ preventScroll: reduceMotionQuery.matches })
          } catch (err) {
            section.focus()
          }
        }
      } catch (error) {
        window.location.href = resolvedHref.toString()
      } finally {
        section.dataset.isLoading = 'false'
        section.classList.remove('is-loading')
        section.setAttribute('aria-busy', 'false')
        if (spinner) {
          spinner.setAttribute('aria-hidden', 'true')
        }
      }
    }
  })
})()
