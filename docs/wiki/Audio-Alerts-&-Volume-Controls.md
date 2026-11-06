# Audio Alerts & Volume Controls

Auditory alerting allows momentum traders to keep their eyes on charting software or Level 2 order books while staying alerted to emerging runners.

---

## 🔔 In-App Audio Alerts Bell (`#btn-mute`)

- Located in the top-right header of the terminal (bell icon).
- **Hotkey**: Press `M` to toggle in-app audio mute.
- **Dedicated Audio Control**: Clicking the bell immediately mutes or resumes local workstation audio chimes without affecting outgoing Telegram push alerts.
- **Visual Feedback**:
  - **Active**: Vibrant green bell (`#38efb0`).
  - **Muted**: Red-tinted slashed bell (`#ff6b7e`) with pulsing alert indicator (`pausePulse`).
- Paired alongside the dedicated **Telegram Push Alerts Bell** (`#btn-telegram`), giving traders independent controls for desk vs. mobile alerting.

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
