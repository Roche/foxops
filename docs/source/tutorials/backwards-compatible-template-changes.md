# Making backwards-compatible Changes to a Template

The following list suggests how to implement certain template changes in a backwards-compatible way.

## Adding a new Variable

fengine supports `default`s, which are used when no value is specified for the template rendering.
Specifying the `default` effectively makes the variable *optional*.

```yaml
variables:
  new_var:
    type: string
    description: New variable for the template
    default: "Hello"
```

## Removing a Variable

fengine ignores, but warns about additional variables being based for the template rendering.
Therefore, removing a variable is supported out of the box and no active measure needs to be taken.

## Changing the name of a Variable

This is has to be implemented as a combination of *Removing a Variable* and *Adding a new Variable*.
fengine doesn't yet support automatic migration of renamed variable as in: fengine knows the old name
of a variable and uses its passed value for the newly named variable.

## Changing the type of a Variable

fengine doesn't yet care about the type too much. It's neither enforced nor are the passed values
casted to its respective Python type.
Changing the type of a Variable can therefore be implemented without taking active measures.
