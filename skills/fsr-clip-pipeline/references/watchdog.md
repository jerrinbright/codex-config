# Watchdogs

A long job with no watcher costs the entire gap until someone asks about it. One
extraction run died minutes after launch and sat dead for ~11 hours.

## Template

```bash
#!/bin/bash
cd /path/to/repo
log(){ echo "[$(date +%H:%M)] $*"; }

running(){ timeout 100 modal app list -e jerrin --json 2>/dev/null | python3 -c "
import sys,json
print(sum(1 for a in json.load(sys.stdin)
          if '$1' in a.get('Description','') and a.get('Stopped at') is None))"; }

for i in $(seq 1 200); do
  pending=$(measure_real_pending)          # see below
  n=$(running my-app-prefix)
  log "pending=$pending workers=$n"

  # ENOSPC is NOT transient. Restarting just spins.
  if grep -qE "No space left on device|available inodes" /tmp/run.log; then
    log "DISK/INODE EXHAUSTED - stopping, needs cleanup"; break
  fi

  [ "$pending" = "0" ] && { log "COMPLETE"; break; }

  if [ "$n" = "0" ]; then
    log "app down with work remaining -> relaunch"
    setsid bash -c "nohup modal run --detach -e jerrin <script> --launch > /tmp/relaunch_$i.log 2>&1 &" < /dev/null
    sleep 150
  fi
  sleep 300
done
```

Launch it detached so it survives the shell:

```bash
setsid bash -c 'nohup bash /tmp/watch.sh > /tmp/watch.log 2>&1 &' < /dev/null
```

## Measure the real completion metric

The single most common watcher bug is polling a proxy. Comparing output count to
input count went wrong twice in one run:

- `undistorted_dirs (80,133) > clips_left (78,845)` was read as "complete", but the
  two counts cover overlapping-but-different episode sets. 4,943 episodes still
  had clips with no rectified output.
- A volume listing lags deletes, so `clips_left` stayed flat while work proceeded.

Poll the actual thing:

```python
pending = [ep for ep in os.listdir(CLIPS)
           if os.listdir(f"{CLIPS}/{ep}") and ep not in os.listdir(OUT)]
```

## Gotchas

**Run detached.** `modal run` without `--detach` dies when the client
disconnects; a 2-minute shell timeout killed a query this way, and Modal logged
`Stopping app - local client disconnected`.

**Unique log filenames.** Reusing `/tmp/final.log` between jobs caused a `grep`
for `RESULT:` to match a previous job's output twice, reporting stale numbers as
current. Timestamp or namespace every log.

**pgrep -f matches your own command line.** Checking for a process whose name
appears in the checking command returns a false positive. Match on
`ps -eo args | grep "^bash /tmp/x.sh"` instead.

**Never poll a dead job forever.** Cap iterations, and treat repeated
"app down -> relaunch" cycles as a signal that the remaining work is impossible
(e.g. episodes with no `calibration_key` can never rectify), not that it needs
more retries.
