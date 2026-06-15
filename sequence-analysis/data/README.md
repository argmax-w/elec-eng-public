# Data

The analysis runs on a single file: `data/raw/BigBatt_telem.csv`, a short burst
of three-phase telemetry from a grid-connected battery. It carries client-local
timestamps (Eastern Australia Time) and six instantaneous channels, `V1`-`V3`
and `I1`-`I3`, sampled near 1.6 kHz for about a second.

That CSV is real measurement data, so it is **gitignored** rather than
redistributed (`**/data/raw/` and `*.csv` are both ignored). To reproduce the
results, drop a telemetry export with the following header in at
`data/raw/BigBatt_telem.csv`:

```
"Timestamp (Client Local) Eastern Australia Time","Timestamp (Device Local) Eastern Australia Time","V1","V2","V3","I1","I2","I3"
```

The loader (`seqanalysis.io.load_telemetry`) reads the client timestamps to
recover the sampling interval, renames the channels to `Va`-`Vc` and `Ia`-`Ic`,
and reports how many samples fall in one 50 Hz cycle. That count sets the
decomposition window, so any three-phase record in this schema will run: the
cycle length simply adapts to the sampling rate.
