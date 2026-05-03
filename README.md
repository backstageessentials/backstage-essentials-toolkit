# backstage-essentials-toolkit

A reusable, subject-neutral toolkit for building courses from plain text source files. Bundles documentation, Claude Code skills, and templates so a course author working on a Chromebook can go from blank repo to published course without reinventing the workflow each time. The toolkit works for any subject (high school science, college, adult trade training, sports coaching, etc.) and any publishing target (Thinkific, Canvas, Google Classroom, static web, PDF). Voice is per-course, not toolkit-baked: each course writes its own voice guide and the lesson-drafter skill reads it at run time. Designed around a "verify don't think" model — skills generate drafts, humans review and revise.

## Status

Skeleton, in active development.

## Related Repositories

- [backstageessentials/backstage-essentials-course](https://github.com/backstageessentials/backstage-essentials-course) — the first course built using this toolkit. Treat that repo as the reference implementation while the toolkit is still maturing.

## Architecture

The architecture (phases, skill boundaries, doc layout) is documented in the toolkit plan doc, which will be added to this repo in a future commit.

## License

Released under [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](LICENSE) (CC BY-NC-SA 4.0).
