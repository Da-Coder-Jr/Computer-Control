import os
import sys
import json
from typing import Dict, List, Any


sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)


import pytest  # noqa: E402

from computer_control import client  # noqa: E402
from computer_control import controller  # noqa: E402


def test_functions_spec_matches_action_map():
    names_spec = {f["function"]["name"] for f in client.FUNCTIONS_SPEC}
    names_map = set(client.ACTION_MAP)
    assert names_spec == names_map


def test_execute_tool_calls_dry_run(capsys):
    calls = [
        {
            "function": {
                "name": "run_shell",
                "arguments": json.dumps({"command": "echo hello"}),
            }
        },
        {
            "function": {
                "name": "open_app",
                "arguments": json.dumps({"name": "calculator"}),
            }
        },
        {
            "function": {
                "name": "scroll",
                "arguments": json.dumps({"amount": 100}),
            }
        },
        {
            "function": {
                "name": "double_click",
                "arguments": json.dumps({"x": 10, "y": 10}),
            },
        },
        {
            "function": {
                "name": "drag_mouse",
                "arguments": json.dumps(
                    {"from_x": 0, "from_y": 0, "to_x": 1, "to_y": 1}
                ),
            },
        },
        {
            "function": {
                "name": "draw_path",
                "arguments": json.dumps(
                    {"points": [{"x": 0, "y": 0}, {"x": 1, "y": 1}]}
                ),
            },
        },
        {
            "function": {
                "name": "hotkey",
                "arguments": json.dumps({"keys": ["ctrl", "c"]}),
            },
        },
        {
            "function": {
                "name": "open_url",
                "arguments": json.dumps({"url": "https://example.com"}),
            },
        },
    ]
    client.execute_tool_calls(calls, dry_run=True, secure=False, delay=0)

    captured = capsys.readouterr()
    assert "DRY-RUN" in captured.out


def test_execute_tool_calls_secure(monkeypatch, capsys):
    calls = [
        {
            "function": {
                "name": "run_shell",
                "arguments": json.dumps({"command": "echo hello"}),
            }
        }
    ]
    monkeypatch.setattr("builtins.input", lambda *_: "n")
    client.execute_tool_calls(calls, dry_run=False, secure=True, delay=0)
    captured = capsys.readouterr()
    assert "Skipped run_shell" in captured.out


def test_execute_tool_calls_delay(monkeypatch):
    call = {
        "function": {
            "name": "run_shell",
            "arguments": json.dumps({"command": "echo hi"}),
        }
    }
    sleeps: List[float] = []
    monkeypatch.setattr(client.time, "sleep", lambda d: sleeps.append(d))
    monkeypatch.setattr(client.controller, "run_shell", lambda **_: None)
    client.execute_tool_calls([call], dry_run=False, secure=False, delay=0.5)
    assert sleeps == [0.5]


