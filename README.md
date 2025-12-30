# Vanitas

**Vanitas** is a 2D side-scrolling action game built with **Python and Pygame**, centered around revenge, loss, and the cost of obsession.

The game tells a simple but heavy story:  
in the pursuit of vengeance, you slowly erase the very person you loved.

---

## 🕯 Story & Themes

We were happily married.  
Then someone murdered my wife.

I chase the killer, driven by rage and grief. But I am not strong enough.  
To move forward, I must let go.

Progress in *Vanitas* is tied directly to **forgetting**:
- To gain speed, I forget our **first date**
- To survive longer, I forget **her voice**
- To reach the final confrontation, I must forget **her name**

Each sacrifice grants power, but removes meaning.

By the time I finally confront the killer and strike the final blow,  
I succeed.

But I cannot remember who I did it for.

In the end, revenge costs more than it gives.

---

## 🎮 Gameplay Overview

- Single-player 2D side-view action game
- Heavy focus on **boss encounters**
- Narrative progression through cutscenes and dialogue
- Abilities are unlocked by sacrificing memories
- Minimalist design with strong visual telegraphing

---

## 🕹 Controls

| Action | Key |
|------|----|
| Move Left | A |
| Move Right | D |
| Jump | W |
| Attack | J |
| Dash (unlockable) | K |
| Confirm / Continue | SPACE |

---

## 🎥 Gameplay Preview

<iframe src="https://drive.google.com/file/d/1HASuVZ-mL2vsHd027esL-EG_skmPEPNN/preview" width="720" height="405" allow="autoplay">
</iframe>

> If the video does not load, [watch it here on Google Drive](https://drive.google.com/file/d/1HASuVZ-mL2vsHd027esL-EG_skmPEPNN/view).

---

## 🧠 Core Mechanics

### Memory Sacrifice System
Progression requires letting go of personal memories.  
Each memory lost weakens the protagonist emotionally but strengthens them mechanically.

### Boss-Focused Combat
Each boss represents a different challenge:
- **Papia** – A ranged, pattern-based boss that tests positioning and awareness
- **Harus** – A melee-focused boss that tests timing, discipline, and counterplay

### Visual Telegraphing
All major attacks are clearly telegraphed using animation, effects, and screen shake to ensure fairness.

---

## 🗂 Project Structure

```text
.
├── main.py        # Main game loop and state management
├── player.py      # Player movement, combat, and animations
├── bosses.py      # Boss logic and attack patterns
├── story.py       # Cutscenes and dialogue systems
├── settings.py    # Constants, colors, game states, helpers
├── assets/        # Sprites, sound effects, UI elements
