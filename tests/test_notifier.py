from src.notifier import _format_message


def test_format_message_mixed_new_and_completed():
    """When both lists are non-empty, both sections appear in order."""
    result = _format_message(
        created_titles=["אלגוריתמים: שאלות הבנה – שבוע 4", "Software Project: HW 1"],
        completed_titles=["נוירוביולוגיה: תרגיל 3"],
    )
    expected = (
        "Moodle Tasks Sync:\n"
        "\n"
        "new assignments(2):\n"
        "אלגוריתמים: שאלות הבנה – שבוע 4\n"
        "Software Project: HW 1\n"
        "\n"
        "completed assignments(1):\n"
        "נוירוביולוגיה: תרגיל 3"
    )
    assert result == expected


def test_format_message_only_new_omits_completed_section():
    """When completed_titles is empty, the 'completed' section is not in the output."""
    result = _format_message(
        created_titles=["Software Project: HW 1"],
        completed_titles=[],
    )
    expected = (
        "Moodle Tasks Sync:\n"
        "\n"
        "new assignments(1):\n"
        "Software Project: HW 1"
    )
    assert result == expected
    # Sanity: 'completed' must not appear at all
    assert "completed" not in result
