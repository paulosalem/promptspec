## Tech Stack: Rust + Bevy Game Engine

### Engine & Language
- **Language**: Rust (latest stable edition)
- **Game engine**: Bevy 0.14+ with ECS architecture
- **Windowing**: winit via Bevy's default window plugin
- **Rendering**: Bevy's built-in 2D renderer (or 3D renderer if spec requires)
- **Audio**: bevy_audio with kira backend

### Architecture
- **Pattern**: Entity-Component-System (ECS) — zero inheritance, composition only
- **Systems**: group by concern in plugins (e.g., `PlayerPlugin`, `PhysicsPlugin`, `UIPlugin`)
- **States**: Bevy `States` enum for game phases (Loading, Menu, Playing, Paused, GameOver)
- **Events**: Bevy `Event` types for decoupled communication between systems
- **Resources**: global state as Bevy `Resource` types (e.g., `Score`, `GameConfig`)
- **Assets**: Bevy `AssetServer` with handles; load during `Loading` state, never in gameplay

### Game Loop Conventions
- **Fixed timestep**: physics and game logic in `FixedUpdate` schedule (60 Hz default)
- **Rendering**: visual updates in `Update` schedule (variable frame rate)
- **Input**: read via Bevy `Input<KeyCode>`, `Input<GamepadButton>`, `CursorMoved` events
- **Collision**: bevy_rapier2d (or 3D) for physics-based collision; AABB for simple overlap checks

### Testing
- **Unit tests**: `#[cfg(test)]` modules for pure logic (damage calc, scoring, state machines)
- **Integration**: Bevy's headless mode (`MinimalPlugins`) for system-level tests
- **Assets**: mock asset handles in tests; never load real files

### Build & Distribution
- **Target**: native desktop (Windows, macOS, Linux); WASM via `trunk` if web required
- **Release**: `--release` with LTO enabled, strip symbols
- **Config**: RON files for tunable game parameters (loaded as Bevy assets)