def test_help_runs(tmp_path):
    """computer_control.py --help should exit cleanly."""
    from subprocess import run

    result = run(
        [sys.executable, "computer_control.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()


def test_open_app_failure(monkeypatch):
    def fake_startfile(_):
        raise FileNotFoundError("missing")

    def fake_which(_):
        return None

    monkeypatch.setattr("os.startfile", fake_startfile, raising=False)
    monkeypatch.setattr("shutil.which", fake_which)
    with pytest.raises(RuntimeError):
        from computer_control import controller

        controller.open_app("missing_app")


def test_open_app_linux(monkeypatch):
    from computer_control import controller

    called = {}

    monkeypatch.setattr(
        controller, "os", type("DummyOS", (), {"name": "posix"})
    )  # noqa: E501

    def fake_which(name):
        called["which"] = name
        return "/usr/bin/" + name

    def fake_popen(cmd):
        called["cmd"] = cmd

        class Dummy:
            pass

        return Dummy()

    monkeypatch.setattr("shutil.which", fake_which)
    monkeypatch.setattr(controller.subprocess, "Popen", fake_popen)
    controller.open_app("vim")
    assert called["which"] == "vim"
    assert called["cmd"] == ["vim"]


def test_capture_screen_error(monkeypatch):
    from computer_control import controller

    def bad_screenshot():
        raise OSError("scrot missing")

    monkeypatch.setattr(
        controller,
        "pyautogui",
        type("Dummy", (), {"screenshot": staticmethod(bad_screenshot)}),
    )

    url = controller.capture_screen()
    assert url.startswith("data:image/png;base64,")


def test_capture_screen_jpeg(monkeypatch):
    from computer_control import controller
    from PIL import Image

    def good_screenshot():
        return Image.new("RGB", (10, 10), "red")

    monkeypatch.setattr(
        controller,
        "pyautogui",
        type("Dummy", (), {"screenshot": staticmethod(good_screenshot)}),
    )

    url = controller.capture_screen()
    assert url.startswith("data:image/jpeg;base64,")


def test_capture_screen_fallback(monkeypatch):
    from computer_control import controller
    from PIL import Image

    def bad_screenshot():
        raise OSError("fail")

    def grab():
        return Image.new("RGB", (5, 5), "blue")

    monkeypatch.setattr(
        controller,
        "pyautogui",
        type("Dummy", (), {"screenshot": staticmethod(bad_screenshot)}),
    )
    monkeypatch.setattr(
        controller,
        "ImageGrab",
        type("Dummy", (), {"grab": staticmethod(grab)}),
    )

    url = controller.capture_screen()
    assert url.startswith("data:image/jpeg;base64,")


def test_capture_screen_unidentified(monkeypatch):
    from computer_control import controller
    from PIL import UnidentifiedImageError

    def bad_screenshot():
        raise UnidentifiedImageError("bad")

    def grab():
        raise OSError("fail")

    monkeypatch.setattr(
        controller,
        "pyautogui",
        type("Dummy", (), {"screenshot": staticmethod(bad_screenshot)}),
    )
    monkeypatch.setattr(
        controller,
        "ImageGrab",
        type("Dummy", (), {"grab": staticmethod(grab)}),
    )

    url = controller.capture_screen()
    assert url.startswith("data:image/png;base64,")


def test_query_pollinations_payload(monkeypatch):
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=60):
        captured["url"] = url
        captured["json"] = json

        class Response:

            ok = True

            def raise_for_status(self):
                pass

            def json(self):
                return {"choices": []}

        return Response()

    monkeypatch.setattr(client.requests, "post", fake_post)
    messages: List[Dict[str, str]] = [{"role": "user", "content": "hello"}]
    client.query_pollinations(messages)

    assert captured["json"]["model"] == "openai"
    assert captured["json"]["messages"] == messages
    assert captured["json"]["tools"] == client.FUNCTIONS_SPEC


def test_query_pollinations_network_error(monkeypatch):
    def fake_post(*_, **__):
        raise client.requests.RequestException("boom")

    monkeypatch.setattr(client.requests, "post", fake_post)
    monkeypatch.setattr(client.time, "sleep", lambda *_: None)  # noqa: E501
    messages = [{"role": "user", "content": "hi"}]
    with pytest.raises(RuntimeError):
        client.query_pollinations(messages, retries=2)


def test_query_pollinations_http_error(monkeypatch):
    class Resp:
        status_code = 400
        ok = False
        text = "bad"

        def raise_for_status(self):
            raise client.requests.HTTPError("bad request")

    def fake_post(*_, **__):
        return Resp()

    monkeypatch.setattr(client.requests, "post", fake_post)
    monkeypatch.setattr(client.time, "sleep", lambda *_: None)  # noqa: E501
    with pytest.raises(RuntimeError):
        client.query_pollinations(
            [{"role": "user", "content": "hi"}], retries=2
        )  # noqa: E501


def test_main_uses_blank_image(monkeypatch):
    from computer_control import main as cc_main

    def fake_capture():
        raise controller.GUIUnavailable("no gui")

    def fake_query(messages: List[Dict[str, Any]]):
        nonlocal payload
        payload = messages[1]["content"][1]["image_url"]["url"]
        return {"choices": [{}]}

    payload = ""
    monkeypatch.setattr(controller, "capture_screen", fake_capture)
    monkeypatch.setattr(client, "execute_tool_calls", lambda *_, **__: None)
    monkeypatch.setattr(client, "query_pollinations", fake_query)
    cc_main("hello", steps=1, dry_run=True)
    assert payload.startswith("data:image/png;base64,")


def test_main_uses_blank_image_no_dry_run(monkeypatch):
    from computer_control import main as cc_main

    def fake_capture():
        raise controller.GUIUnavailable("no gui")

    def fake_query(messages: List[Dict[str, Any]]):
        nonlocal payload
        payload = messages[1]["content"][1]["image_url"]["url"]
        return {"choices": [{}]}

    payload = ""
    monkeypatch.setattr(controller, "capture_screen", fake_capture)
    monkeypatch.setattr(client, "execute_tool_calls", lambda *_, **__: None)
    monkeypatch.setattr(client, "query_pollinations", fake_query)
    cc_main("hello", steps=1)
    assert payload.startswith("data:image/png;base64,")


def test_create_file(tmp_path):
    path = tmp_path / "sub" / "note.txt"
    controller.create_file(str(path), "hello")
    assert path.read_text() == "hello"


def test_copy_and_delete_file(tmp_path):
    src = tmp_path / "a.txt"
    dst = tmp_path / "b.txt"
    src.write_text("hi")
    controller.copy_file(str(src), str(dst))
    assert dst.read_text() == "hi"
    controller.delete_file(str(src))
    assert not src.exists()


def test_move_file(tmp_path):
    src = tmp_path / "a.txt"
    dst = tmp_path / "c.txt"
    src.write_text("hi")
    controller.move_file(str(src), str(dst))
    assert dst.read_text() == "hi"
    assert not src.exists()


def test_open_url(monkeypatch):
    called = {}

    def fake_open(url):
        called["url"] = url

    monkeypatch.setattr(controller.webbrowser, "open", fake_open)
    controller.open_url("https://example.com")
    assert called["url"] == "https://example.com"


def test_analysis_functions_removed():
    assert "read_file" not in client.ACTION_MAP
    assert "list_python_files" not in client.ACTION_MAP
    assert "search_code" not in client.ACTION_MAP
    assert "summarize_codebase" not in client.ACTION_MAP


def test_execute_tool_calls_returns_messages():
    call = {
        "id": "abc",
        "function": {
            "name": "run_shell",
            "arguments": json.dumps({"command": "echo hi"}),
        },
    }
    msgs = client.execute_tool_calls([call], dry_run=True, delay=0)
    assert msgs[0]["role"] == "tool"
    assert msgs[0]["tool_call_id"] == "abc"
    assert msgs[0]["name"] == "run_shell"


def test_main_unlimited(monkeypatch):
    from computer_control import main as cc_main

    responses = [
        {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "1",
                                "function": {
                                    "name": "run_shell",
                                    "arguments": "{}",
                                },  # noqa: E501
                            }
                        ]
                    }
                }
            ]
        },
        {"choices": [{"message": {"content": "done", "done": True}}]},
    ]
    idx = {"i": 0}

    def fake_query(_):
        res = responses[idx["i"]]
        idx["i"] += 1
        return res

    monkeypatch.setattr(client, "query_pollinations", fake_query)
    monkeypatch.setattr(
        client,
        "execute_tool_calls",
        lambda *_, **__: [
            {"role": "tool", "tool_call_id": "1", "content": "ok"}
        ],  # noqa: E501
    )
    monkeypatch.setattr(
        controller, "capture_screen", lambda: "data:image/png;base64,abc"
    )
    cc_main("hi", max_steps=0, dry_run=True)
    assert idx["i"] == 2


