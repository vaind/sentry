from unittest import mock

from sentry.api.serializers import SimpleEventSerializer, serialize
from sentry.api.serializers.models.event import DetailedEventSerializer, SharedEventSerializer
from sentry.models import EventError
from sentry.sdk_updates import SdkIndexState
from sentry.testutils import TestCase
from sentry.testutils.helpers.datetime import before_now, iso_format
from sentry.testutils.silo import customer_silo_test
from sentry.utils.samples import load_data


@customer_silo_test
class EventSerializerTest(TestCase):
    def test_simple(self):
        event_id = "a" * 32
        event = self.store_event(
            data={"event_id": event_id, "timestamp": iso_format(before_now(minutes=1))},
            project_id=self.project.id,
        )
        result = serialize(event)
        assert result["id"] == event_id
        assert result["eventID"] == event_id

    def test_eventerror(self):
        event = self.store_event(
            data={
                "event_id": "a" * 32,
                "timestamp": iso_format(before_now(minutes=1)),
                "stacktrace": ["ü"],
            },
            project_id=self.project.id,
            assert_no_errors=False,
        )

        result = serialize(event)
        assert len(result["errors"]) == 1
        assert "data" in result["errors"][0]
        assert result["errors"][0]["type"] == EventError.INVALID_DATA
        assert result["errors"][0]["data"] == {
            "name": "stacktrace",
            "reason": "expected rawstacktrace",
            "value": ["\xfc"],
        }
        assert "startTimestamp" not in result
        assert "timestamp" not in result

    def test_hidden_eventerror(self):
        event = self.store_event(
            data={
                "event_id": "a" * 32,
                "timestamp": iso_format(before_now(minutes=1)),
                "breadcrumbs": ["ü"],
            },
            project_id=self.project.id,
            assert_no_errors=False,
        )

        result = serialize(event)
        assert result["errors"] == []

    def test_renamed_attributes(self):
        # Only includes meta for simple top-level attributes
        event = self.store_event(
            data={
                "event_id": "a" * 32,
                "timestamp": iso_format(before_now(minutes=1)),
                "extra": {"extra": True},
                "modules": {"modules": "foobar"},
                "_meta": {
                    "extra": {"": {"err": ["extra error"]}},
                    "modules": {"": {"err": ["modules error"]}},
                },
            },
            project_id=self.project.id,
            assert_no_errors=False,
        )

        result = serialize(event)
        assert result["context"] == {"extra": True}
        assert result["_meta"]["context"] == {"": {"err": ["extra error"]}}
        assert result["packages"] == {"modules": "foobar"}
        assert result["_meta"]["packages"] == {"": {"err": ["modules error"]}}

    def test_message_interface(self):
        event = self.store_event(
            data={
                "event_id": "a" * 32,
                "timestamp": iso_format(before_now(minutes=1)),
                "logentry": {"formatted": "bar"},
                "_meta": {"logentry": {"formatted": {"": {"err": ["some error"]}}}},
            },
            project_id=self.project.id,
            assert_no_errors=False,
        )

        result = serialize(event)
        assert result["message"] == "bar"
        assert result["_meta"]["message"] == {"": {"err": ["some error"]}}

    def test_message_formatted(self):
        event = self.store_event(
            data={
                "event_id": "a" * 32,
                "timestamp": iso_format(before_now(minutes=1)),
                "logentry": {"formatted": "baz"},
                "_meta": {"logentry": {"formatted": {"": {"err": ["some error"]}}}},
            },
            project_id=self.project.id,
            assert_no_errors=False,
        )

        result = serialize(event)
        assert result["message"] == "baz"
        assert result["_meta"]["message"] == {"": {"err": ["some error"]}}

    def test_tags_tuples(self):
        event = self.store_event(
            data={
                "event_id": "a" * 32,
                "level": "error",  # creates a derived tag.
                "timestamp": iso_format(before_now(minutes=1)),
                "tags": [["foo", "foo"], ["bar", "bar"], ["last", "tag"], None],
                "_meta": {
                    "tags": {
                        "0": {"1": {"": {"err": ["foo error"]}}},
                        "1": {"0": {"": {"err": ["bar error"]}}},
                        "3": {"": {"err": ["full error"]}},
                    }
                },
            },
            project_id=self.project.id,
            assert_no_errors=False,
        )

        result = serialize(event)
        # Expect 3 custom tags + derived "level". The ``None``` entry is removed
        # by the serializer as it cannot be rendered. Such entries are generated
        # by Relay normalization.
        assert len(result["tags"]) == 4
        assert result["tags"][0]["value"] == "bar"
        assert result["tags"][1]["value"] == "foo"
        assert result["_meta"]["tags"]["0"]["key"] == {"": {"err": ["bar error"]}}
        assert result["_meta"]["tags"]["1"]["value"] == {"": {"err": ["foo error"]}}
        assert result["_meta"]["tags"].get("2") is None

    def test_tags_dict(self):
        event = self.store_event(
            data={
                "event_id": "a" * 32,
                "timestamp": iso_format(before_now(minutes=1)),
                "tags": {"foo": "foo", "bar": "bar", "last": "tag"},
                "_meta": {
                    "tags": {
                        "foo": {"": {"err": ["foo error"]}},
                        "bar": {"": {"err": ["bar error"]}},
                    }
                },
            },
            project_id=self.project.id,
            assert_no_errors=False,
        )

        result = serialize(event)
        assert result["tags"][0]["value"] == "bar"
        assert result["tags"][1]["value"] == "foo"
        assert result["_meta"]["tags"]["0"]["value"] == {"": {"err": ["bar error"]}}
        assert result["_meta"]["tags"]["1"]["value"] == {"": {"err": ["foo error"]}}
        assert result["_meta"]["tags"].get("2") is None

    def test_none_interfaces(self):
        event = self.store_event(
            data={
                "event_id": "a" * 32,
                "timestamp": iso_format(before_now(minutes=1)),
                "breadcrumbs": None,
                "exception": None,
                "logentry": None,
                "request": None,
                "user": None,
                "contexts": None,
                "sdk": None,
                "_meta": None,
            },
            project_id=self.project.id,
        )

        result = serialize(event)
        assert not any(e["type"] == "breadcrumbs" for e in result["entries"])
        assert not any(e["type"] == "exception" for e in result["entries"])
        assert not any(e["type"] == "message" for e in result["entries"])
        assert not any(e["type"] == "request" for e in result["entries"])
        assert result["user"] is None
        assert result["sdk"] is None
        assert result["contexts"] == {}
        assert "startTimestamp" not in result

    def test_transaction_event(self):
        event_data = load_data("transaction")
        event = self.store_event(data=event_data, project_id=self.project.id)
        result = serialize(event)
        assert isinstance(result["endTimestamp"], float)
        assert result["endTimestamp"] == event.data.get("timestamp")
        assert isinstance(result["startTimestamp"], float)
        assert result["startTimestamp"] == event.data.get("start_timestamp")
        assert "dateCreated" not in result
        assert "crashFile" not in result
        assert "fingerprints" not in result
        assert "measurements" in result
        assert result["measurements"] == event_data["measurements"]
        assert "breakdowns" in result
        assert result["breakdowns"] == event_data["breakdowns"]

    def test_transaction_event_empty_spans(self):
        event_data = load_data("transaction")
        event_data["spans"] = []
        event = self.store_event(data=event_data, project_id=self.project.id)
        result = serialize(event)
        assert result["entries"][0]["type"] == "spans"


