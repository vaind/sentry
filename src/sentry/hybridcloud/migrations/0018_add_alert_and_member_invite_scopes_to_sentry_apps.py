# Generated by Django 5.1.4 on 2025-01-06 19:59

from django.db import migrations

import bitfield.models
from sentry.new_migrations.migrations import CheckedMigration


class Migration(CheckedMigration):
    # This flag is used to mark that a migration shouldn't be automatically run in production.
    # This should only be used for operations where it's safe to run the migration after your
    # code has deployed. So this should not be used for most operations that alter the schema
    # of a table.
    # Here are some things that make sense to mark as post deployment:
    # - Large data migrations. Typically we want these to be run manually so that they can be
    #   monitored and not block the deploy for a long period of time while they run.
    # - Adding indexes to large tables. Since this can take a long time, we'd generally prefer to
    #   run this outside deployments so that we don't block them. Note that while adding an index
    #   is a schema change, it's completely safe to run the operation after the code has deployed.
    # Once deployed, run these manually via: https://develop.sentry.dev/database-migrations/#migration-deployment

    is_post_deployment = False

    dependencies = [
        ("hybridcloud", "0017_add_scoping_organization_apitokenreplica"),
    ]

    operations = [
        migrations.AlterField(
            model_name="apikeyreplica",
            name="scopes",
            field=bitfield.models.BitField(
                [
                    "project:read",
                    "project:write",
                    "project:admin",
                    "project:releases",
                    "team:read",
                    "team:write",
                    "team:admin",
                    "event:read",
                    "event:write",
                    "event:admin",
                    "org:read",
                    "org:write",
                    "org:admin",
                    "member:read",
                    "member:write",
                    "member:admin",
                    "org:integrations",
                    "alerts:read",
                    "alerts:write",
                    "member:invite",
                ],
                default=None,
            ),
        ),
        migrations.AlterField(
            model_name="apitokenreplica",
            name="scopes",
            field=bitfield.models.BitField(
                [
                    "project:read",
                    "project:write",
                    "project:admin",
                    "project:releases",
                    "team:read",
                    "team:write",
                    "team:admin",
                    "event:read",
                    "event:write",
                    "event:admin",
                    "org:read",
                    "org:write",
                    "org:admin",
                    "member:read",
                    "member:write",
                    "member:admin",
                    "org:integrations",
                    "alerts:read",
                    "alerts:write",
                    "member:invite",
                ],
                default=None,
            ),
        ),
    ]