def test_trim_history_avoids_partial_pairs():
    from computer_control import trim_history  # noqa: E402

    # Build a message sequence with two tool call loops
    msgs = [
        {"role": "system", "content": "hi"},
        {"role": "user", "content": "goal"},
        {"role": "assistant", "tool_calls": [{"id": "1"}]},
        {"role": "tool", "tool_call_id": "1", "content": "ok"},
        {"role": "user", "content": "s1"},
        {"role": "assistant", "tool_calls": [{"id": "2"}]},
        {"role": "tool", "tool_call_id": "2", "content": "ok"},
        {"role": "user", "content": "s2"},
    ]

    trimmed = trim_history(msgs, 3)
    assert trimmed[0]["role"] in ("system", "user")
    assert len(trimmed) <= 3
    pending = []
    for m in trimmed:
        if m.get("tool_calls"):
            pending.extend(c["id"] for c in m["tool_calls"])
        if m.get("tool_call_id") and m["tool_call_id"] in pending:
            pending.remove(m["tool_call_id"])
    assert not pending


def test_trim_history_drops_trailing_tool_call():
    from computer_control import trim_history  # noqa: E402

    msgs = [
        {"role": "system", "content": "hi"},
        {"role": "user", "content": "goal"},
        {"role": "assistant", "tool_calls": [{"id": "1"}]},
        {"role": "tool", "tool_call_id": "1", "content": "ok"},
        {"role": "user", "content": "s1"},
        {"role": "assistant", "tool_calls": [{"id": "2"}]},
    ]

    trimmed = trim_history(msgs, 5)
    assert trimmed[-1]["role"] == "user"


def test_trim_history_removes_incomplete_pairs():
    from computer_control import trim_history  # noqa: E402

    msgs = [
        {"role": "system", "content": "hi"},
        {"role": "user", "content": "goal"},
        {"role": "assistant", "tool_calls": [{"id": "1"}, {"id": "2"}]},
        {"role": "tool", "tool_call_id": "1", "content": "ok"},
        {"role": "user", "content": "next"},
    ]

    trimmed = trim_history(msgs, 4)
    assert all(m.get("tool_call_id") != "1" for m in trimmed)
    assert not any("tool_calls" in m for m in trimmed)


def test_trim_history_strips_leading_tool_messages():
    from computer_control import trim_history  # noqa: E402

    msgs = [
        {"role": "system", "content": "hi"},
        {"role": "user", "content": "goal"},
        {"role": "assistant", "tool_calls": [{"id": "1"}, {"id": "2"}]},
        {"role": "tool", "tool_call_id": "1", "content": "ok"},
        {"role": "user", "content": "screen"},
    ]

    trimmed = trim_history(msgs, 4)
    assert trimmed == [{"role": "user", "content": "screen"}]


