# guards.py
from typing import Iterable, Optional, Set
from sqlglot import parse_one, expressions as exp

def force_safe_select(sql: str, limit: int = 1000, dialect: Optional[str] = None) -> str:
    tree = parse_one(sql, read=dialect)
    if not (isinstance(tree, exp.Select) or tree.find(exp.Select)):
        raise ValueError("Only SELECT statements are allowed")
    if not tree.find(exp.Limit):
        tree.set("limit", exp.Limit(this=exp.Literal.number(limit)))
    return tree.sql(dialect=dialect)

def extract_used_tables(sql: str, dialect: Optional[str] = None) -> Set[str]:
    tree = parse_one(sql, read=dialect)
    return {t.name for t in tree.find_all(exp.Table) if t and t.name}

def ensure_allowlisted_tables(sql: str, allowed: Iterable[str], dialect: Optional[str] = None) -> None:
    allowed = set(allowed)
    used = extract_used_tables(sql, dialect)
    bad = used - allowed
    if bad:
        raise ValueError(f"Tables not allowed: {', '.join(sorted(bad))}")

def sanitize_sql(sql: str, *, limit: int, dialect: Optional[str], allowlist: Iterable[str]) -> str:
    safe = force_safe_select(sql, limit=limit, dialect=dialect)
    ensure_allowlisted_tables(safe, allowlist, dialect=dialect)
    return safe
