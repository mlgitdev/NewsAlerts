# Audio Alerts & Volume Controls

Auditory alerting allows momentum traders to keep their eyes on charting software or Level 2 order books while staying alerted to emerging runners.

---

## 🔔 Master Bell Toggle (The Bell)

- Located in the top-right header of the terminal (bell icon).
- **Hotkey**: Press `M` to toggle mute.
- **Unified Control**: Clicking the bell immediately:
  1. Mutes all audible chimes and bells.
  2. Pauses outgoing Telegram alert dispatching.
- The bell icon dynamically displays an amber strikethrough badge when muted.

---

## 🔊 Interactive Rising Triangle Volume Scrubber

NewsAlerts features a unique institutional **Rising Triangle Volume Scrubber** in the top header:
- Click or drag across the triangular volume wedge to smoothly scale volume from **0% to 100%**.
- Real-time audio feedback plays a soft preview tone at the selected level.
- On Windows, uses per-process WinMM `waveOutSetVolume` scaling without modifying your master operating system volume.
- On macOS and Linux, smoothly scales playback parameters (`afplay -v`, `paplay`).

---

## 🎵 Sound Customization

- Default audio files reside in `assets/sounds/` (`bell.wav`, `chime.wav`, `alert.wav`, `surge.wav`).
- Sound files can be configured individually per strategy in the Settings modal.
- Audio calls are executed asynchronously in background worker threads to guarantee zero UI lag or dropped animation frames.
