@e2e
Feature: Foxops Reconciliation
    In order to keep GitOps repositories at scale in
    sync, we need to be able to reconcile changes
    from a template to the real GitOps repositories.

    Scenario: Update incarnation repository when new template version exists
        Given I have a template repository at "template"
        And I want an incarnation repository at "incarnation"
        And I reconcile
        When I update the template repository at "template"
        And I want the updated template for the repository at "incarnation"
        And I reconcile
        Then I should see a new Merge Request with the updates on GitLab at "incarnation"

    Scenario: Update incarnation repository when template data changed
        Given I have a template repository at "template"
        And I want an incarnation repository at "incarnation"
        And I reconcile
        When I change the template data for the "incarnation" repository
        And I reconcile
        Then I should see a new Merge Request with the changes on GitLab at "incarnation"
