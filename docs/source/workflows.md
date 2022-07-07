# Workflows

The following chapter provides an overview and details about the main `foxops` workflows, like `initialization` and `update`.

## Reconciliation Workflow

```{mermaid}
graph TD
    START(reconcile)-->EXISTS{{incarnation repository exists?}}
    EXISTS-->|no|END
    EXISTS-->|yes|INITIALIZED{{incarnation repository already initialized?}}
    INITIALIZED-->|no|INITIALIZE[[fengine init]]
    INITIALIZED-->|yes|UPDATE[[fengine update]]

    INITIALIZE-->IS_EMPTY{{is incarnation location empty?}}
    IS_EMPTY-->|yes|COMMIT_DEFAULT(commit to default branch)
    COMMIT_DEFAULT-->END

    IS_EMPTY-->|no|CREATE_MR(commit to feature branch and create MR)
    CREATE_MR-->AUTOMERGE_ENABLED{{is automerge enabled?}}
    AUTOMERGE_ENABLED-->|no|END
    AUTOMERGE_ENABLED-->|yes|SET_AUTOMERGE(set MR to automerge)
    SET_AUTOMERGE-->END

    UPDATE-->CHANGES{{any changes?}}
    CHANGES-->|no|END
    CHANGES-->|yes|CREATE_MR

    END(done)
```

## Initialization Workflow (fengine init)

```{mermaid}
graph TD
    START(reconcile)-->EXISTS{{incarnation repository exists?}}
    EXISTS-->|no|LOG_NOT_EXISTS[Log Warning]
    EXISTS-->|yes|INITIALIZED{{incarnation repository already initialized?}}
    INITIALIZED-->|no|INITIALIZE[[fengine init]]
    INITIALIZED-->|yes|UPDATE[[fengine update]]

    INITIALIZE-->IS_EMPTY{{is incarnation location empty?}}


    INITIALIZE-->RENDER_INIT(render template with incarnation variables)
    UPDATE-->IS_UPDATE_REQUIRED{{is template update required?}}
    IS_UPDATE_REQUIRED-->|yes|RENDER_OLD(render old template version)
    IS_UPDATE_REQUIRED-->|no|NO_UPDATE[End]

    RENDER_OLD-->RENDER_NEW(render new template version)
    RENDER_NEW-->CALC_DIFF(calculate diff between outcome)
    CALC_DIFF-->APPLY_DIFF(apply patch to incarnation)
```
