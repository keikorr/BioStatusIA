import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "biostatusia.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analises (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT    NOT NULL,
            imagem    TEXT    NOT NULL,
            categoria TEXT    NOT NULL,
            laudo     TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resultados_pipeline (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora     TEXT    NOT NULL,
            dataset_path  TEXT,
            n_imagens     INTEGER,
            pipeline_json TEXT,
            melhor_modelo TEXT,
            analise_id    INTEGER,
            FOREIGN KEY (analise_id) REFERENCES analises(id)
        )
    """)
    conn.commit()
    return conn


def salvar(imagem: str, categoria: str, laudo: str) -> int:
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO analises (data_hora, imagem, categoria, laudo) VALUES (?,?,?,?)",
        (datetime.now().isoformat(), imagem, categoria, laudo),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def listar() -> list[tuple]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, data_hora, imagem, categoria FROM analises ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return rows


def salvar_resultado(
    dataset_path: str,
    n_imagens: int,
    pipeline_data: dict,
    melhor_modelo: str,
    analise_id: int,
) -> int:
    conn = _get_conn()
    cur = conn.execute(
        """INSERT INTO resultados_pipeline
           (data_hora, dataset_path, n_imagens, pipeline_json, melhor_modelo, analise_id)
           VALUES (?,?,?,?,?,?)""",
        (
            datetime.now().isoformat(),
            dataset_path,
            n_imagens,
            json.dumps(pipeline_data),
            melhor_modelo,
            analise_id,
        ),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def buscar_resultado(resultado_id: int) -> dict | None:
    conn = _get_conn()
    row = conn.execute(
        """SELECT rp.id, rp.data_hora, rp.dataset_path, rp.n_imagens,
                  rp.pipeline_json, rp.melhor_modelo, rp.analise_id,
                  a.imagem, a.categoria, a.laudo
           FROM resultados_pipeline rp
           LEFT JOIN analises a ON a.id = rp.analise_id
           WHERE rp.id = ?""",
        (resultado_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "data_hora": row[1],
        "dataset_path": row[2],
        "n_imagens": row[3],
        "pipeline": json.loads(row[4]) if row[4] else {},
        "melhor_modelo": row[5],
        "analise_id": row[6],
        "imagem": row[7],
        "categoria": row[8],
        "laudo": row[9],
    }


def listar_resultados() -> list[tuple]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, data_hora, n_imagens, melhor_modelo FROM resultados_pipeline ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return rows
