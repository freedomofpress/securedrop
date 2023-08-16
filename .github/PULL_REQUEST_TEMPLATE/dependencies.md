---
name: Dependency change
about: Update a production dependency or silence an alert
---

## Status

Ready for review / Work in progress

## Description of Changes

<!-- Fill out the appropriate "###" section below and delete the others. -->

### If you've added or updated a production code dependency:

Production code dependencies are defined in:

- `admin/requirements.in`
- `admin/requirements-ansible.in`
- `securedrop/requirements/python3/requirements.in`

If you changed another `requirements.in` file that applies only to development
or testing environments, then no diff review is required, and you can open
a regular pull request.

Choose one of the following:

- [ ] I have performed a diff review and pasted the contents to [the packaging wiki](https://github.com/freedomofpress/securedrop-debian-packaging/wiki)
- [ ] I would like someone else to do the diff review

### If you've silenced an alert about a production code dependency, explain why:

## Testing

How should the reviewer test this PR?
Write out any special testing steps here.

## Deployment

Any special considerations for deployment? Consider both:

1. Upgrading existing production instances.
2. New installs.
