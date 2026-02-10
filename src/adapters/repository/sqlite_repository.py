"""SQLite 기반 저장소 구현"""

import json
import sqlite3
from datetime import date
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from core.domain.player import Player
from core.domain.competitor import Competitor
from core.domain.turn import Turn, GamePhase, DaySegment
from core.domain.store import Store
from core.domain.product import Product
from core.domain.inventory import Inventory
from core.domain.research import Research
from core.domain.value_objects import Money, Percentage, Progress, StatValue, Experience
from core.ports.repository_port import RepositoryPort


# ── DDL ──

_DDL = """
CREATE TABLE IF NOT EXISTS games (
    id              TEXT PRIMARY KEY,
    player_name     TEXT NOT NULL,
    created_at      TEXT DEFAULT (datetime('now')),
    is_active       INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS players (
    id              TEXT PRIMARY KEY,
    game_id         TEXT NOT NULL REFERENCES games(id),
    name            TEXT NOT NULL,
    cooking_base    INTEGER DEFAULT 10,
    cooking_exp     INTEGER DEFAULT 0,
    management_base INTEGER DEFAULT 8,
    management_exp  INTEGER DEFAULT 0,
    service_base    INTEGER DEFAULT 8,
    service_exp     INTEGER DEFAULT 0,
    tech_base       INTEGER DEFAULT 5,
    tech_exp        INTEGER DEFAULT 0,
    stamina_base    INTEGER DEFAULT 50,
    stamina_exp     INTEGER DEFAULT 0,
    fatigue         REAL DEFAULT 0.0,
    happiness       REAL DEFAULT 50.0,
    money           INTEGER DEFAULT 2000000,
    store_ids_json  TEXT DEFAULT '[]',
    research_ids_json TEXT DEFAULT '[]',
    UNIQUE(game_id)
);

CREATE TABLE IF NOT EXISTS stores (
    id              TEXT PRIMARY KEY,
    game_id         TEXT NOT NULL REFERENCES games(id),
    owner_id        TEXT NOT NULL,
    name            TEXT NOT NULL,
    monthly_rent    INTEGER DEFAULT 1500000,
    product_ids_json TEXT DEFAULT '[]',
    inventory_item_ids_json TEXT DEFAULT '[]',
    parttime_worker_ids_json TEXT DEFAULT '[]',
    manager_id      TEXT,
    is_first_store  INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS products (
    id              TEXT PRIMARY KEY,
    game_id         TEXT NOT NULL REFERENCES games(id),
    name            TEXT NOT NULL,
    recipe_id       TEXT NOT NULL,
    selling_price   INTEGER DEFAULT 20000,
    research_progress INTEGER DEFAULT 0,
    awareness       INTEGER DEFAULT 10,
    ingredients_json TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS turns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id         TEXT NOT NULL REFERENCES games(id),
    turn_number     INTEGER NOT NULL,
    game_date       TEXT NOT NULL,
    current_phase   TEXT DEFAULT 'PLAYER_ACTION',
    is_complete     INTEGER DEFAULT 0,
    UNIQUE(game_id, turn_number)
);

CREATE TABLE IF NOT EXISTS game_state (
    game_id         TEXT PRIMARY KEY REFERENCES games(id),
    remaining_hours INTEGER DEFAULT 12,
    ingredient_qty  INTEGER DEFAULT 100,
    prepared_qty    INTEGER DEFAULT 0,
    ingredient_freshness REAL DEFAULT 90.0,
    reputation      INTEGER DEFAULT 50,
    wake_time       INTEGER DEFAULT 7,
    open_time       INTEGER DEFAULT 10,
    close_time      INTEGER DEFAULT 21,
    sleep_time      INTEGER DEFAULT 24,
    current_segment TEXT DEFAULT 'PREP',
    segment_hours_used INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS queued_actions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id         TEXT NOT NULL,
    turn_number     INTEGER NOT NULL,
    slot_order      INTEGER NOT NULL,
    action_type     TEXT NOT NULL,
    specific_action TEXT NOT NULL,
    hours           REAL NOT NULL,
    cost            INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'QUEUED',
    segment         TEXT DEFAULT 'PREP',
    UNIQUE(game_id, turn_number, slot_order)
);

CREATE TABLE IF NOT EXISTS business_decisions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id         TEXT NOT NULL,
    turn_number     INTEGER NOT NULL,
    decision_key    TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT DEFAULT '',
    choice_a_label  TEXT NOT NULL,
    choice_b_label  TEXT NOT NULL,
    choice_a_effect TEXT DEFAULT '{}',
    choice_b_effect TEXT DEFAULT '{}',
    trigger_hour    INTEGER DEFAULT 0,
    player_choice   TEXT DEFAULT NULL,
    effect_json     TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS phase_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id         TEXT NOT NULL,
    turn_number     INTEGER NOT NULL,
    phase           TEXT NOT NULL,
    result_json     TEXT NOT NULL,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS competitors (
    id              TEXT PRIMARY KEY,
    game_id         TEXT NOT NULL REFERENCES games(id),
    data_json       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_data (
    id              TEXT PRIMARY KEY,
    game_id         TEXT NOT NULL REFERENCES games(id),
    data_json       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analysis_data (
    player_id       TEXT PRIMARY KEY,
    game_id         TEXT NOT NULL REFERENCES games(id),
    analysis_json   TEXT NOT NULL,
    turn_number     INTEGER DEFAULT 0
);
"""


