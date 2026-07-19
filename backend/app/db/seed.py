"""Creates and seeds the local SQLite store_inventory database.

This mirrors the schema used in experiment/database_utils.ipynb (t_shirts / discounts)
but targets SQLite instead of MySQL so the project runs with zero external services.
"""

import random
import sqlite3

from app.config import settings

BRANDS = ["Peter England", "Van Huesen", "Levis", "Nike", "Adidas", "Puma"]
COLORS = ["Red", "Blue", "Pink", "Black", "White", "Navy"]
SIZES = ["XS", "S", "M", "L", "XL"]

CREATE_TABLES_SQL = """
DROP TABLE IF EXISTS discounts;
DROP TABLE IF EXISTS t_shirts;

CREATE TABLE t_shirts (
    t_shirt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL CHECK (brand IN ('Peter England','Van Huesen','Levis','Nike','Adidas','Puma')),
    color TEXT NOT NULL CHECK (color IN ('Red','Blue','Pink','Black','White','Navy')),
    size TEXT NOT NULL CHECK (size IN ('XS','S','M','L','XL')),
    price INTEGER NOT NULL CHECK (price BETWEEN 10 AND 50),
    stock_quantity INTEGER NOT NULL,
    UNIQUE (brand, color, size)
);

CREATE TABLE discounts (
    discount_id INTEGER PRIMARY KEY AUTOINCREMENT,
    t_shirt_id INTEGER NOT NULL REFERENCES t_shirts(t_shirt_id),
    pct_discount REAL NOT NULL CHECK (pct_discount BETWEEN 0 AND 100)
);
"""


def seed_database(num_shirts: int = 180, seed: int = 42) -> None:
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)

    connection = sqlite3.connect(settings.sqlite_path)
    try:
        connection.executescript(CREATE_TABLES_SQL)

        combos = [(b, c, s) for b in BRANDS for c in COLORS for s in SIZES]
        rng.shuffle(combos)
        rows = [
            (brand, color, size, rng.randint(10, 50), rng.randint(10, 100))
            for brand, color, size in combos[:num_shirts]
        ]
        connection.executemany(
            "INSERT INTO t_shirts (brand, color, size, price, stock_quantity) VALUES (?, ?, ?, ?, ?)",
            rows,
        )

        shirt_ids = [r[0] for r in connection.execute("SELECT t_shirt_id FROM t_shirts")]
        discount_ids = rng.sample(shirt_ids, k=min(11, len(shirt_ids)))
        discount_rows = [(t_shirt_id, rng.choice([5, 10, 15, 20, 25, 30, 35, 40, 45])) for t_shirt_id in discount_ids]
        connection.executemany(
            "INSERT INTO discounts (t_shirt_id, pct_discount) VALUES (?, ?)",
            discount_rows,
        )

        connection.commit()
        shirt_count = connection.execute("SELECT COUNT(*) FROM t_shirts").fetchone()[0]
        discount_count = connection.execute("SELECT COUNT(*) FROM discounts").fetchone()[0]
        print(f"Seeded {settings.sqlite_path} — t_shirts: {shirt_count}, discounts: {discount_count}")
    finally:
        connection.close()


if __name__ == "__main__":
    seed_database()
