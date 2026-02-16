from src.core.progress_tracker import ProgressTracker


def test_update_before_start_is_noop():
    tracker = ProgressTracker(total_files=1)

    tracker.update()

    assert tracker.success_count == 0
    assert tracker.failed_count == 0


def test_progress_context_updates_counts():
    tracker = ProgressTracker(total_files=2)

    with tracker as active:
        active.update(success=True)
        active.update(success=False)

    assert tracker.success_count == 1
    assert tracker.failed_count == 1


def test_stop_without_start_is_safe():
    tracker = ProgressTracker(total_files=1)

    tracker.stop()

    assert tracker.progress is None
