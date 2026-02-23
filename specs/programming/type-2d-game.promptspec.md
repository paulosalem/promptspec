## Software Type: 2D Game with ECS Architecture

### Core Loop
- The game follows a standard update loop:
  1. Process input events
  2. Run game logic systems (physics, AI, scoring)
  3. Render frame
- All gameplay state is expressed as ECS entities with components — no global mutable singletons.

### Game States
- **Loading**: show progress bar, preload all textures/sounds/fonts.
- **MainMenu**: title screen with Start, Options, Quit. Animated background.
- **Playing**: active gameplay. HUD overlay with score, health, timer as applicable.
- **Paused**: freeze gameplay systems, show semi-transparent overlay with Resume/Quit.
- **GameOver**: show final score, high score, Play Again / Main Menu.

### Player Entity
- Components: `Transform`, `Velocity`, `Sprite`, `Health`, `PlayerInput`, `Collider`.
- Movement: 8-directional or platformer (as spec requires). Acceleration-based, not instant.
- Invulnerability frames: 1.5 seconds after taking damage, visual flash effect.

### Camera
- Smooth follow: lerp toward player position at 5.0 speed factor.
- Camera bounds: clamp to level boundaries, never show outside-of-map void.
- Screen shake: on damage events, amplitude 4px, decay over 0.3 seconds.

### Sound Design
- Categories: `music` (looping BGM), `sfx` (one-shot effects), `ui` (button clicks).
- Volume controls: independent sliders for each category, persisted to config.
- Spatial audio: stereo panning based on entity position relative to camera.

### Scoring & Persistence
- High scores stored locally (RON/JSON file) with top 10 entries.
- Score display: animated counter that rolls up to final value.
