def test_progress_bar_begins_at_zero(gui):
    assert gui.progressBar.value() == 0


def test_output_text_box_not_initially_displayed(gui):
    assert gui.groupBox.isChecked() == False
