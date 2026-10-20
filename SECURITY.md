# Security policy

## Reporting a vulnerability

Please report security problems **privately**, through GitHub's private
vulnerability reporting:

**[Report a vulnerability](https://github.com/upskilltoai/upskill-to-ai/security/advisories/new)**

Please don't open a public issue for a security problem. A private report
gives time to fix it before it's widely known.

Useful things to include:
- what the problem is, and what someone could do with it;
- steps to reproduce it;
- the version or commit you tested against.

## What's in scope

- The portal: sign-in, sessions, progress tracking, and anything that touches
  learner data.
- Verification of submitted work, and anything that could let someone mark
  work as verified, or obtain a certificate, without actually doing the work.
- The content pipeline and the container image built from this repository.

A curriculum link that points somewhere harmful is better reported as an
ordinary issue, so it can be removed quickly.

## Please don't

- access, change or delete data that isn't yours;
- run tests that degrade the service for others (load or denial-of-service
  testing);
- use social engineering against contributors or learners.

## What to expect

This project is maintained by one person, so responses are best effort and
there's no fixed response time. There is no bug bounty. Reports are read,
taken seriously, and credited in the fix if you'd like.

Only the latest version on the `main` branch is supported.
