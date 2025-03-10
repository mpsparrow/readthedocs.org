VCS Integrations
================

Read the Docs provides integrations with several VCS providers to detect changes to your
documentation and versions, mainly using *webhooks*.
Integrations are configured with your repository provider,
such as GitHub, Bitbucket or GitLab,
and with each change to your repository, Read the Docs is notified. When we
receive an integration notification, we determine if the change is related to an
active version for your project, and if it is, a build is triggered for that
version.

You'll find a list of configured integrations on your project's :guilabel:`Admin`
dashboard, under :guilabel:`Integrations`. You can select any of these integrations to
see the *integration detail page*. This page has additional configuration
details and a list of HTTP exchanges that have taken place for the integration,
including the Payload URL needed by the repository provider
such as GitHub, GitLab, or Bitbucket.

Integration Creation
--------------------

If you have :doc:`connected your Read the Docs account </connected-accounts>` to GitHub, Bitbucket, or GitLab,
**an integration will be set up automatically for your repository**. However, if your
project was not imported through a connected account, you may need to
manually configure an integration for your project.

To manually set up an integration, go to :guilabel:`Admin` > :guilabel:`Integrations` >  :guilabel:`Add integration`
dashboard page and select the integration type you'd like to add.
After you have added the integration, you'll see a link to information about the integration.

As an example, the URL pattern looks like this: *https://readthedocs.org/api/v2/webhook/<project-name>/<id>/*.

Use this URL when setting up a new integration with your provider -- these steps vary depending on the provider.

.. note::

   If your account is connected to the provider,
   we'll try to setup the integration automatically.
   If something fails, you can still setup the integration manually.

.. _webhook-integration-github:

GitHub
~~~~~~

* Go to the :guilabel:`Settings` page for your project
* Click :guilabel:`Webhooks` > :guilabel:`Add webhook`
* For **Payload URL**, use the URL of the integration on Read the Docs,
  found on the project's :guilabel:`Admin` > :guilabel:`Integrations` page.
  You may need to prepend *https://* to the URL.
* For **Content type**, both *application/json* and
  *application/x-www-form-urlencoded* work
* Leave the **Secrets** field blank
* Select **Let me select individual events**,
  and mark **Branch or tag creation**, **Branch or tag deletion**, **Pull requests** and **Pushes** events
* Ensure **Active** is enabled; it is by default
* Finish by clicking **Add webhook**.  You may be prompted to enter your GitHub password to confirm your action.

You can verify if the webhook is working at the bottom of the GitHub page under **Recent Deliveries**.
If you see a Response 200, then the webhook is correctly configured.
For a 403 error, it's likely that the Payload URL is incorrect.

GitHub will emit an initial HTTP request (`X-GitHub-Event: ping`) upon creating the webhook and you may notice that the Read the Docs responds with `{"detail":"Unhandled webhook event"}` – this is normal and expected.
Push changes to your repository and webhooks will work from this point.

.. note:: The webhook token, intended for the GitHub **Secret** field, is not yet implemented.

.. _webhook-integration-bitbucket:

Bitbucket
~~~~~~~~~

* Go to the :guilabel:`Settings` > :guilabel:`Webhooks` > :guilabel:`Add webhook` page for your project
* For **URL**, use the URL of the integration on Read the Docs,
  found on the :guilabel:`Admin` > :guilabel:`Integrations`  page
* Under **Triggers**, **Repository push** should be selected
* Finish by clicking **Save**

.. _webhook-integration-gitlab:

GitLab
~~~~~~

* Go to the :guilabel:`Settings` > :guilabel:`Integrations` page for your project
* For **URL**, use the URL of the integration on Read the Docs,
  found on the :guilabel:`Admin` > :guilabel:`Integrations`  page
* Leave the default **Push events** selected and mark **Tag push events** also
* Finish by clicking **Add Webhook**

Gitea
~~~~~

These instructions apply to any Gitea instance.

.. warning::

   This isn't officially supported, but using the "GitHub webhook" is an effective workaround,
   because Gitea uses the same payload as GitHub. The generic webhook is not compatible with Gitea.
   See `issue #8364`_ for more details. Official support may be implemented in the future.

On Read the Docs:

* Manually create a "GitHub webhook" integration
  (this will show a warning about the webhook not being correctly set up,
  that will go away when the webhook is configured in Gitea)