@customer_silo_test
class SharedEventSerializerTest(TestCase):
    def test_simple(self):
        event = self.store_event(
            data={"event_id": "a" * 32, "timestamp": iso_format(before_now(minutes=1))},
            project_id=self.project.id,
        )

        result = serialize(event, None, SharedEventSerializer())
        assert result["id"] == "a" * 32
        assert result["eventID"] == "a" * 32
        assert result.get("context") is None
        assert result.get("contexts") is None
        assert result.get("user") is None
        assert result.get("tags") is None
        assert "sdk" not in result
        assert "errors" not in result
        for entry in result["entries"]:
            assert entry["type"] != "breadcrumbs"


@customer_silo_test
class SimpleEventSerializerTest(TestCase):
    def test_user(self):
        """
        Use the SimpleEventSerializer to serialize an event
        """
        event = self.store_event(
            data={
                "event_id": "a" * 32,
                "timestamp": iso_format(before_now(minutes=1)),
                "user": {"email": "test@test.com"},
            },
            project_id=self.project.id,
        )
        result = serialize(event, None, SimpleEventSerializer())

        assert result["eventID"] == event.event_id
        assert result["projectID"] == str(event.project_id)
        assert result["groupID"] == str(event.group.id)
        assert result["message"] == event.message
        assert result["title"] == event.title
        assert result["location"] == event.location
        assert result["culprit"] == event.culprit
        assert result["dateCreated"] == event.datetime
        assert result["user"]["id"] == event.get_minimal_user().id
        assert result["user"]["email"] == event.get_minimal_user().email
        assert result["user"]["username"] == event.get_minimal_user().username
        assert result["user"]["ip_address"] == event.get_minimal_user().ip_address
        assert result["tags"] == [
            {"key": "level", "value": "error"},
            {"key": "user", "value": "email:test@test.com", "query": 'user.email:"test@test.com"'},
        ]

    def test_no_group(self):
        """
        Use the SimpleEventSerializer to serialize an event without group
        """
        event = self.store_event(
            data={
                "event_id": "a" * 32,
                "start_timestamp": iso_format(before_now(minutes=1)),
                "timestamp": iso_format(before_now(minutes=1)),
                "user": {"email": "test@test.com"},
                "type": "transaction",
                "transaction": "api.issue.delete",
                "spans": [],
                "contexts": {"trace": {"op": "foobar", "trace_id": "a" * 32, "span_id": "a" * 16}},
            },
            project_id=self.project.id,
        )

        result = serialize(event, None, SimpleEventSerializer())
        assert result["groupID"] is None


