# {COURSE_NAME}

{ONE_SENTENCE_SUMMARY_FROM_DESCRIPTION}

## Status

Active development. Built using the [Backstage Essentials Course Builder Toolkit](https://github.com/backstageessentials/backstage-essentials-toolkit).

## Structure

- `course-description.md`: audience, outcomes, scope.
- `voice-guide.md`: how the writing should sound.
- `docs/build-spec.md`: the technical spec for this course.
- `content/`: lessons and knowledge checks per unit.
- `exam/course-final.yaml`: comprehensive final assessment.
- `scripts/`: sync and validation scripts.

## Daily Workflow

```
cd {COURSE_SLUG}
git pull
claude
```

Then use Claude Code or the bes command to draft lessons, write quiz questions, or sync to {TARGET_PLATFORM}.

## Platform

This course deploys to {TARGET_PLATFORM}.

## License

[Specify your course content license here. Common options: All rights reserved (default), Creative Commons, etc.]
