# email2html

This repo contains `src/email2html.py` which converts email source to html.

## before everything

```console
[Host]$ git clone <this repo> && cd <this repo>
[Host]$ docker-compose up --build -d
[Host]$ docker exec -it <container-name> /bin/bash
[Container]# pwd #-> /var/app
```

## usage

### show help

```console
[Container]# python email2html.py --help
```

### convert one file

```console
[Container]# python email2html.py convert --file-path=./original_files/original_msg.txt
```

### convert some files

```console
[Container]# python email2html.py bulkconvert --original-dir=./original_files --output-dir=./output
```
