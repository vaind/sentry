from sentry import features
from sentry.services.hybrid_cloud.organization import ApiOrganization, organization_service
from sentry.testutils import TestCase
from sentry.testutils.helpers import with_feature


class TestTestUtilsFeatureHelper(TestCase):
    def setUp(self):
        self.org = self.create_organization()

    def test_without_feature(self):
        assert not features.has("organizations:global-views", self.org)

    @with_feature("organizations:global-views")
    def test_with_feature(self):
        assert features.has("organizations:global-views", self.org)

    def test_feature_with_api_organization(self):

        with self.feature({"organizations:customer-domains": False}):
            org_context = organization_service.get_organization_by_slug(
                slug=self.org.slug, only_visible=False, user_id=None
            )
            assert org_context
            assert org_context.organization
            assert isinstance(org_context.organization, ApiOrganization)

            assert features.has("organizations:customer-domains", org_context.organization) is False

        with self.feature({"organizations:customer-domains": True}):
            org_context = organization_service.get_organization_by_slug(
                slug=self.org.slug, only_visible=False, user_id=None
            )
            assert org_context
            assert org_context.organization
            assert isinstance(org_context.organization, ApiOrganization)

            assert features.has("organizations:customer-domains", org_context.organization)
