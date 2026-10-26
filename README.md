# IRON FRONT — Ashes of the Machine

An original side-scrolling native Android run-and-gun game. Fully offline, multi-touch and landscape fullscreen.

## Controls
- Touch left-side joystick to run.
- JUMP: jump; double tap for a double jump.
- Hold FIRE to shoot. Drag finger vertically on FIRE to aim up/down.
- DASH to rush briefly without taking damage, BOMB to throw a grenade.
- Top-right pause button, tap paused overlay to resume.

## Features
Three zones: Obsidian Jungle, Neon Exodus, Last Reactor. Three 9,000-unit levels, checkpoints, three weapon types (Pulse, Spread, Rail), moving infantry, flying drones, turrets, brutes, enormous bosses, parallax art, weather, particles, screen shake, original synthesized soundtrack and effects.

## Build
JDK 17, Android SDK platform 35, Gradle 8.6+. `pip install Pillow`; `ART_OUT=app/src/main/assets python gen_art.py` to regenerate original graphics and audio; `gradle assembleDebug`.
The GitHub Actions build uploads `IronFront.apk` to Releases.

No copied Contra artwork, no tracking, no Internet permissions.
