from app import rules


def test_engineering_gets_github_and_google():
    steps = rules.actions_for("employee.created", {"department": "Engineering"})
    assert [(s["app"], s["action"]) for s in steps] == [
        ("github", "add_to_team"),
        ("google", "create_account"),
    ]


def test_sales_gets_only_google():
    steps = rules.actions_for("employee.created", {"department": "Sales"})
    assert [s["app"] for s in steps] == ["google"]


def test_unknown_department_gets_nothing():
    assert rules.actions_for("employee.created", {"department": "Legal"}) == []


def test_unknown_event_gets_nothing():
    assert rules.actions_for("employee.exploded", {"department": "Engineering"}) == []


def test_employee_fields_derives_username_from_email():
    f = rules.employee_fields({"email": "asha@acme.com", "name": "Asha Rao"})
    assert f == {"user": "asha", "email": "asha@acme.com", "name": "Asha Rao"}
