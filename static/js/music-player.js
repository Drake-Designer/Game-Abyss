/**
 * Game Abyss - Background Music Player
 */
;(function () {
  'use strict'

  const music = document.getElementById('gaBgMusic')
  const musicBtn = document.getElementById('gaMusicBtn')
  const musicMute = document.getElementById('gaMusicMute')
  const toastEl = document.getElementById('musicToast')

  if (!music || !musicBtn || !musicMute) return

  const KEY_TIME = 'gaMusicTime'
  const KEY_PLAYING = 'gaMusicPlaying'
  const KEY_TOAST = 'gaMusicToastShown'
  const DEFAULT_VOLUME = 0.3

  function init() {
    music.volume = DEFAULT_VOLUME

    // Restore position
    const savedTime = localStorage.getItem(KEY_TIME)
    if (savedTime) music.currentTime = parseFloat(savedTime)

    // Restore state
    const shouldPlay = localStorage.getItem(KEY_PLAYING) === 'yes'
    if (shouldPlay) {
      music.play().catch(() => updateUI(true))
    } else {
      updateUI(true)
    }

    // Button click
    musicBtn.onclick = (e) => {
      e.preventDefault()
      if (music.paused) {
        music
          .play()
          .then(() => {
            localStorage.setItem(KEY_PLAYING, 'yes')
          })
          .catch(() => updateUI(true))
      } else {
        music.pause()
        localStorage.setItem(KEY_PLAYING, 'no')
      }
    }

    // Events
    music.addEventListener('play', () => updateUI(false))
    music.addEventListener('pause', () => updateUI(true))
    music.addEventListener('timeupdate', () => {
      if (!music.paused) {
        localStorage.setItem(KEY_TIME, music.currentTime.toString())
      }
    })

    // Before unload
    window.addEventListener('beforeunload', () => {
      if (!music.paused) {
        localStorage.setItem(KEY_TIME, music.currentTime.toString())
      }
    })

    // Show toast only once
    showToastOnce()
  }

  function updateUI(isMuted) {
    musicBtn.classList.toggle('util-is-playing', !isMuted)
    musicBtn.classList.toggle('util-is-paused', isMuted)
    musicMute.classList.toggle('util-visible', isMuted)
  }

  function showToastOnce() {
    if (!toastEl || !window.bootstrap || !bootstrap.Toast) return
    if (localStorage.getItem(KEY_TOAST) === 'yes') return

    const toast = new bootstrap.Toast(toastEl, { delay: 4000, autohide: true })
    toast.show()
    localStorage.setItem(KEY_TOAST, 'yes')
  }

  document.readyState === 'loading'
    ? document.addEventListener('DOMContentLoaded', init)
    : init()
})()
