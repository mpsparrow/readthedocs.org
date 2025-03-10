"""Endpoint to generate footer HTML."""

import re
from functools import lru_cache

import structlog
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template import loader as template_loader
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jsonp.renderers import JSONPRenderer

from readthedocs.api.v2.mixins import CachedResponseMixin
from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.builds.constants import LATEST, TAG
from readthedocs.builds.models import Version
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.constants import MKDOCS, SPHINX_HTMLDIR
from readthedocs.projects.models import Project
from readthedocs.projects.version_handling import (
    highest_version,
    parse_version_failsafe,
)

log = structlog.get_logger(__name__)


def get_version_compare_data(project, base_version=None):
    """
    Retrieve metadata about the highest version available for this project.

    :param base_version: We assert whether or not the base_version is also the
                         highest version in the resulting "is_highest" value.
    """
    if (
        not project.show_version_warning or
        (base_version and base_version.is_external)
    ):
        return {'is_highest': False}

    versions_qs = (
        Version.internal.public(project=project)
        .filter(built=True, active=True)
    )

    # Take preferences over tags only if the project has at least one tag
    if versions_qs.filter(type=TAG).exists():
        versions_qs = versions_qs.filter(type=TAG)

    # Optimization
    versions_qs = versions_qs.select_related('project')

    highest_version_obj, highest_version_comparable = highest_version(
        versions_qs,
    )
    ret_val = {
        'project': str(highest_version_obj),
        'version': str(highest_version_comparable),
        'is_highest': True,
    }
    if highest_version_obj:
        # Never link to the dashboard,
        # users reading the docs may don't have access to the dashboard.
        ret_val['url'] = highest_version_obj.get_absolute_url()
        ret_val['slug'] = highest_version_obj.slug
    if base_version and base_version.slug != LATEST:
        try:
            base_version_comparable = parse_version_failsafe(
                base_version.verbose_name,
            )
            if base_version_comparable:
                # This is only place where is_highest can get set. All error
                # cases will be set to True, for non- standard versions.
                ret_val['is_highest'] = (
                    base_version_comparable >= highest_version_comparable
                )
            else:
                ret_val['is_highest'] = True
        except (Version.DoesNotExist, TypeError):
            ret_val['is_highest'] = True
    return ret_val


class BaseFooterHTML(CachedResponseMixin, APIView):

    """
    Render and return footer markup.

    Query parameters:

    - project
    - version
    - page: Sphinx's page name (name of the source file),
      used to build the "edit on" links.
    - theme: Used to decide how to integrate the flyout menu.
    - docroot: Path where all the source documents are.
      Used to build the ``edit_on`` URL.
    - source_suffix: Suffix from the source document.
      Used to build the ``edit_on`` URL.

    .. note::

       The methods `_get_project` and `_get_version`
       are called many times, so a basic cache is implemented.
    """

    http_method_names = ['get']
    permission_classes = [IsAuthorizedToViewVersion]
    renderer_classes = [JSONRenderer, JSONPRenderer]
    project_cache_tag = 'rtd-footer'

    @lru_cache(maxsize=1)
    def _get_project(self):
        project_slug = self.request.GET.get('project', None)
        project = get_object_or_404(Project, slug=project_slug)
        return project

    @lru_cache(maxsize=1)
    def _get_version(self):
        version_slug = self.request.GET.get('version', None)

        # Hack in a fix for missing version slug deploy
        # that went out a while back
        if version_slug == '':
            version_slug = LATEST

        project = self._get_project()
        version = get_object_or_404(
            project.versions.all(),
            slug__iexact=version_slug,
        )
        return version

    def _get_active_versions_sorted(self):
        """Get all versions that the user has access, sorted."""
        project = self._get_project()
        versions = project.ordered_active_versions(
            user=self.request.user,
            include_hidden=False,
        )
        return versions

    def _get_context(self):
        theme = self.request.GET.get('theme', False)
        docroot = self.request.GET.get('docroot', '')
        source_suffix = self.request.GET.get('source_suffix', '.rst')

        new_theme = (theme == 'sphinx_rtd_theme')

        project = self._get_project()
        main_project = project.main_language_project or project
        version = self._get_version()

        page_slug = self.request.GET.get('page', '')
        path = ''
        if page_slug and page_slug != 'index':
            if version.documentation_type in {SPHINX_HTMLDIR, MKDOCS}:
                path = re.sub('/index$', '', page_slug) + '/'
            else:
                path = page_slug + '.html'

        context = {
            "project": project,
            "version": version,
            "path": path,
            "downloads": version.get_downloads(pretty=True),
            "current_version": version,
            "versions": self._get_active_versions_sorted(),
            "main_project": main_project,
            "translations": main_project.translations.all(),
            "current_language": project.language,
            "new_theme": new_theme,
            "settings": settings,
            "github_edit_url": version.get_github_url(
                docroot,
                page_slug,
                source_suffix,
                'edit',
            ),
            'github_view_url': version.get_github_url(
                docroot,
                page_slug,
                source_suffix,
                'view',
            ),
            'gitlab_edit_url': version.get_gitlab_url(
                docroot,
                page_slug,
                source_suffix,
                'edit',
            ),
            'gitlab_view_url': version.get_gitlab_url(
                docroot,
                page_slug,
                source_suffix,
                'view',
            ),
            'bitbucket_url': version.get_bitbucket_url(
                docroot,
                page_slug,
                source_suffix,
            ),
        }
        return context

    def get(self, request, format=None):
        project = self._get_project()
        version = self._get_version()
        version_compare_data = get_version_compare_data(
            project,
            version,
        )

        context = self._get_context()
        html = template_loader.get_template('restapi/footer.html').render(
            context,
            request,
        )

        show_version_warning = (
            project.show_version_warning and
            not version.is_external
        )

        resp_data = {
            'html': html,
            'show_version_warning': show_version_warning,
            'version_active': version.active,
            'version_compare': version_compare_data,
            'version_supported': version.supported,
        }

        return Response(resp_data)


class FooterHTML(SettingsOverrideObject):
    _default_class = BaseFooterHTML
