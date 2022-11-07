# Generated by Django 2.2.28 on 2022-11-07 19:24

from django.db import migrations

from sentry.db.models import GzippedDictField
from sentry.new_migrations.migrations import CheckedMigration
from sentry.types.issues import GroupType
from sentry.utils.query import RangeQuerySetWrapperWithProgressBar


def update_message_field(apps, schema_editor):
    """
    for performance issues, updates Group.message field value with the value in Group.data.metadata.title
    """
    Group = apps.get_model("sentry", "Group")
    unzipper = GzippedDictField()

    for group in RangeQuerySetWrapperWithProgressBar(Group.objects.all()):
        if group.type in (
            GroupType.PERFORMANCE_N_PLUS_ONE.value,
            GroupType.PERFORMANCE_SLOW_SPAN.value,
            GroupType.PERFORMANCE_SEQUENTIAL_SLOW_SPANS.value,
            GroupType.PERFORMANCE_LONG_TASK_SPANS.value,
            GroupType.PERFORMANCE_RENDER_BLOCKING_ASSET_SPAN.value,
            GroupType.PERFORMANCE_DUPLICATE_SPANS.value,
            GroupType.PERFORMANCE_N_PLUS_ONE_DB_QUERIES.value,
        ):
            try:
                # for perf-issue Groups, data should contain:
                # {
                #   'type': 'transaction'
                #   'culprit': '<location-of-transaction>',
                #   'metadata': {
                #     'title': 'N+1 Query',  # this is the title, after issue detection (the field we care about)
                #     'location': '<location-of-transaction>',
                #     'value': '<root cause of the detected issue>'
                #   },
                #   'title': '<location-of-transaction>',
                #   'location': '<location-of-transaction>',
                #   'last_received': 12345567
                # }
                data_map = unzipper.to_python(group.data)
                metadata = data_map.get("metadata")
                if metadata and metadata.get("title"):
                    group.message = metadata.get("title")
                    group.save(update_fields=["message"])
            except Exception:
                continue


class Migration(CheckedMigration):
    # This flag is used to mark that a migration shouldn't be automatically run in production. For
    # the most part, this should only be used for operations where it's safe to run the migration
    # after your code has deployed. So this should not be used for most operations that alter the
    # schema of a table.
    # Here are some things that make sense to mark as dangerous:
    # - Large data migrations. Typically we want these to be run manually by ops so that they can
    #   be monitored and not block the deploy for a long period of time while they run.
    # - Adding indexes to large tables. Since this can take a long time, we'd generally prefer to
    #   have ops run this and not block the deploy. Note that while adding an index is a schema
    #   change, it's completely safe to run the operation after the code has deployed.
    is_dangerous = True

    # This flag is used to decide whether to run this migration in a transaction or not. Generally
    # we don't want to run in a transaction here, since for long running operations like data
    # back-fills this results in us locking an increasing number of rows until we finally commit.
    atomic = False

    dependencies = [
        ("sentry", "0341_reconstrain_savedsearch_pinning_fields"),
    ]

    operations = [
        migrations.RunPython(
            update_message_field,
            migrations.RunPython.noop,
            hints={"tables": ["sentry_groupedmessage"]},
        ),
    ]
