## Status

Ready for review / Work in progress

## Description of Changes

Fixes #.

Changes proposed in this pull request:

## Testing

How should the reviewer test this PR?
Write out any special testing steps here.

## Deployment

Any special considerations for deployment? Consider both:

1. Upgrading existing production instances.
2. New installs.

## Checklist

### If you made changes to the server application code:

- [ ] Linting (`make lint`) and tests (`make test`) pass in the development container

### If you made changes to `securedrop-admin`:

- [ ] Linting and tests (`make -C admin test`) pass in the admin development container

### If you made changes to the system configuration:

- [ ] [Configuration tests](https://docs.securedrop.org/en/latest/development/testing_configuration_tests.html) pass

### If you made non-trivial code changes:

- [ ] I have written a test plan and validated it for this PR

### If you made changes to documentation:

- [ ] Doc linting (`make docs-lint`) passed locally

### If you added or updated a code dependency:

Choose one of the following:

- [ ] I have performed a diff review and pasted the contents to [the packaging wiki](https://github.com/freedomofpress/securedrop-debian-packaging/wiki)
- [ ] I would like someone else to do the diff review