class SQLiteRepository(RepositoryPort):
    """SQLite 기반 RepositoryPort 구현"""

    def __init__(self, db_path: str, game_id: str = None):
        self._db_path = db_path
        self._game_id = game_id
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        try:
            conn.executescript(_DDL)
            conn.commit()
        finally:
            conn.close()

    @property
    def game_id(self) -> str:
        return self._game_id

    @game_id.setter
    def game_id(self, value: str):
        self._game_id = value

    # ── Game lifecycle ──

    def create_game(self, game_id: str, player_name: str):
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO games (id, player_name) VALUES (?, ?)",
                (game_id, player_name),
            )
            conn.execute(
                "INSERT INTO game_state (game_id) VALUES (?)",
                (game_id,),
            )
            conn.commit()
        finally:
            conn.close()
        self._game_id = game_id

    def get_game(self, game_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone()
            if not row:
                return None
            return dict(row)
        finally:
            conn.close()

    def list_active_games(self) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT g.*, gs.remaining_hours, gs.ingredient_qty "
                "FROM games g LEFT JOIN game_state gs ON g.id=gs.game_id "
                "WHERE g.is_active=1 ORDER BY g.created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def deactivate_game(self, game_id: str):
        conn = self._get_conn()
        try:
            conn.execute("UPDATE games SET is_active=0 WHERE id=?", (game_id,))
            conn.commit()
        finally:
            conn.close()

    # ── Player ──

    def save_player(self, player: Player) -> None:
        conn = self._get_conn()
        try:
            store_ids = json.dumps([str(sid) for sid in player.store_ids])
            research_ids = json.dumps([str(rid) for rid in player.research_ids])
            conn.execute(
                """INSERT OR REPLACE INTO players
                   (id, game_id, name, cooking_base, cooking_exp,
                    management_base, management_exp, service_base, service_exp,
                    tech_base, tech_exp, stamina_base, stamina_exp,
                    fatigue, happiness, money, store_ids_json, research_ids_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(player.id), self._game_id, player.name,
                    player.cooking.base_value, player.cooking.experience.value,
                    player.management.base_value, player.management.experience.value,
                    player.service.base_value, player.service.experience.value,
                    player.tech.base_value, player.tech.experience.value,
                    player.stamina.base_value, player.stamina.experience.value,
                    player.fatigue.value, player.happiness.value,
                    player.money.amount, store_ids, research_ids,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_player(self, player_id: UUID) -> Optional[Player]:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM players WHERE id=?", (str(player_id),)).fetchone()
            if not row:
                return None
            return self._row_to_player(row)
        finally:
            conn.close()

    def get_player_by_game(self, game_id: str) -> Optional[Player]:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM players WHERE game_id=?", (game_id,)).fetchone()
            if not row:
                return None
            return self._row_to_player(row)
        finally:
            conn.close()

    def get_all_players(self) -> List[Player]:
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT * FROM players WHERE game_id=?", (self._game_id,)).fetchall()
            return [self._row_to_player(r) for r in rows]
        finally:
            conn.close()

    def _row_to_player(self, row) -> Player:
        store_ids = tuple(UUID(s) for s in json.loads(row["store_ids_json"]))
        research_ids = tuple(UUID(s) for s in json.loads(row["research_ids_json"]))
        return Player(
            id=UUID(row["id"]),
            name=row["name"],
            cooking=StatValue(row["cooking_base"], Experience(row["cooking_exp"])),
            management=StatValue(row["management_base"], Experience(row["management_exp"])),
            service=StatValue(row["service_base"], Experience(row["service_exp"])),
            tech=StatValue(row["tech_base"], Experience(row["tech_exp"])),
            stamina=StatValue(row["stamina_base"], Experience(row["stamina_exp"])),
            fatigue=Percentage(row["fatigue"]),
            happiness=Percentage(row["happiness"]),
            money=Money(row["money"]),
            store_ids=store_ids,
            research_ids=research_ids,
        )

    # ── Competitor ──

    def save_competitor(self, competitor: Competitor) -> None:
        conn = self._get_conn()
        try:
            # Serialize competitor to JSON for simplicity
            data = json.dumps({"id": str(competitor.id), "name": getattr(competitor, "name", "")})
            conn.execute(
                "INSERT OR REPLACE INTO competitors (id, game_id, data_json) VALUES (?,?,?)",
                (str(competitor.id), self._game_id, data),
            )
            conn.commit()
        finally:
            conn.close()

    def get_all_competitors(self) -> List[Competitor]:
        # Return empty list — competitors are not deeply persisted in this version
        return []

    # ── Turn ──

    def save_turn(self, turn: Turn) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO turns
                   (game_id, turn_number, game_date, current_phase, is_complete)
                   VALUES (?,?,?,?,?)""",
                (
                    self._game_id,
                    turn.turn_number,
                    turn.game_date.isoformat(),
                    turn.current_phase.name,
                    1 if turn.is_complete else 0,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def load_game(self, save_name: str) -> Optional[Dict[str, Any]]:
        return self.get_game(save_name)

    def load_current_turn(self) -> Optional[Turn]:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM turns WHERE game_id=? ORDER BY turn_number DESC LIMIT 1",
                (self._game_id,),
            ).fetchone()
            if not row:
                return None
            return self._row_to_turn(row)
        finally:
            conn.close()

    def _row_to_turn(self, row) -> Turn:
        return Turn(
            turn_number=row["turn_number"],
            game_date=date.fromisoformat(row["game_date"]),
            current_phase=GamePhase[row["current_phase"]],
            is_complete=bool(row["is_complete"]),
        )

    # ── Store ──

    def save_store(self, store: Store) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO stores
                   (id, game_id, owner_id, name, monthly_rent,
                    product_ids_json, inventory_item_ids_json,
                    parttime_worker_ids_json, manager_id, is_first_store)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(store.id), self._game_id, str(store.owner_id),
                    store.name, store.monthly_rent.amount,
                    json.dumps([str(p) for p in store.product_ids]),
                    json.dumps([str(i) for i in store.inventory_item_ids]),
                    json.dumps([str(w) for w in store.parttime_worker_ids]),
                    str(store.manager_id) if store.manager_id else None,
                    1 if store.is_first_store else 0,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_store(self, store_id: UUID) -> Optional[Store]:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM stores WHERE id=?", (str(store_id),)).fetchone()
            if not row:
                return None
            return self._row_to_store(row)
        finally:
            conn.close()

    def get_store_by_game(self, game_id: str) -> Optional[Store]:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM stores WHERE game_id=? LIMIT 1", (game_id,)).fetchone()
            if not row:
                return None
            return self._row_to_store(row)
        finally:
            conn.close()

    def _row_to_store(self, row) -> Store:
        return Store(
            id=UUID(row["id"]),
            owner_id=UUID(row["owner_id"]),
            name=row["name"],
            is_first_store=bool(row["is_first_store"]),
            monthly_rent=Money(row["monthly_rent"]),
            product_ids=tuple(UUID(p) for p in json.loads(row["product_ids_json"])),
            inventory_item_ids=tuple(UUID(i) for i in json.loads(row["inventory_item_ids_json"])),
            parttime_worker_ids=tuple(UUID(w) for w in json.loads(row["parttime_worker_ids_json"])),
            manager_id=UUID(row["manager_id"]) if row["manager_id"] else None,
        )

    # ── Product ──

    def save_product(self, product: Product) -> None:
        conn = self._get_conn()
        try:
            ingredients = json.dumps([
                {
                    "id": str(ing.id), "name": ing.name,
                    "quantity": ing.quantity, "quality": ing.quality,
                    "purchase_price": ing.purchase_price.amount,
                }
                for ing in product.ingredients
            ])
            conn.execute(
                """INSERT OR REPLACE INTO products
                   (id, game_id, name, recipe_id, selling_price,
                    research_progress, awareness, ingredients_json)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    str(product.id), self._game_id, product.name,
                    str(product.recipe_id), product.selling_price.amount,
                    product.research_progress.value, product.awareness,
                    ingredients,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_product(self, product_id: UUID) -> Optional[Product]:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM products WHERE id=?", (str(product_id),)).fetchone()
            if not row:
                return None
            return self._row_to_product(row)
        finally:
            conn.close()

    def get_product_by_game(self, game_id: str) -> Optional[Product]:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM products WHERE game_id=? LIMIT 1", (game_id,)).fetchone()
            if not row:
                return None
            return self._row_to_product(row)
        finally:
            conn.close()

    def _row_to_product(self, row) -> Product:
        raw_ingredients = json.loads(row["ingredients_json"])
        ingredients = [
            Inventory(
                id=UUID(ing["id"]), name=ing["name"],
                quantity=ing["quantity"], quality=ing["quality"],
                purchase_price=Money(ing["purchase_price"]),
            )
            for ing in raw_ingredients
        ]
        return Product(
            id=UUID(row["id"]),
            name=row["name"],
            recipe_id=UUID(row["recipe_id"]),
            selling_price=Money(row["selling_price"]),
            research_progress=Progress(row["research_progress"]),
            ingredients=ingredients,
            awareness=row["awareness"],
        )

    # ── Research ──

    def save_research(self, research: Research) -> None:
        conn = self._get_conn()
        try:
            data = json.dumps({"id": str(research.id)})
            conn.execute(
                "INSERT OR REPLACE INTO research_data (id, game_id, data_json) VALUES (?,?,?)",
                (str(research.id), self._game_id, data),
            )
            conn.commit()
        finally:
            conn.close()

    def get_research(self, research_id: UUID) -> Optional[Research]:
        return None

    # ── Analysis ──

    def save_player_analysis(self, player_id: UUID, analysis: Dict[str, Any]) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO analysis_data (player_id, game_id, analysis_json) VALUES (?,?,?)",
                (str(player_id), self._game_id, json.dumps(analysis)),
            )
            conn.commit()
        finally:
            conn.close()

    def load_player_analysis(self, player_id: UUID) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT analysis_json FROM analysis_data WHERE player_id=?",
                (str(player_id),),
            ).fetchone()
            if not row:
                return None
            return json.loads(row["analysis_json"])
        finally:
            conn.close()

    def load_turn_analysis_history(self, player_id: UUID, limit: int) -> List[Dict[str, Any]]:
        return []

    # ── Game State (remaining_hours, ingredient_qty, freshness) ──

    def get_game_state(self, game_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM game_state WHERE game_id=?", (game_id,)).fetchone()
            if not row:
                return None
            return dict(row)
        finally:
            conn.close()

    def update_game_state(self, game_id: str, **kwargs):
        conn = self._get_conn()
        try:
            sets = ", ".join(f"{k}=?" for k in kwargs)
            vals = list(kwargs.values()) + [game_id]
            conn.execute(f"UPDATE game_state SET {sets} WHERE game_id=?", vals)
            conn.commit()
        finally:
            conn.close()

    # ── Queued Actions ──

    def queue_action(self, game_id: str, turn_number: int, slot_order: int,
                     action_type: str, specific_action: str, hours: int, cost: int = 0,
                     segment: str = "PREP"):
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO queued_actions
                   (game_id, turn_number, slot_order, action_type, specific_action, hours, cost, segment)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (game_id, turn_number, slot_order, action_type, specific_action, hours, cost, segment),
            )
            conn.commit()
        finally:
            conn.close()

    def get_queued_actions(self, game_id: str, turn_number: int, segment: str = None) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            if segment:
                rows = conn.execute(
                    "SELECT * FROM queued_actions WHERE game_id=? AND turn_number=? AND segment=? ORDER BY slot_order",
                    (game_id, turn_number, segment),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM queued_actions WHERE game_id=? AND turn_number=? ORDER BY slot_order",
                    (game_id, turn_number),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def remove_queued_action(self, game_id: str, turn_number: int, slot_order: int):
        conn = self._get_conn()
        try:
            conn.execute(
                "DELETE FROM queued_actions WHERE game_id=? AND turn_number=? AND slot_order=?",
                (game_id, turn_number, slot_order),
            )
            # Re-order remaining slots
            rows = conn.execute(
                "SELECT id FROM queued_actions WHERE game_id=? AND turn_number=? ORDER BY slot_order",
                (game_id, turn_number),
            ).fetchall()
            for i, row in enumerate(rows):
                conn.execute(
                    "UPDATE queued_actions SET slot_order=? WHERE id=?",
                    (i, row["id"]),
                )
            conn.commit()
        finally:
            conn.close()

    def clear_queued_actions(self, game_id: str, turn_number: int):
        conn = self._get_conn()
        try:
            conn.execute(
                "DELETE FROM queued_actions WHERE game_id=? AND turn_number=?",
                (game_id, turn_number),
            )
            conn.commit()
        finally:
            conn.close()

    def get_total_queued_hours(self, game_id: str, turn_number: int, segment: str = None) -> float:
        conn = self._get_conn()
        try:
            if segment:
                row = conn.execute(
                    "SELECT COALESCE(SUM(hours),0) as total FROM queued_actions WHERE game_id=? AND turn_number=? AND segment=?",
                    (game_id, turn_number, segment),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COALESCE(SUM(hours),0) as total FROM queued_actions WHERE game_id=? AND turn_number=?",
                    (game_id, turn_number),
                ).fetchone()
            return row["total"]
        finally:
            conn.close()

    def get_total_queued_cost(self, game_id: str, turn_number: int, segment: str = None) -> int:
        conn = self._get_conn()
        try:
            if segment:
                row = conn.execute(
                    "SELECT COALESCE(SUM(cost),0) as total FROM queued_actions WHERE game_id=? AND turn_number=? AND segment=?",
                    (game_id, turn_number, segment),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COALESCE(SUM(cost),0) as total FROM queued_actions WHERE game_id=? AND turn_number=?",
                    (game_id, turn_number),
                ).fetchone()
            return row["total"]
        finally:
            conn.close()

    # ── Phase Results ──

    def save_phase_result(self, game_id: str, turn_number: int, phase: str, result: Dict[str, Any]):
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO phase_results (game_id, turn_number, phase, result_json) VALUES (?,?,?,?)",
                (game_id, turn_number, phase, json.dumps(result)),
            )
            conn.commit()
        finally:
            conn.close()

    def get_phase_results(self, game_id: str, turn_number: int) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM phase_results WHERE game_id=? AND turn_number=? ORDER BY id",
                (game_id, turn_number),
            ).fetchall()
            return [
                {"phase": r["phase"], "result": json.loads(r["result_json"])}
                for r in rows
            ]
        finally:
            conn.close()

    def get_latest_phase_result(self, game_id: str, turn_number: int, phase: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT result_json FROM phase_results WHERE game_id=? AND turn_number=? AND phase=? ORDER BY id DESC LIMIT 1",
                (game_id, turn_number, phase),
            ).fetchone()
            if not row:
                return None
            return json.loads(row["result_json"])
        finally:
            conn.close()

    # ── Business Decisions ──

    def save_business_decision(self, game_id: str, turn_number: int, decision: Dict[str, Any]) -> int:
        conn = self._get_conn()
        try:
            cur = conn.execute(
                """INSERT INTO business_decisions
                   (game_id, turn_number, decision_key, title, description,
                    choice_a_label, choice_b_label, choice_a_effect, choice_b_effect, trigger_hour)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    game_id, turn_number,
                    decision["decision_key"], decision["title"], decision.get("description", ""),
                    decision["choice_a_label"], decision["choice_b_label"],
                    json.dumps(decision.get("choice_a_effect", {})),
                    json.dumps(decision.get("choice_b_effect", {})),
                    decision.get("trigger_hour", 0),
                ),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def get_business_decisions(self, game_id: str, turn_number: int) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM business_decisions WHERE game_id=? AND turn_number=? ORDER BY trigger_hour",
                (game_id, turn_number),
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["choice_a_effect"] = json.loads(d["choice_a_effect"])
                d["choice_b_effect"] = json.loads(d["choice_b_effect"])
                d["effect_json"] = json.loads(d["effect_json"])
                result.append(d)
            return result
        finally:
            conn.close()

    def update_business_decision(self, decision_id: int, choice: str, effect: Dict[str, Any]):
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE business_decisions SET player_choice=?, effect_json=? WHERE id=?",
                (choice, json.dumps(effect), decision_id),
            )
            conn.commit()
        finally:
            conn.close()

    def clear_business_decisions(self, game_id: str, turn_number: int):
        conn = self._get_conn()
        try:
            conn.execute(
                "DELETE FROM business_decisions WHERE game_id=? AND turn_number=?",
                (game_id, turn_number),
            )
            conn.commit()
        finally:
            conn.close()
