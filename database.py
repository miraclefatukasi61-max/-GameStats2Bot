import sqlite3
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "game_stats.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        total_games INTEGER DEFAULT 0,
                        total_wins INTEGER DEFAULT 0,
                        total_losses INTEGER DEFAULT 0,
                        total_draws INTEGER DEFAULT 0,
                        total_points INTEGER DEFAULT 0,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS game_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        game_type TEXT,
                        opponent TEXT,
                        result TEXT,
                        points INTEGER DEFAULT 0,
                        played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                ''')
                
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON game_sessions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wins ON users(total_wins)')
                
                conn.commit()
                logger.info("✅ Database ready")
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            raise

    def register_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, last_active)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, username, first_name, last_name))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Register error: {e}")
            return False

    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"❌ Stats error: {e}")
            return None

    def update_game_result(self, user_id: int, result: str, game_type: str = "unknown", opponent: str = "AI", points: int = 0):
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET total_games = total_games + 1,
                        total_wins = total_wins + ?,
                        total_losses = total_losses + ?,
                        total_draws = total_draws + ?,
                        total_points = total_points + ?,
                        last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (
                    1 if result == 'win' else 0,
                    1 if result == 'loss' else 0,
                    1 if result == 'draw' else 0,
                    points,
                    user_id
                ))
                
                cursor.execute('''
                    INSERT INTO game_sessions (user_id, game_type, opponent, result, points)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, game_type, opponent, result, points))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Update error: {e}")
            return False

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT username, first_name, total_games, total_wins, total_losses, total_draws, total_points,
                           ROUND(CAST(total_wins AS FLOAT) / NULLIF(total_games, 0) * 100, 1) as win_rate
                    FROM users
                    WHERE total_games > 0
                    ORDER BY total_points DESC, total_wins DESC
                    LIMIT ?
                ''', (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ Leaderboard error: {e}")
            return []

    def get_game_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT game_type, opponent, result, points, played_at
                    FROM game_sessions
                    WHERE user_id = ?
                    ORDER BY played_at DESC
                    LIMIT ?
                ''', (user_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ History error: {e}")
            return []

db = Database()
