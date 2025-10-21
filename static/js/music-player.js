/**
 * Game Abyss - Background Music Player
 */

;(function () {
  'use strict'

  const music = document.getElementById('gaBgMusic')
  const musicBtn = document.getElementById('gaMusicBtn')
  const musicMute = document.getElementById('gaMusicMute')

  if (!music || !musicBtn || !musicMute) return

  const STORAGE_TIME = 'gaMusicTime'
  const DEFAULT_VOLUME = 0.3

  function init() {
    // Set volume and restore position
    music.volume = parseFloat(localStorage.getItem('gaMusicVolume')) || DEFAULT_VOLUME
    const savedTime = localStorage.getItem(STORAGE_TIME)
    if (savedTime) music.currentTime = parseFloat(savedTime)

    // Try autoplay
    music
      .play()
      .then(() => updateState(true))
      .catch(() => updateState(false))

    // Event listeners
    musicBtn.onclick = () => (music.paused ? music.play() : music.pause())
    music.onplay = () => updateState(true)
    music.onpause = () => updateState(false)

    // Save time
    let saveTimeout
    music.ontimeupdate = window.onbeforeunload = () => {
      clearTimeout(saveTimeout)
      saveTimeout = setTimeout(() => {
        if (!music.paused) localStorage.setItem(STORAGE_TIME, music.currentTime)
      }, 200)
    }

    // Start on first click if blocked
    document.addEventListener('click', () => music.paused && music.play(), {
      once: true,
    })
  }

  function updateState(isPlaying) {
    musicBtn.classList.toggle('ga-playing', isPlaying)
    musicBtn.classList.toggle('ga-paused', !isPlaying)
    musicMute.classList.toggle('ga-visible', !isPlaying)
  }

  document.readyState === 'loading'
    ? document.addEventListener('DOMContentLoaded', init)
    : init()
})()
