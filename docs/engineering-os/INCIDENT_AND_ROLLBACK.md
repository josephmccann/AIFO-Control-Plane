# Incident and rollback

Incidents preserve the originating mission and pull request, severity, kill
switch, recovery actions, and verification. Supported recovery classes are
clean revert, forward fix, point-in-time restore, data-migration recovery, and
irreversible recovery with explicit authority.

Merge approval never authorizes rollback execution. Recovery actions that
mutate deployment, cloud, data, or other external state require their own
current authority. The incident validator accepts authenticated authority
records, not a caller-supplied authorization flag, and consumes one exact
single-use record bound to the originating mission, repository, pull request,
reviewed head, responder, changed paths, and recovery action.
