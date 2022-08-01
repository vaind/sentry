import datetime
import typing

from sentry.utils import json


def assert_expected_response(
    response: typing.Dict[str, typing.Any], expected_response: typing.Dict[str, typing.Any]
) -> None:
    """Assert a received response matches what was expected."""
    # Compare the response structure and values to the expected response.
    for key, value in expected_response.items():
        assert key in response, key
        response_value = response.pop(key)
        assert response_value == value, f'"{response_value}" "{value}"'

    # Ensure no lingering unexpected keys exist.
    assert list(response.keys()) == []


def mock_expected_response(
    project_id: str,
    replay_id: str,
    started_at: datetime.datetime,
    finished_at: datetime.datetime,
    **kwargs: typing.Dict[str, typing.Any],
) -> typing.Dict[str, typing.Any]:
    urls = kwargs.pop("urls", [""])  # TODO: Update when url consumer is merged
    return {
        "replay_id": replay_id,
        "title": kwargs.pop("title", "Title"),
        "project_id": project_id,
        "urls": urls,
        "trace_ids": kwargs.pop("trace_ids", []),
        "started_at": datetime.datetime.strftime(started_at, "%Y-%m-%dT%H:%M:%S+00:00"),
        "finished_at": datetime.datetime.strftime(finished_at, "%Y-%m-%dT%H:%M:%S+00:00"),
        "duration": (finished_at - started_at).seconds,
        "count_errors": kwargs.pop("count_errors", 0),
        "count_segments": kwargs.pop("count_segments", 1),
        "count_urls": len(urls),
        "longest_transaction": kwargs.pop("longest_transaction", 0),
        "platform": kwargs.pop("platform", "javascript"),
        "environment": kwargs.pop("environment", "production"),
        "release": kwargs.pop("release", "version@1.3"),
        "dist": kwargs.pop("dist", "abc123"),
        "user": {
            "id": kwargs.pop("user_id", "123"),
            "email": kwargs.pop("user_email", "username@example.com"),
            "name": kwargs.pop("user_name", "username"),
            "ip_address": kwargs.pop("user_ip_address", "127.0.0.1"),
        },
        "sdk_name": kwargs.pop("sdk_name", "sentry.javascript.react"),
        "sdk_version": kwargs.pop("sdk_version", "6.18.1"),
        "tags": {"customtag": "is_set"},
    }


def mock_replay(
    timestamp: datetime.datetime,
    project_id: str,
    replay_id: str,
    **kwargs: typing.Dict[str, typing.Any],
) -> typing.Dict[str, typing.Any]:
    return {
        "type": "replay_event",
        "start_time": kwargs.pop("timestamp", int(timestamp.timestamp())),
        "replay_id": replay_id,
        "project_id": project_id,
        "retention_days": 30,
        "payload": list(
            bytes(
                json.dumps(
                    {
                        "type": "replay_event",
                        "replay_id": replay_id,
                        "segment_id": kwargs.pop("segment_id", 0),
                        "tags": {
                            "customtag": "is_set",
                            "transaction": kwargs.pop("title", "Title"),
                        },
                        "trace_ids": kwargs.pop("trace_ids", []),
                        "dist": kwargs.pop("dist", "abc123"),
                        "platform": kwargs.pop("platform", "javascript"),
                        "timestamp": kwargs.pop("timestamp", int(timestamp.timestamp())),
                        "environment": kwargs.pop("environment", "production"),
                        "release": kwargs.pop("release", "version@1.3"),
                        "user": {
                            "id": kwargs.pop("user_id", "123"),
                            "username": kwargs.pop("user_name", "username"),
                            "email": kwargs.pop("user_email", "username@example.com"),
                            "ip_address": kwargs.pop("ipv4", "127.0.0.1"),
                        },
                        "sdk": {
                            "name": kwargs.pop("sdk_name", "sentry.javascript.react"),
                            "version": kwargs.pop("sdk_version", "6.18.1"),
                        },
                        "contexts": {
                            "trace": {
                                "op": "pageload",
                                "span_id": "affa5649681a1eeb",
                                "trace_id": kwargs.pop(
                                    "trace_id", "23eda6cd4b174ef8a51f0096df3bfdd1"
                                ),
                            }
                        },
                        "request": {
                            "url": kwargs.pop("url", "http://localhost:3000/"),
                            "headers": {
                                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
                            },
                        },
                        "extra": {},
                    }
                ).encode()
            )
        ),
    }
