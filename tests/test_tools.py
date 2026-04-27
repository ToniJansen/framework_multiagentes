from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch


# -- file_ops ------------------------------------------------------------------


class TestReadFile:
    def test_read_existing(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_text("world")
        import agentkit.tools.file_ops as fo
        import agentkit.guardrails.policies as pol

        orig = pol.WORKSPACE_ROOT
        pol.WORKSPACE_ROOT = tmp_path
        importlib.reload(fo)
        result = fo.read_file.invoke({"path": str(f)})
        pol.WORKSPACE_ROOT = orig
        assert "world" in result

    def test_read_outside_blocked(self, tmp_path):
        import agentkit.tools.file_ops as fo
        import agentkit.guardrails.policies as pol

        orig = pol.WORKSPACE_ROOT
        pol.WORKSPACE_ROOT = tmp_path
        importlib.reload(fo)
        result = fo.read_file.invoke({"path": "/etc/passwd"})
        pol.WORKSPACE_ROOT = orig
        assert "error" in result.lower() or "policy" in result.lower()


class TestWriteFile:
    def test_write_inside_out(self, tmp_path):
        import agentkit.tools.file_ops as fo
        import agentkit.guardrails.policies as pol

        orig = pol.ALLOWED_WRITE_DIR
        pol.ALLOWED_WRITE_DIR = tmp_path
        importlib.reload(fo)
        dest = tmp_path / "diff.patch"
        result = fo.write_file.invoke({"path": str(dest), "content": "--- a\n+++ b\n"})
        pol.ALLOWED_WRITE_DIR = orig
        assert "Written" in result

    def test_write_outside_blocked(self, tmp_path):
        import agentkit.tools.file_ops as fo
        import agentkit.guardrails.policies as pol

        orig = pol.ALLOWED_WRITE_DIR
        pol.ALLOWED_WRITE_DIR = tmp_path / "out"
        importlib.reload(fo)
        result = fo.write_file.invoke({"path": "/tmp/evil.sh", "content": "rm -rf /"})
        pol.ALLOWED_WRITE_DIR = orig
        assert "error" in result.lower() or "policy" in result.lower()


# -- sql_safe ------------------------------------------------------------------


class TestRunSql:
    def _mock_conn(self, rows: list, columns: list[str]) -> MagicMock:
        cursor = MagicMock()
        cursor.__enter__ = lambda s: s
        cursor.__exit__ = MagicMock(return_value=False)
        cursor.fetchall.return_value = rows
        desc = []
        for col in columns:
            col_desc = MagicMock()
            col_desc.__getitem__ = MagicMock(return_value=col)
            desc.append(col_desc)
        cursor.description = desc
        conn = MagicMock()
        conn.__enter__ = lambda s: s
        conn.__exit__ = MagicMock(return_value=False)
        conn.cursor.return_value = cursor
        return conn

    def test_valid_select(self):
        from agentkit.tools.sql_safe import run_sql

        conn = self._mock_conn([("Blocos", 129.90)], ["name", "price"])
        with patch("agentkit.tools.sql_safe._get_conn", return_value=conn):
            result = run_sql.invoke({"query": "SELECT name, price FROM products LIMIT 5"})
        assert "name" in result
        assert "price" in result

    def test_delete_blocked(self):
        from agentkit.tools.sql_safe import run_sql

        result = run_sql.invoke({"query": "DELETE FROM products WHERE id = 1"})
        assert "policy" in result.lower() or "error" in result.lower()

    def test_no_limit_blocked(self):
        from agentkit.tools.sql_safe import run_sql

        result = run_sql.invoke({"query": "SELECT * FROM products"})
        assert "policy" in result.lower() or "limit" in result.lower()

    def test_empty_result(self):
        from agentkit.tools.sql_safe import run_sql

        conn = self._mock_conn([], ["id"])
        with patch("agentkit.tools.sql_safe._get_conn", return_value=conn):
            result = run_sql.invoke({"query": "SELECT id FROM products LIMIT 1"})
        assert "no rows" in result
