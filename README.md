# `pfair`

[![Build](https://github.com/FNNDSC/pfair/actions/workflows/build.yml/badge.svg)](https://github.com/FNNDSC/pfair/actions/workflows/build.yml)

*a slightly opinionated telemetry logging service*

## Abstract

`pfair` is a service that _caches_ data from the [purple air network of sensors](https://www2.purpleair.com), allowing for no-cost API requests on especially historical data. The [purple air API](https://api.purpleair.com) provides access to data collected on the sensor network. Each API request, however, has a real-world cost associated with the access, meaning that repeated historical access can incur a real world cost. This service allows for no-cost historical access (since pulled data is stored in its own database independently from purple air) and also allows for some useful query API endpoints (for example, "Which sensors are dead in my pool?").

## Only slightly opinionated?


## Getting and using

### Build

Build the latest docker image

```bash
# Pull repo...
gh repo clone rudolphpienaar/pfair
# Enter the repo...
cd pfair

# Set some vars
set UID (id -u) # THIS IF FOR FISH SHELLs
# export UID=$(id -u)  # THIS IS FOR BASH/ZSH SHELLs

# If you are behind a proxy, set this accordingly
# export PROXY="http://10.41.13.4:3128"

# Here we build an image called local/pfair
# Using --no-cache is a good idea to force the image to build all from scratch

# If you're behind a proxy, uncomment this:
# docker build --no-cache --build-arg http_proxy=$PROXY --build-arg UID=$UID -t local/pfair .

# If you're not behind a proxy, then
docker build --no-cache --build-arg UID=$UID -t local/pfair .
```

## Deploy as background process

```bash
docker run --name pfair  --rm -it -d                                            \
        -p 22223:22223                                                          \
        -v /home/dicom:/home/dicom                                              \
        local/pfair /start-reload.sh
```

### "Hello, `pfair`, you're looking good"

Using [httpie](https://httpie.org/), let's ask `pfair` about itself


```bash
http :22223/api/v1/about/
```

and say `hello` with some info about the system on which `pfair` is running:

```bash
http :22223/api/v1/hello/ echoBack=="Hello, World!"
```

For full exemplar documented examples, see `pfair/workflow.sh` in this repository as well as `HOWTORUN`. Also consult the `pfair/pfair.sh` script for more details.

### API swagger

Full API swagger is available. Once you have started `pfair`, and assuming that the machine hosting the container is `localhost`, navigate to [http://localhost:22223/docs](http://localhost:22223/docs) .


## Development

To debug code within `pfair` from a containerized instance, perform volume mappings in an interactive session:

```bash
# Run with support for source debugging
docker run --name pfair  --rm -it                                              	\
        -p 22223:22223 	                                                        \
        -v /home/dicom:/home/dicom                                             	\
        -v $PWD/pfair:/app:ro                                                  	\
        local/pfair /start-reload.sh
```

## Test

To check that the service is working properly, you log a test message with

```bash
# Set pfair appropriately for your local env:
export PTFEL=http://localhost:22223
curl -s -X 'POST'                                                             \
  "$pfair/api/v1/slog/?logObject=default&logCollection=slog&logEvent=log"     \
  -H 'accept: application/json'                                               \
  -H 'Content-Type: application/json'                                         \
  -d '{
  "log": "Hello, pfair service, how are things?"
  }'
```

_-30-_
