# `pftel`

[![Build](https://github.com/FNNDSC/pftel/actions/workflows/build.yml/badge.svg)](https://github.com/FNNDSC/pftel/actions/workflows/build.yml)

*a slightly opinionated telemetry logging service*

## Abstract

`pftel` was developed to capture logging events from any remote service in a centralized location. The initial/current version is more proof-of-concept but should be mostly production ready. The internal database reflects itself transparently onto the filesystem and on restart the filesystem reflection is considered the _ground truth_. This is used mostly as simplicity convenience at the moment. Some concurrency problems can arise if multiple `pftel` instances are deployed on the same base filesystem, and should be better addressed in future versions.

This repository also provides a shell-based client script that provides `bash`/`zsh` functions for easy CLI usage.

## Only slightly opinionated?

As its naming convention suggests, `pftel` is part of the ChRIS ecosystem of applications. ChRIS "Feeds" (or "Analyses") in ChRIS, can consist of many individual computing applications organized in trees and scheduled by the ChRIS scheduler on a variety of compute environments. While these individual applications might log information during execution, these logs can be cumbersome to access. In particular, some logging could provide useful telemetry -- such as _"How long does a Feed run?"_ or _"What is the execution time of each application in a Feed?"_

To better address this question, `pftel` was created as a simple server to which any remote client can log messages. The _opinionatedness_ of `pftel` is reflected in its core data organizational schema -- which is really a two-level directory organization where the second directory contains logging files. This organization allows for easily grouping messages from ChRIS Analyses. The first, or _top_ level directory is simply called the `logObject`. This directory contains a multitide of `logCollections` directories. Each `logCollection` contains `logEvents`.

Information POSTed by a client has the following model:

```python
class logStructured(BaseModel):
    """A simple structured log model"""
    logObject                           : str   = "default"
    logCollection                       : str   = ""
    logEvent                            : str   = ""
    appName                             : str   = ""
    execTime                            : float = 0.0
    payload                             : str   = ""
```

A client simply POSTS the above as a JSON object to the appropriate API endpoint and `pftel` organizes it appropriately. For instance, a `logObject` could be `legMeasurementPipeline`, and a  `logCollection` could be the name of a particular feed, `run1`. Each application in the Feed can specify its `logEvent` (such as the plugin name). This `logEvent` is used as the database "entry" that contains an `appName`, an `execTime` and an additional freeform `payload` message string.

It is thus easily possible to capture information organized as:

```console
/home/dicom/telemetry
└── DB
    └── service
        ├── default
        │   ├── info
        │   ├── json_created
        │   └── json_modified
        └── legMeasurementPipeline
            ├── info
            ├── json_created
            ├── json_modified
            ├── run1
            │   ├── 000-mha-to-dicom
            │   ├── 001-heatmaps
            │   ├── 002-measure
            │   └── 003-push-to-pacs
            └── run2
                ├── 000-mha-to-dicom
                ├── 001-heatmaps
                ├── 002-measure
                └── 003-push-to-pacs
```

where an individual `logEvent` (say `legMeasurementPipeline/run1/001-heatmaps`) is recorded as:

```json
{
  "_id": "001",
  "_timestamp": "2023-03-07 18:06:45.728971",
  "appName": "pl-LLD_inference",
  "execTime": 77.48,
  "requestHost": "192.168.1.200",
  "requestPort": "57296",
  "requestUserAgent": "curl/7.88.1",
  "payload": ""
}
```

## Goodies

As the database of telemetry grows, `pftel` is able to provide some useful query returns and statistics. Assumine you have `source workflow.sh`, you could do get a nice CSV on the events in `legMeasurementPipeline` `run1`:


```shell
❯ logEvent_getAllAsCSV legMeasurementPipeline run1 _timestamp,appName,execTime
┌──────────────────────────┬────────────────────┬──────────┐
│        _timestamp        │      appName       │ execTime │
├──────────────────────────┼────────────────────┼──────────┤
│2023-03-07 18:06:45.691175│    pl-mha2dicom    │    0.1550│
│2023-03-07 18:06:45.728971│  pl-LLD_inference  │   77.4800│
│2023-03-07 18:06:45.768222│     pl-legMeas     │    5.6010│
│2023-03-07 18:06:45.804124│  pl-orthanc_push   │    2.1480│
└──────────────────────────┴────────────────────┴──────────┘
```

and some statistics:

```shell
❯ logEvent_getStats legMeasurementPipeline run1
{
  "run1": {
    "sum": 85.384,
    "minmax": [
      0.155,
      77.48
    ],
    "mean": 21.346,
    "variance": 1405.5175553333331,
    "nobs": 4,
    "skewness": 1.1423208583037028,
    "kurtosis": -0.6764204859682819
  }
}
```

How about statistcs for all the events in a collection?

```shell
❯ logCollection_getStats legMeasurementPipeline
{
  "run1": {
    "sum": 85.384,
    "minmax": [
      0.155,
      77.48
    ],
    "mean": 21.346,
    "variance": 1405.5175553333331,
    "nobs": 4,
    "skewness": 1.1423208583037028,
    "kurtosis": -0.6764204859682819
  },
    ...
    ...
  "run5": {
    "sum": 95.54599999999999,
    "minmax": [
      0.082,
      90.111
    ],
    "mean": 23.886499999999998,
    "variance": 1951.3259443333336,
    "nobs": 4,
    "skewness": 1.1509204982086199,
    "kurtosis": -0.6695897536288866
  }
}
```

and how about _processing_ all the statistics for a collection?

```shell
❯ logCollection_getStatsProcess  legMeasurementPipeline
{
  "legMeasurementPipeline": {
    "sum": 318.35200000000003,
    "minmax": [
      0.082,
      90.111
    ],
    "mean": 15.917599999999998,
    "variance": 873.0404462526316,
    "nobs": 20,
    "skewness": 1.9002098035627986,
    "kurtosis": 1.77786468680873
  }
}
```

## Getting and using

### Build

Build the latest docker image

```bash
# Pull repo...
gh repo clone FNNDSC/pftel
# Enter the repo...
cd pftel

# Set some vars
set UID (id -u) # THIS IF FOR FISH SHELLs
# export UID=$(id -u)  # THIS IS FOR BASH SHELLs
export PROXY="http://10.41.13.4:3128"

# Here we build an image called local/pftel
# Using --no-cache is a good idea to force the image to build all from scratch
docker build --no-cache --build-arg http_proxy=$PROXY --build-arg UID=$UID -t local/pftel .

# If you're not behind a proxy, then
docker build --no-cache --build-arg UID=$UID -t local/pftel .
```

## Deploy as background process

```bash
docker run --name pftel  --rm -it -d                                            \
        -p 22223:22223                                                          \
        -v /home/dicom:/home/dicom                                              \
        local/pftel /start-reload.sh
```

### "Hello, `pftel`, you're looking good"

Using [httpie](https://httpie.org/), let's ask `pftel` about itself


```bash
http :22223/api/v1/about/
```

and say `hello` with some info about the system on which `pftel` is running:

```bash
http :22223/api/v1/hello/ echoBack=="Hello, World!"
```

For full exemplar documented examples, see `pftel/workflow.sh` in this repository as well as `HOWTORUN`. Also consult the `pftel/pftel.sh` script for more details.

### API swagger

Full API swagger is available. Once you have started `pftel`, and assuming that the machine hosting the container is `localhost`, navigate to [http://localhost:22223/docs](http://localhost:22223/docs) .


## Development

To debug code within `pftel` from a containerized instance, perform volume mappings in an interactive session:

```bash
# Run with support for source debugging
docker run --name pftel  --rm -it                                              	\
        -p 22223:22223 	                                                        \
        -v /home/dicom:/home/dicom                                             	\
        -v $PWD/pftel:/app:ro                                                  	\
        local/pftel /start-reload.sh
```

## Test

To check that the service is working properly, you log a test message with

```bash
# Set PFTEL appropriately for your local env:
export PTFEL=http://localhost:22223
curl -s -X 'POST'                                                             \
  "$PFTEL/api/v1/slog/?logObject=default&logCollection=slog&logEvent=log"     \
  -H 'accept: application/json'                                               \
  -H 'Content-Type: application/json'                                         \
  -d '{
  "log": "Hello, pftel service, how are things?"
  }'
```

_-30-_
