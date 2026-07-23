# Test-1: Reject DROP TABLE

import pytest

from backend.app.sql_agent.db import (
    ReadOnlySQLDatabase,
    ReadOnlySQLQueryError,
)


def test_reject_drop_table(tmp_path):

    db = ReadOnlySQLDatabase(tmp_path / "dummy.db")

    with pytest.raises(ReadOnlySQLQueryError):
        db._validate_read_only_statement(
            "DROP TABLE users"
        )


#Test-2: Reject DELETE

def test_reject_delete(tmp_path):

    db = ReadOnlySQLDatabase(tmp_path / "dummy.db")

    with pytest.raises(ReadOnlySQLQueryError):
        db._validate_read_only_statement(
            "DELETE FROM users"
        )

# Test-3: Reject UPDATE

def test_reject_update(tmp_path):

    db = ReadOnlySQLDatabase(tmp_path / "dummy.db")

    with pytest.raises(ReadOnlySQLQueryError):
        db._validate_read_only_statement(
            "UPDATE users SET age = 20"
        )

#Test-4: Reject INSERT

def test_reject_insert(tmp_path):

    db = ReadOnlySQLDatabase(tmp_path / "dummy.db")

    with pytest.raises(ReadOnlySQLQueryError):
        db._validate_read_only_statement(
            "INSERT INTO users VALUES (1)"
        )

# Test-5: Reject Multiple Statements

def test_reject_multiple_statements(tmp_path):

    db = ReadOnlySQLDatabase(tmp_path / "dummy.db")

    with pytest.raises(ReadOnlySQLQueryError):
        db._reject_multiple_statements(
            "SELECT * FROM users; DROP TABLE users"
        )

# Test 6: Allow SELECT

def test_allow_select(tmp_path):

    db = ReadOnlySQLDatabase(tmp_path / "dummy.db")

    db._validate_read_only_statement(
        "SELECT * FROM users"
    )

# Test 7: Allow WITH

def test_allow_cte(tmp_path):

    db = ReadOnlySQLDatabase(tmp_path / "dummy.db")

    db._validate_read_only_statement(
        """
        WITH t AS (
            SELECT 1
        )
        SELECT * FROM t;
        """
    )
def test_allow_explain(tmp_path):

    db = ReadOnlySQLDatabase(tmp_path / "dummy.db")

    db._validate_read_only_statement(
        "EXPLAIN SELECT * FROM users"
    )

# Test 8: Reject Empty SQL

def test_empty_query(tmp_path):

    db = ReadOnlySQLDatabase(tmp_path / "dummy.db")

    with pytest.raises(ReadOnlySQLQueryError):
        db._validate_read_only_statement("")



def test_reject_begin_transaction(tmp_path):

    db = ReadOnlySQLDatabase(tmp_path / "dummy.db")

    with pytest.raises(ReadOnlySQLQueryError):
        db._validate_read_only_statement(
            "BEGIN TRANSACTION"
        )