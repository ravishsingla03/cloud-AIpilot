# Kubernetes: Pod stuck in CrashLoopBackOff

## Symptom

The pod's status column shows CrashLoopBackOff and the restart counter
climbs every few minutes. The container starts, exits, and the kubelet
backs off before restarting it again, doubling the wait each time up to
five minutes. The pod is not broken by Kubernetes; the container itself
is exiting and Kubernetes is doing exactly what it was told to do.

## First command to run

Always read the logs of the run that already died, not the run that is
currently starting: `kubectl logs <pod> --previous`. Without `--previous`
you get the logs of the new container, which is usually still empty. If
the container never produced output, describe the pod and read the Last
State block, which carries the exit code and reason.

## Cause: application exits immediately

Exit code 0 with a fast restart means the process finished its work and
returned. A Deployment expects a long-running process, so a batch script
deployed as a Deployment will loop forever. The fix is either a Job or a
container command that stays in the foreground. Web servers started in
daemon mode cause the same failure.

## Cause: OOMKilled

Exit code 137 and reason OOMKilled mean the kernel killed the process
because the container exceeded its memory limit. Raise the limit only
after checking whether the workload actually needs it; a memory leak
will simply take longer to hit the new ceiling. JVM and Go services with
no awareness of cgroup limits are the usual offenders.

## Cause: failing liveness probe

If the liveness probe fails before the application finishes starting,
the kubelet kills a healthy container repeatedly. The symptom looks
identical to a crash. Check the Events section for Liveness probe failed
and compare initialDelaySeconds against real startup time. A startup
probe is the correct fix for slow-booting services.

## Cause: missing config or secret

A container that cannot find a mounted secret or a required environment
variable usually exits with a non-zero code within a second. Events will
show the mount failure if the secret does not exist at all, but an
existing secret with a missing key fails silently inside the app.
