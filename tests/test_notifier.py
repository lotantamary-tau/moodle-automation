from src.notifier import _format_message


def test_format_message_mixed_new_and_completed():
    """When both lists are non-empty, both sections appear in order, with combined footer."""
    result = _format_message(
        created_titles=["אלגוריתמים: שאלות הבנה – שבוע 4", "Software Project: HW 1"],
        completed_titles=["נוירוביולוגיה: תרגיל 3"],
    )
    expected = (
        "Moodle Tasks Sync:\n"
        "\n"
        "משימות חדשות(2):\n"
        "- אלגוריתמים: שאלות הבנה – שבוע 4\n"
        "- Software Project: HW 1\n"
        "\n"
        "משימות שבוצעו(1):\n"
        "- נוירוביולוגיה: תרגיל 3\n"
        "\n"
        "המשימות החדשות נוספו ל-Google Tasks, והמשימות שבוצעו סומנו כהושלמו."
    )
    assert result == expected


def test_format_message_only_new_omits_completed_section():
    """When completed_titles is empty, the 'completed' section and its footer are absent."""
    result = _format_message(
        created_titles=["Software Project: HW 1"],
        completed_titles=[],
    )
    expected = (
        "Moodle Tasks Sync:\n"
        "\n"
        "משימות חדשות(1):\n"
        "- Software Project: HW 1\n"
        "\n"
        "המשימות החדשות נוספו ל-Google Tasks."
    )
    assert result == expected
    # Sanity: the 'completed' section's Hebrew label must not appear at all
    assert "שבוצעו" not in result
