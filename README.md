# LoS Aimbot & Mirror Strafing Game

A 2D Python game built with Pygame. This project demonstrates advanced player-assist mechanics designed for beginners, featuring a predictive 6-round burst aimbot and Line of Sight (LoS) mirror strafing.

## 🌟 Features

1. **Predictive Aiming (Aimbot)**
   - Calculates the target's current velocity, distance, and bullet speed using a quadratic equation to predict the exact future collision point.
   - Fires a 6-round burst that dynamically adjusts to hit a moving target 100% of the time.

2. **Mirror Strafing on LoS Axis**
   - Once a bullet hits the enemy, the player enters "Mirror Strafing" mode.
   - The player is locked onto an invisible Line of Sight (LoS) axis connecting them to the enemy.
   - If the enemy moves, the player automatically mirrors their movement to maintain the exact same distance and angle.

3. **Dynamic Distance Control**
   - While in Mirror Strafing mode, the player can move back and forth along the LoS axis to close the gap or retreat, all while perfectly tracking the enemy.

## 🛠️ Prerequisites

- Python 3.7 or higher
- [Pygame](https://www.pygame.org/)

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/los-aimbot-game.git
   cd los-aimbot-game
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🎮 How to Play

Run the main game script:
```bash
python game.py
```

### Controls
- **WASD**: Normal Movement (when not locked on).
- **Mouse Left Click**: Fire a 6-round predictive burst.
- **W / S (During Lock-on)**: Move closer or further away along the LoS axis.
- **SPACEBAR**: Break the mirror strafing lock-on and return to normal movement.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
