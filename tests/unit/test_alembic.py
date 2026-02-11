"""Tests for Alembic migration setup and initial migration integrity."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestAlembicConfig:
    def test_alembic_ini_exists(self):
        assert (REPO_ROOT / "alembic.ini").is_file()

    def test_migrations_env_exists(self):
        assert (REPO_ROOT / "migrations" / "env.py").is_file()

    def test_script_mako_exists(self):
        assert (REPO_ROOT / "migrations" / "script.py.mako").is_file()

    def test_versions_dir_exists(self):
        assert (REPO_ROOT / "migrations" / "versions").is_dir()


class TestInitialMigration:
    def setup_method(self):
        migration_file = REPO_ROOT / "migrations" / "versions" / "001_initial_schema.py"
        assert migration_file.is_file(), "Initial migration not found"
        with open(migration_file) as f:
            self.source = f.read()
        self.tree = ast.parse(self.source)

    def test_has_revision_id(self):
        assert 'revision: str = "001_initial"' in self.source

    def test_has_no_down_revision(self):
        assert "down_revision" in self.source

    def test_upgrade_creates_all_10_tables(self):
        expected_tables = {
            "brands", "policies", "sources", "patterns", "ideas",
            "scripts", "assets", "posts", "metrics", "runs",
        }
        for table in expected_tables:
            assert f'"{table}"' in self.source, f"Table '{table}' not found in migration"

    def test_downgrade_drops_tables_in_reverse_order(self):
        # Find all drop_table calls
        drops = []
        for line in self.source.split("\n"):
            if "op.drop_table" in line:
                # Extract table name from op.drop_table("xxx")
                start = line.index('"') + 1
                end = line.index('"', start)
                drops.append(line[start:end])

        assert len(drops) == 10
        # brands should be last (other tables have FKs to it)
        assert drops[-1] == "brands"
        # runs and metrics should be early (leaf tables)
        assert drops.index("runs") < drops.index("brands")
        assert drops.index("metrics") < drops.index("posts")

    def test_has_foreign_keys(self):
        fk_patterns = [
            'ForeignKey("brands.id"',
            'ForeignKey("ideas.id"',
            'ForeignKey("scripts.id"',
            'ForeignKey("posts.id"',
            'ForeignKey("patterns.id"',
        ]
        for fk in fk_patterns:
            assert fk in self.source, f"FK {fk} not found"

    def test_has_indexes(self):
        assert self.source.count("op.create_index") >= 10

    def test_upgrade_function_exists(self):
        found = False
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name == "upgrade":
                found = True
        assert found

    def test_downgrade_function_exists(self):
        found = False
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name == "downgrade":
                found = True
        assert found


class TestMigrationsEnv:
    def test_env_imports_all_models(self):
        env_file = REPO_ROOT / "migrations" / "env.py"
        with open(env_file) as f:
            source = f.read()

        expected_imports = [
            "Asset", "Brand", "Idea", "Metrics", "Pattern",
            "Policy", "Post", "Run", "Script", "Source",
        ]
        for model in expected_imports:
            assert model in source, f"Model {model} not imported in env.py"

    def test_env_uses_async_engine(self):
        env_file = REPO_ROOT / "migrations" / "env.py"
        with open(env_file) as f:
            source = f.read()
        assert "async_engine_from_config" in source
        assert "run_async_migrations" in source

    def test_env_imports_base_metadata(self):
        env_file = REPO_ROOT / "migrations" / "env.py"
        with open(env_file) as f:
            source = f.read()
        assert "target_metadata = Base.metadata" in source
