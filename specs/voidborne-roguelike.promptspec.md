# Voidborne — 2D Space Roguelike

@refine programming/base-spec-author.promptspec.md
@refine programming/stack-rust-bevy.promptspec.md
@refine programming/type-2d-game.promptspec.md

@audience "Rust game developer implementing from this spec"
@style "precise, systems-oriented, performance-conscious"

## Game Concept

Voidborne is a **2D top-down space roguelike** where the player pilots a ship
through procedurally generated sectors, fighting enemies, collecting upgrades,
and facing a boss at the end of each zone. Runs last 20–40 minutes. Death is
permanent — progress carries over only as unlockable ship blueprints.

## Gameplay Systems

### Ship & Movement
- Top-down twin-stick controls: left stick/WASD moves, right stick/mouse aims.
- Ship has `thrust` (acceleration), `max_speed`, `drag` (deceleration coefficient).
- Boost: press shift to double thrust for 2 seconds, 8-second cooldown.
- Ship hitbox: circle collider, radius = 12px at default sprite scale.

### Combat
- Primary weapon: auto-fires toward aim direction. Stats: `damage`, `fire_rate`,
  `projectile_speed`, `spread_angle`. Defined per weapon type.
- Secondary weapon: activated ability with cooldown (missile barrage, shield, EMP).
- Damage formula: `final_damage = base_damage * (1 + damage_bonus) - target_armor`.
  Minimum 1 damage. Critical hits: 15% base chance, 2x multiplier.

### Enemies
@match enemy_complexity
  "simple" ==>
    - 4 enemy types: Drone (chases), Turret (stationary, aimed), Bomber (slow, AoE),
      Sniper (long-range, telegraphed shot).
    - Each has: health, damage, speed, behavior (FSM with Idle → Aggro → Attack states).
    - Spawn system: wave-based per room, scaled by zone difficulty multiplier.

  "complex" ==>
    - 8 enemy types: all from "simple" plus Elite variants with shields,
      Swarmers (spawn in packs of 6, low HP), Cloakers (invisible until close),
      Carriers (spawn drones), and Minibosses (appear every 5 rooms).
    - Elite enemies: 2x HP, special ability (shield regen, homing shots, teleport).
    - Behavior trees instead of FSMs: patrol → detect → engage → flee-when-low-HP.
    - Director system: dynamically adjusts spawn rate based on player performance
      (time-to-kill, damage taken, items collected).

### Procedural Generation
- Each zone = 8–12 interconnected rooms (graph, not grid).
- Room types: Combat, Shop, Treasure, Rest (heal 30% HP), Boss.
- Generation algorithm:
  1. Place start room.
  2. Branch 2–3 paths, each 3–5 rooms.
  3. Converge paths at pre-boss room.
  4. Place boss room after convergence.
  5. Randomly assign room types (at least 1 shop, 1 rest per zone).
- Room interiors: hand-authored tile templates with randomized obstacle placement.

### Upgrades & Items
- Passive upgrades: +damage%, +speed%, +armor, +crit chance, etc.
  Stack additively. Max 6 passive slots.
- Weapon pickups: replace current primary or secondary.
- Currency: "Scrap" dropped by enemies. Spent at shops.
- Meta-progression: "Data Cores" (persist across runs) unlock new ship blueprints
  and starting passive options.

### Boss Fights
- One boss per zone, 3 zones total.
- Each boss has 3 phases with distinct attack patterns.
- Phase transitions at 66% and 33% HP — brief invulnerable animation + arena change.
- Telegraphed attacks: danger zones shown 0.8 seconds before damage.

## HUD & UI
- HUD (during gameplay): HP bar (top-left), boost cooldown arc, weapon icons,
  minimap (top-right, shows room layout), scrap counter.
- Pause menu: Resume, Controls, Quit Run.
- Death screen: stats summary (enemies killed, damage dealt, time survived, scrap earned),
  data cores earned, "Try Again" button.

@assert "Every game mechanic must include specific numeric values (damage, cooldowns, percentages)"
@assert "The spec must define all ECS components for player, enemies, and projectiles"

@output_format "markdown"
  Structure the output as:
  1. Architecture Overview (ECS plugins, state machine)
  2. Component Definitions (all ECS components with types)
  3. System Definitions (each system's responsibilities and schedule)
  4. Asset Requirements (sprites, sounds, fonts — listed with dimensions/formats)
  5. Game Balance Table (all numeric parameters in one reference table)
  6. Testing Plan