@customer_silo_test
class EventSerializerSdkUpdatesTest(TestCase):
    @mock.patch(
        "sentry.sdk_updates.SdkIndexState",
        return_value=SdkIndexState(sdk_versions={"example.sdk": "2.0.0"}),
    )
    def test_update_on_major(self, mock_index_state):
        min_ago = iso_format(before_now(minutes=1))
        event = self.store_event(
            data={
                "event_id": "a" * 32,
                "message": "oh no",
                "timestamp": min_ago,
                "fingerprint": ["group-1"],
                "sdk": {"name": "example.sdk", "version": "1.0.0"},
            },
            project_id=self.project.id,
            assert_no_errors=False,
        )

        result = serialize(event, None, DetailedEventSerializer())
        assert result["sdkUpdates"] == [
            {
                "enables": [],
                "newSdkVersion": "2.0.0",
                "sdkName": "example.sdk",
                "sdkUrl": None,
                "type": "updateSdk",
            }
        ]

    @mock.patch(
        "sentry.sdk_updates.SdkIndexState",
        return_value=SdkIndexState(sdk_versions={"example.sdk": "1.1.0"}),
    )
    def test_update_on_minor(self, mock_index_state):
        min_ago = iso_format(before_now(minutes=1))
        event = self.store_event(
            data={
                "event_id": "a" * 32,
                "message": "oh no",
                "timestamp": min_ago,
                "fingerprint": ["group-1"],
                "sdk": {"name": "example.sdk", "version": "1.0.0"},
            },
            project_id=self.project.id,
            assert_no_errors=False,
        )

        result = serialize(event, None, DetailedEventSerializer())
        assert result["sdkUpdates"] == [
            {
                "enables": [],
                "newSdkVersion": "1.1.0",
                "sdkName": "example.sdk",
                "sdkUrl": None,
                "type": "updateSdk",
            }
        ]

    @mock.patch(
        "sentry.sdk_updates.SdkIndexState",
        return_value=SdkIndexState(sdk_versions={"example.sdk": "1.0.1"}),
    )
    def test_ignores_patch(self, mock_index_state):
        min_ago = iso_format(before_now(minutes=1))
        event = self.store_event(
            data={
                "event_id": "a" * 32,
                "message": "oh no",
                "timestamp": min_ago,
                "fingerprint": ["group-1"],
                "sdk": {"name": "example.sdk", "version": "1.0.0"},
            },
            project_id=self.project.id,
            assert_no_errors=False,
        )

        result = serialize(event, None, DetailedEventSerializer())
        assert result["sdkUpdates"] == []