def test_trim_history_enforces_limit():
    from computer_control import trim_history  # noqa: E402

    msgs: List[Dict[str, Any]] = [{"role": "system", "content": "hi"}]
    for i in range(4):
        msgs.append({"role": "user", "content": f"u{i}"})
        msgs.append({"role": "assistant", "tool_calls": [{"id": str(i)}]})
        msgs.append({"role": "tool", "tool_call_id": str(i), "content": "ok"})

    trimmed = trim_history(msgs, 5)
    assert len(trimmed) <= 5
    assert trimmed[0]["role"] in ("system", "user")
    assert not trimmed[-1].get("tool_calls")
    pending = []
    for m in trimmed:
        if m.get("tool_calls"):
            pending.extend(c["id"] for c in m["tool_calls"])
        if m.get("tool_call_id") and m["tool_call_id"] in pending:
            pending.remove(m["tool_call_id"])
    assert not pending


def test_trim_history_keeps_complete_pairs(monkeypatch):
    from computer_control import trim_history  # noqa: E402

    msgs = [
        {"role": "system", "content": "hi"},
        {"role": "user", "content": "goal"},
        {"role": "assistant", "tool_calls": [{"id": "1"}]},
        {"role": "tool", "tool_call_id": "1", "content": "ok"},
        {"role": "user", "content": "next"},
        {"role": "assistant", "tool_calls": [{"id": "2"}]},
    ]

    trimmed = trim_history(msgs, 6)
    assert trimmed == msgs[:5]


def test_trim_history_multi_tool_call_partial():
    from computer_control import trim_history  # noqa: E402

    msgs = [
        {"role": "system", "content": "hi"},
        {"role": "user", "content": "goal"},
        {
            "role": "assistant",
            "tool_calls": [
                {"id": "1"},
                {"id": "2"},
                {"id": "3"},
            ],
        },
        {"role": "tool", "tool_call_id": "1", "content": "ok"},
        {"role": "tool", "tool_call_id": "2", "content": "ok"},
        {"role": "tool", "tool_call_id": "3", "content": "ok"},
        {"role": "user", "content": "next"},
    ]

    trimmed = trim_history(msgs, 5)
    assert trimmed == [{"role": "user", "content": "next"}]


def test_main_save_dir(monkeypatch, tmp_path):
    from computer_control import main as cc_main
    from computer_control import controller, client
    import base64

    def fake_capture():
        return "data:image/jpeg;base64," + base64.b64encode(b"abc").decode()

    def fake_query(_):
        return {"choices": [{"message": {"content": "done", "done": True}}]}

    monkeypatch.setattr(controller, "capture_screen", fake_capture)
    monkeypatch.setattr(client, "execute_tool_calls", lambda *_, **__: [])
    monkeypatch.setattr(client, "query_pollinations", fake_query)

    cc_main("goal", steps=1, dry_run=True, save_dir=str(tmp_path))
    assert (tmp_path / "0.jpg").exists()
    assert (tmp_path / "final.jpg").exists()


def test_query_pollinations_413(monkeypatch):
    class Resp:
        status_code = 413
        ok = False
        text = "too big"

    def fake_post(*_, **__):
        return Resp()

    monkeypatch.setattr(client.requests, "post", fake_post)
    with pytest.raises(RuntimeError):
        client.query_pollinations([{"role": "user", "content": "hi"}])


def test_main_retries_on_413(monkeypatch):
    from computer_control import main as cc_main

    calls = {"count": 0}

    def fake_query(_):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError(
                "Pollinations API returned 413: request entity too large"
            )
        return {"choices": [{"message": {"done": True}}]}

    monkeypatch.setattr(client, "query_pollinations", fake_query)
    monkeypatch.setattr(client, "execute_tool_calls", lambda *_, **__: [])
    monkeypatch.setattr(
        controller, "capture_screen", lambda: "data:image/png;base64,abc"
    )

    cc_main("goal", steps=1, dry_run=True, history=4)
    assert calls["count"] == 2


def test_validate_history_ok():
    from computer_control.main import validate_history

    msgs = [
        {"role": "system", "content": "hi"},
        {"role": "assistant", "tool_calls": [{"id": "1"}]},
        {"role": "tool", "tool_call_id": "1", "content": "ok"},
    ]

    validate_history(msgs)


def test_validate_history_error():
    from computer_control.main import validate_history

    msgs = [
        {"role": "assistant", "tool_calls": [{"id": "1"}]},
        {"role": "user", "content": "next"},
    ]

    with pytest.raises(ValueError):
        validate_history(msgs)
