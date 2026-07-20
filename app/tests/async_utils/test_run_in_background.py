import threading

from app.async_utils import run_in_background


def test_runs_func_with_given_args_in_a_separate_thread(mocker):
    mocker.patch("app.async_utils.close_old_connections")
    caller_thread = threading.current_thread()
    # A list, not a plain variable: side_effect runs inside the background thread,
    # so it needs a shared mutable object to hand its result back to this thread.
    thread_func_ran_on = []
    func = mocker.Mock(
        side_effect=lambda *args, **kwargs: thread_func_ran_on.append(threading.current_thread())
    )

    background_thread = run_in_background(func, "arg", kwarg="value")
    background_thread.join(timeout=1)

    func.assert_called_once_with("arg", kwarg="value")
    assert thread_func_ran_on[0] is not caller_thread


def test_closes_connections_after_func_returns(mocker):
    close_old_connections = mocker.patch("app.async_utils.close_old_connections")
    func = mocker.Mock()

    thread = run_in_background(func)
    thread.join(timeout=1)

    close_old_connections.assert_called_once()


def test_closes_connections_even_when_func_raises(mocker):
    close_old_connections = mocker.patch("app.async_utils.close_old_connections")

    def _raise():
        raise ValueError("boom")

    thread = run_in_background(_raise)
    thread.join(timeout=1)

    close_old_connections.assert_called_once()
