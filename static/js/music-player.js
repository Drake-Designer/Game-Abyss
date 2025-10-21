/**
 * Game Abyss - Background Music Player
 */

;(function () {
  'use strict'

  const music = document.getElementById('gaBgMusic')
  const musicBtn = document.getElementById('gaMusicBtn')
  const musicMute = document.getElementById('gaMusicMute')

  if (!music || !musicBtn || !musicMute) return

  const KEY_TIME = 'gaMusicTime'
  const KEY_PLAYING = 'gaMusicPlaying'
  const DEFAULT_VOLUME = 0.3

  function init() {
    // Set volume
    music.volume = parseFloat(localStorage.getItem('gaMusicVolume')) || DEFAULT_VOLUME

    // Restore position
    const savedTime = localStorage.getItem(KEY_TIME)
    if (savedTime) music.currentTime = parseFloat(savedTime)

    // Check saved state
    const shouldPlay = localStorage.getItem(KEY_PLAYING) === 'yes'

    // Try to restore playback
    if (shouldPlay) {
      // Try immediate play
      music.play().catch(() => {
        // If blocked, show playing UI and wait for interaction
        updateUI(false)
      })
    } else {
      updateUI(true)
    }

    // Button click handler
    musicBtn.onclick = (e) => {
      e.preventDefault()
      e.stopPropagation()

      if (music.paused) {
        music.play()
        localStorage.setItem(KEY_PLAYING, 'yes')
      } else {
        music.pause()
        localStorage.setItem(KEY_PLAYING, 'no')
      }
    }

    // Update UI on play/pause
    music.addEventListener('play', () => updateUI(false))
    music.addEventListener('pause', () => updateUI(true))

    // Save time while playing
    music.addEventListener('timeupdate', () => {
      if (!music.paused) {
        localStorage.setItem(KEY_TIME, music.currentTime.toString())
      }
    })

    // CRITICAL: Force play before navigation if music should be playing
    document.addEventListener(
      'click',
      (e) => {
        const link = e.target.closest('a[href]')
        if (link && !link.target) {
          // Save current state
          const isPlaying = !music.paused
          localStorage.setItem(KEY_PLAYING, isPlaying ? 'yes' : 'no')
          if (isPlaying) {
            localStorage.setItem(KEY_TIME, music.currentTime.toString())
          }

          // If music should be playing, force a play attempt RIGHT NOW
          // This creates a user interaction that bypasses autoplay blocks
          if (localStorage.getItem(KEY_PLAYING) === 'yes' && music.paused) {
            music.play().catch(() => {})
          }
        }
      },
      true,
    )

    // Retry play on ANY click if music should be playing but is paused
    document.addEventListener('click', () => {
      if (localStorage.getItem(KEY_PLAYING) === 'yes' && music.paused) {
        music.play().catch(() => {})
      }
    })

    // Save on page unload
    window.addEventListener('beforeunload', () => {
      const playing = !music.paused
      localStorage.setItem(KEY_PLAYING, playing ? 'yes' : 'no')
      if (playing) {
        localStorage.setItem(KEY_TIME, music.currentTime.toString())
      }
    })
  }

  function updateUI(isMuted) {
    musicBtn.classList.toggle('ga-playing', !isMuted)
    musicBtn.classList.toggle('ga-paused', isMuted)
    musicMute.classList.toggle('ga-visible', isMuted)
  }

  document.readyState === 'loading'
    ? document.addEventListener('DOMContentLoaded', init)
    : init()
})()