On your Gitea instance:

* Go to the :guilabel:`Settings` > :guilabel:`Webhooks` page for your project on your Gitea instance
* Create a new webhook of type "Gitea" 
* For **URL**, use the URL of the integration on Read the Docs,
  found on the :guilabel:`Admin` > :guilabel:`Integrations` page
* Leave the default **HTTP Method** as POST
* For **Content type**, both *application/json* and
  *application/x-www-form-urlencoded* work
* Leave the **Secret** field blank
* Select **Choose events**,
  and mark **Branch or tag creation**, **Branch or tag deletion** and **Push** events
* Ensure **Active** is enabled; it is by default
* Finish by clicking **Add Webhook**
* Test the webhook with :guilabel:`Delivery test`

Finally, on Read the Docs, check that the warnings have disappeared
and the delivery test triggered a build.

.. _issue #8364: https://github.com/readthedocs/readthedocs.org/issues/8364

.. _webhook-integration-generic:

Using the generic API integration
---------------------------------

For repositories that are not hosted with a supported provider, we also offer a
generic API endpoint for triggering project builds. Similar to webhook integrations,
this integration has a specific URL, which can be found on the project's **Integrations** dashboard page
(:guilabel:`Admin` > :guilabel:`Integrations`).

Token authentication is required to use the generic endpoint, you will find this
token on the integration details page. The token should be passed in as a
request parameter, either as form data or as part of JSON data input.

Parameters
~~~~~~~~~~

This endpoint accepts the following arguments during an HTTP POST:

branches
    The names of the branches to trigger builds for. This can either be an array
    of branch name strings, or just a single branch name string.

    Default: **latest**

token
    The integration token found on the project's **Integrations** dashboard page
    (:guilabel:`Admin` > :guilabel:`Integrations`).

For example, the cURL command to build the ``dev`` branch, using the token
``1234``, would be::

    curl -X POST -d "branches=dev" -d "token=1234" https://readthedocs.org/api/v2/webhook/example-project/1/

A command like the one above could be called from a cron job or from a hook
inside Git_, Subversion_, Mercurial_, or Bazaar_.

.. _Git: http://www.kernel.org/pub/software/scm/git/docs/githooks.html
.. _Subversion: https://www.mikewest.org/2006/06/subversion-post-commit-hooks-101
.. _Mercurial: http://hgbook.red-bean.com/read/handling-repository-events-with-hooks.html
.. _Bazaar: http://wiki.bazaar.canonical.com/BzrHooks

Authentication
~~~~~~~~~~~~~~

This endpoint requires authentication. If authenticating with an integration
token, a check will determine if the token is valid and matches the given
project. If instead an authenticated user is used to make this request, a check
will be performed to ensure the authenticated user is an owner of the project.

Debugging webhooks
------------------

If you are experiencing problems with an existing webhook, you may be able to
use the integration detail page to help debug the issue. Each project
integration, such as a webhook or the generic API endpoint, stores the HTTP
exchange that takes place between Read the Docs and the external source. You'll
find a list of these exchanges in any of the integration detail pages.

Resyncing webhooks
------------------

It might be necessary to re-establish a webhook if you are noticing problems.
To resync a webhook from Read the Docs, visit the integration detail page and
follow the directions for re-syncing your repository webhook.

Payload validation
------------------

If your project was imported through a connected account,
we create a secret for every integration that offers a way to verify that a webhook request is legitimate.
Currently, `GitHub <https://developer.github.com/webhooks/securing/>`__ and `GitLab <https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#secret-token>`__
offer a way to check this.

Troubleshooting
---------------

Webhook activation failed. Make sure you have the necessary permissions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you find this error,
make sure your user has permissions over the repository.
In case of GitHub,
check that you have granted access to the Read the Docs `OAuth App`_ to your organization.

.. _OAuth App: https://github.com/settings/applications

My project isn't automatically building
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your project isn't automatically building, you can check your integration on
Read the Docs to see the payload sent to our servers. If there is no recent
activity on your Read the Docs project webhook integration, then it's likely
that your VCS provider is not configured correctly. If there is payload
information on your Read the Docs project, you might need to verify that your
versions are configured to build correctly.

Either way, it may help to either resync your webhook integration (see
`Resyncing webhooks`_ for information on this process), or set up an entirely
new webhook integration.
